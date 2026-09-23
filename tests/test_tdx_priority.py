"""Regression tests for the TDX-first client code shipped in SKILL.md."""

import re
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd


def load_tdx_client_code():
    skill = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    section = skill.split("### TDX 首选客户端 + mootdx 自动降级", 1)[1]
    block = re.search(r"```python\n(.*?)\n```", section, re.S).group(1)
    namespace = {}
    exec(compile(block, "SKILL.md:tdx-client", "exec"), namespace)
    return namespace


class Response:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(str(self.status_code))

    def json(self):
        return self.payload


class TDXPriorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = load_tdx_client_code()

    def test_primary_tdx_is_selected_before_mootdx(self):
        primary = MagicMock()
        primary.health.return_value = True
        primary.bars.return_value = pd.DataFrame([{"close": 1}])
        with patch.dict(self.ns, {
                "TDXHTTPClient": MagicMock(return_value=primary),
                "_mootdx_client": MagicMock(side_effect=AssertionError("fallback must not run"))}):
            self.assertIs(self.ns["tdx_client"](), primary)

    def test_lan_service_is_the_default_and_token_is_supported(self):
        self.assertEqual(self.ns["TDX_HTTP_URL"], "http://192.168.1.74:8080/")
        client = self.ns["TDXHTTPClient"](token="secret")
        self.assertEqual(client.session.headers["Authorization"], "Bearer secret")

    def test_mootdx_is_used_when_tdx_health_check_fails(self):
        primary = MagicMock()
        primary.health.return_value = False
        fallback = object()
        with patch.dict(self.ns, {
                "TDXHTTPClient": MagicMock(return_value=primary),
                "_mootdx_client": MagicMock(return_value=fallback)}):
            self.assertIs(self.ns["tdx_client"](), fallback)

    def test_kline_schema_and_price_units(self):
        session = MagicMock()
        session.get.return_value = Response({"code": 0, "msg": "ok", "data": {
            "Count": 1,
            "List": [{"Open": 12340, "Close": 12560, "High": 12600, "Low": 12200,
                      "Volume": 99, "Amount": 4567000, "Time": "2026-09-11T15:00:00+08:00"}],
        }})
        client = self.ns["TDXHTTPClient"]()
        client.session = session
        out = client.bars("600519.SH", frequency=9, offset=1)
        self.assertEqual(out.iloc[0].open, 12.34)
        self.assertEqual(out.iloc[0].amount, 4567)
        self.assertEqual(out.iloc[0].vol, 99)
        self.assertEqual(session.get.call_args.kwargs["params"]["code"], "sh600519")

    def test_adjusted_all_and_index_routes(self):
        session = MagicMock()
        session.get.return_value = Response({"code": 0, "msg": "ok", "data": {"Count": 0, "List": []}})
        client = self.ns["TDXHTTPClient"]()
        client.session = session
        out = client.bars_all("600519", adjust="qfq")
        self.assertEqual(out.attrs["adjust"], "qfq")
        self.assertTrue(session.get.call_args.args[0].endswith("/kline/day/qfq/all"))
        client.bars("000300.SH", frequency=0, start=2, offset=5, index=True)
        self.assertTrue(session.get.call_args.args[0].endswith("/index/5minute"))
        self.assertEqual(session.get.call_args.kwargs["params"]["start"], 2)

    def test_symbols_auction_dataset_and_generic_api(self):
        session = MagicMock()
        session.get.side_effect = [
            Response({"code": 0, "msg": "ok", "data": ["sh600519"]}),
            Response({"code": 0, "msg": "ok", "data": {"Count": 1, "List": [
                {"Time": "2026-09-18T09:25:00+08:00", "Price": 1260000,
                 "Match": 10, "Unmatched": 2, "Flag": -1}]}}),
            Response({"code": 0, "msg": "ok", "data": [{"Code": "600519"}]}),
        ]
        client = self.ns["TDXHTTPClient"]()
        client.session = session
        self.assertEqual(client.symbols("stocks"), ["sh600519"])
        auction = client.call_auction("600519")
        self.assertEqual(auction.iloc[0].price, 1260)
        self.assertEqual(client.dataset("hy")[0]["Code"], "600519")
        with self.assertRaises(ValueError):
            client.api("https://evil.example/")
        with self.assertRaises(ValueError):
            client.api("//evil.example/quote")

    def test_finance_normalizes_names_and_derives_per_share_fields(self):
        session = MagicMock()
        session.get.return_value = Response({"code": 0, "msg": "ok", "data": {
            "Code": "600519", "ZongGuBen": 1000, "LiuTongGuBen": 800,
            "JingZiChan": 5000, "JingLiRun": 500, "ZhuYingShouRu": 2000,
            "ZiBenGongJiJin": 1000, "WeiFenLiRun": 1500,
        }})
        client = self.ns["TDXHTTPClient"]()
        client.session = session
        row = client.finance("600519").iloc[0]
        self.assertEqual(row.liutongguben, 800)
        self.assertEqual(row.eps, 0.5)
        self.assertEqual(row.bvps, 5)
        self.assertEqual(row.roe, 10)
        self.assertEqual(row.meigugongjijin, 1)

    def test_bad_symbol_and_offset_fail_before_network(self):
        client = self.ns["TDXHTTPClient"]()
        client.session = MagicMock(side_effect=AssertionError("network must not run"))
        for code, offset in [("../600519", 1), ("SZ600519", 1), ("BJ000001", 1),
                             ("600519", 0), ("600519", 801), ("600519", True)]:
            with self.subTest(code=code, offset=offset), self.assertRaises(ValueError):
                client.bars(code, offset=offset)

    def test_api_error_is_not_treated_as_empty_data(self):
        session = MagicMock()
        session.get.return_value = Response({"code": 1, "msg": "upstream failed", "data": None})
        client = self.ns["TDXHTTPClient"]()
        client.session = session
        with self.assertRaisesRegex(RuntimeError, "upstream failed"):
            client.bars("600519", offset=1)


if __name__ == "__main__":
    unittest.main()
