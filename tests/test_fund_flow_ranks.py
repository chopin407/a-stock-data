"""Offline contract checks for the Eastmoney fund-flow ranking snippets."""

import ast
import re
import unittest
from pathlib import Path


SKILL = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")


def code(section, following):
    block = SKILL.split(section, 1)[1].split(following, 1)[0]
    return re.search(r"```python\n(.*?)\n```", block, re.S).group(1)


def load_code():
    source = code("### 3.4a", "### 3.5") + "\n" + code("### 3.8a", "### 3.9")
    tree = ast.parse(source)
    tree.body = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.Assign))
                 and not (isinstance(node, ast.Assign) and any(
                     isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                     and call.func.id in {"stock_fund_flow_rank", "industry_fund_flow_rank"}
                     for call in ast.walk(node)))]
    ns = {"UA": "test-agent"}
    exec(compile(tree, "SKILL.md:fund-flow-ranks", "exec"), ns)
    return ns


class FundFlowRankTests(unittest.TestCase):
    def setUp(self):
        self.ns = load_code()
        self.calls = []
        self.pages = {}

        def fake_em_get(url, **kwargs):
            self.calls.append((url, kwargs))
            page = int(kwargs["params"]["pn"])
            payload = self.pages.get(page, {"diff": [], "total": 0})

            class Response:
                def json(self):
                    return {"data": payload}

            return Response()

        self.ns["em_get"] = fake_em_get

    def test_stock_today_inflow(self):
        self.pages[1] = {"total": 1, "diff": [{
            "f12": "600001", "f14": "样本", "f2": 12.3, "f3": 2.1,
            "f62": 100, "f184": 4.5, "f66": 60, "f69": 2.7,
            "f72": 40, "f75": 1.8, "f78": -20, "f81": -0.9,
            "f84": -80, "f87": -3.6, "f127": "机械"}]}
        result = self.ns["stock_fund_flow_rank"]("today", "in", 10)
        params = self.calls[0][1]["params"]
        self.assertEqual((params["fid"], params["po"]), ("f62", "1"))
        self.assertIn("m:0+t:6+f:!2", params["fs"])
        self.assertEqual(result["rows"][0]["main_net"], 100)
        self.assertEqual(result["rows"][0]["industry"], "机械")
        self.assertEqual(result["rows"][0]["small_pct"], -3.6)

    def test_stock_three_day_outflow(self):
        self.pages[1] = {"total": 1, "diff": [{"f12": "000001", "f267": -500,
                                                "f268": -8.2, "f269": -300,
                                                "f270": -4.9, "f257": -1.1}]}
        result = self.ns["stock_fund_flow_rank"]("3d", "out", 1)
        params = self.calls[0][1]["params"]
        self.assertEqual((params["fid"], params["po"]), ("f267", "0"))
        self.assertEqual(result["rows"][0]["main_pct"], -8.2)
        self.assertEqual(result["rows"][0]["super_large_net"], -300)

    def test_industry_five_day(self):
        self.pages[1] = {"total": 1, "diff": [{"f12": "BK0001", "f14": "行业",
                                                "f164": 250, "f165": 3.3,
                                                "f166": 100, "f167": 1.3}]}
        result = self.ns["industry_fund_flow_rank"]("5d", "in", 2)
        params = self.calls[0][1]["params"]
        self.assertEqual(params["fs"], "m:90+s:4")
        self.assertEqual(params["fid"], "f164")
        self.assertEqual(result["rows"][0]["super_large_net"], 100)
        self.assertNotIn("industry", result["rows"][0])

    def test_empty_and_invalid(self):
        self.assertEqual(self.ns["stock_fund_flow_rank"]()["rows"], [])
        with self.assertRaises(ValueError):
            self.ns["industry_fund_flow_rank"]("3d")
        with self.assertRaises(ValueError):
            self.ns["stock_fund_flow_rank"]("today", "sideways")

    def test_pagination_uses_reported_total(self):
        self.pages[1] = {"total": 2, "diff": [{"f12": "000001", "f62": 100}]}
        self.pages[2] = {"total": 2, "diff": [{"f12": "000002", "f62": 90}]}
        result = self.ns["stock_fund_flow_rank"]("today", "in", 2)
        self.assertEqual([row["code"] for row in result["rows"]], ["000001", "000002"])
        self.assertEqual([call[1]["params"]["pn"] for call in self.calls], ["1", "2"])


if __name__ == "__main__":
    unittest.main()
