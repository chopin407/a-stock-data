"""Offline contracts for the Eastmoney dragon-tiger detail page."""

import ast
import re
import unittest
from datetime import datetime
from pathlib import Path


SKILL = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")


def load_functions():
    section = SKILL.split("### 3.9 全市场龙虎榜", 1)[1].split("### 3.10", 1)[0]
    source = re.search(r"```python\n(.*?)\n```", section, re.S).group(1)
    tree = ast.parse(source)
    tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    namespace = {"datetime": datetime}
    exec(compile(tree, "SKILL.md:dragon-tiger", "exec"), namespace)
    return namespace


class DragonTigerDetailRangeTests(unittest.TestCase):
    def test_date_filter_columns_and_pagination_helper(self):
        ns = load_functions()
        calls = []
        ns["_em_datacenter_strict"] = lambda *args, **kwargs: calls.append((args, kwargs)) or []
        self.assertEqual(ns["dragon_tiger_detail_range"]("2026-09-28", "2026-09-30"), [])
        args, kwargs = calls[0]
        self.assertEqual(args, ("RPT_DAILYBILLBOARD_DETAILSNEW",))
        self.assertEqual(kwargs["filter_str"],
                         "(TRADE_DATE<='2026-09-30')(TRADE_DATE>='2026-09-28')")
        self.assertEqual((kwargs["sort_columns"], kwargs["sort_types"]),
                         ("SECURITY_CODE,TRADE_DATE", "1,-1"))
        self.assertIn("D10_CLOSE_ADJCHRATE", kwargs["columns"])
        self.assertEqual(kwargs["max_rows"], float("inf"))

    def test_bad_range_rejected_before_request(self):
        ns = load_functions()
        with self.assertRaises(ValueError):
            ns["dragon_tiger_detail_range"]("2026-09-30", "2026-09-28")

    def test_daily_summary_uses_full_range_and_sorts(self):
        ns = load_functions()
        calls = []
        def fetch(start, end):
            calls.append((start, end))
            return [
                {"TRADE_DATE": "2026-09-29", "SECURITY_CODE": "000001",
                 "BILLBOARD_NET_AMT": 10000},
                {"TRADE_DATE": "2026-09-29", "SECURITY_CODE": "000002",
                 "BILLBOARD_NET_AMT": 30000},
            ]
        ns["dragon_tiger_detail_range"] = fetch
        result = ns["daily_dragon_tiger"]("2026-09-29")
        self.assertEqual(calls, [("2026-09-29", "2026-09-29")])
        self.assertEqual(result["total_records"], 2)
        self.assertEqual([r["code"] for r in result["stocks"]], ["000002", "000001"])


if __name__ == "__main__":
    unittest.main()
