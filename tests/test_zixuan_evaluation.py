"""Offline contract for Eastmoney's rate-limited watchlist evaluation report."""

import ast
import re
import json
import unittest
from pathlib import Path
from unittest.mock import Mock
from types import SimpleNamespace


SKILL = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")


def load_function():
    section = SKILL.split("### 6.9 东财自选股综合评价", 1)[1].split("## Layer 7:", 1)[0]
    source = re.search(r"```python\n(.*?)\n```", section, re.S).group(1)
    tree = ast.parse(source)
    tree.body = [node for node in tree.body if
                 (isinstance(node, ast.Import) and not any(alias.name == "requests" for alias in node.names))
                 or isinstance(node, ast.FunctionDef)
                 or (isinstance(node, ast.Assign) and all(
                     isinstance(target, ast.Name) and target.id.startswith("_") for target in node.targets))]
    namespace = {"requests": SimpleNamespace(RequestException=Exception)}
    exec(compile(tree, "SKILL.md:zixuan", "exec"), namespace)
    return namespace


class ZixuanEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.ns = load_function()
        self.ns["norm_ticker"] = lambda code, stock_only=False: "600657"
        self.ns["get_prefix"] = lambda code: "sh"
        self.clock = [100.0]
        self.sleeps = []
        self.ns["time"].monotonic = lambda: self.clock[0]
        self.ns["time"].sleep = lambda seconds: self.sleeps.append(seconds) or self.clock.__setitem__(0, self.clock[0] + seconds)
        self.calls = []
        def request(url, **kwargs):
            self.calls.append((url, kwargs))
            response = Mock()
            response.text = ('astock_zixuan_eval(' + json.dumps({"code": 0, "result": {
                "pages": None, "count": 1, "data": [{"SECUCODE": "600657.SH", "RAW": 1,
                                                   "TOTAL_SCORE": 76.45,
                                                   "LIST": [{"WEIGHT_ROE": 4.21}]}]
            }}) + ');')
            return response
        self.ns["em_get"] = request

    def test_request_parameters_and_cache(self):
        first = self.ns["eastmoney_zixuan_evaluation"]("600657.SH")
        self.assertEqual(first, {"SECUCODE": "600657.SH", "RAW": 1,
                                 "TOTAL_SCORE": 76.45, "LIST": [{"WEIGHT_ROE": 4.21}]})
        url, kwargs = self.calls[0]
        self.assertEqual(url, "https://datacenter-web.eastmoney.com/web/api/data/v1/get")
        self.assertEqual(kwargs["params"], {
            "reportName": "RPT_CUSTOM_SEVEN_JOINED_ZIXUAN_ZHENGU",
            "filter": '(SECUCODE="600657.SH")',
            "source": "QuoteWeb", "client": "ZixuanWEB",
            "callback": "astock_zixuan_eval"})
        self.assertNotIn("Cookie", kwargs["headers"])
        first["RAW"] = 9
        self.assertEqual(self.ns["eastmoney_zixuan_evaluation"]("sh600657"),
                         {"SECUCODE": "600657.SH", "RAW": 1,
                          "TOTAL_SCORE": 76.45, "LIST": [{"WEIGHT_ROE": 4.21}]})
        self.assertEqual(len(self.calls), 1)

    def test_expired_cache_respects_five_second_interval(self):
        self.ns["eastmoney_zixuan_evaluation"]("600657.SH")
        self.clock[0] += 601
        self.ns["eastmoney_zixuan_evaluation"]("600657.SH")
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.sleeps, [])
        self.ns["_zixuan_eval_cache"].clear()
        self.ns["eastmoney_zixuan_evaluation"]("600657.SH")
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.sleeps, [5.0])

    def test_server_error_is_not_cached(self):
        def fail(url, **kwargs):
            response = Mock()
            response.text = '{"code": 429, "message": "rate limited"}'
            return response
        self.ns["em_get"] = fail
        with self.assertRaisesRegex(RuntimeError, "429"):
            self.ns["eastmoney_zixuan_evaluation"]("600657.SH")
        self.assertFalse(self.ns["_zixuan_eval_cache"])


if __name__ == "__main__":
    unittest.main()
