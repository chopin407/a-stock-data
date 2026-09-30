"""Offline contract checks for the two Eastmoney pools added to SKILL.md §8.1."""

import ast
import re
import unittest
from pathlib import Path


SKILL = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
BLOCK = SKILL.split("### 8.1 东财涨停板池", 1)[1].split("### 8.2", 1)[0]
CODE = re.search(r"```python\n(.*?)\n```", BLOCK, re.S).group(1)


def load_pool_code():
    tree = ast.parse(CODE)
    tree.body = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.Assign))
                 and not (isinstance(node, ast.Assign) and any(
                     isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                     and call.func.id == "em_zt_pool" for call in ast.walk(node)))]
    namespace = {"UA": "test-agent"}
    exec(compile(tree, "SKILL.md:8.1", "exec"), namespace)
    return namespace


class PoolTests(unittest.TestCase):
    def setUp(self):
        self.ns = load_pool_code()
        self.calls = []
        self.pool = []

        def fake_em_get(url, **kwargs):
            self.calls.append((url, kwargs))

            class Response:
                def json(inner_self):
                    return {"data": {"pool": self.pool}}

            return Response()

        self.ns["em_get"] = fake_em_get

    def test_strong_pool(self):
        self.pool = [{"c": "600001", "n": "样本", "p": 12340, "ztp": 12500,
                      "zdp": 5.23, "hs": 3.45, "cc": 3, "nh": 1, "lb": 1.8,
                      "amount": 200000, "ltsz": 300000, "tshare": 400000,
                      "zs": 0.5, "hybk": "机械", "zttj": {"days": 5, "ct": 2}}]
        row, = self.ns["em_qs_pool"]("20260930")
        url, kwargs = self.calls[-1]
        self.assertTrue(url.endswith("/getTopicQSPool"))
        self.assertEqual(kwargs["params"]["sort"], "zdp:desc")
        self.assertEqual(kwargs["params"]["date"], "20260930")
        self.assertEqual(row["price"], 12.34)
        self.assertEqual(row["reason"], "60日新高且近期多次涨停")
        self.assertTrue(row["new_high"])
        self.assertEqual(row["zt_stat"], "5天2板")

    def test_sub_new_pool(self):
        self.pool = [{"c": "301001", "n": "次新样本", "p": 17890,
                      "ztp": 100000001, "zdp": -1.25, "hs": 4.2, "ods": 6,
                      "od": 20260920, "ipod": 20260912, "nh": 0}]
        row, = self.ns["em_cx_pool"]("20260930")
        url, kwargs = self.calls[-1]
        self.assertTrue(url.endswith("/getTopicCXPooll"))
        self.assertEqual(kwargs["params"]["sort"], "ods:asc")
        self.assertEqual(row["open_days"], 6)
        self.assertEqual(row["open_date"], "20260920")
        self.assertEqual(row["list_date"], "20260912")
        self.assertIsNone(row["limit_price"])
        self.assertFalse(row["new_high"])

    def test_empty_pool(self):
        self.assertEqual(self.ns["em_qs_pool"]("20260930"), [])
        self.assertEqual(self.ns["em_cx_pool"]("20260930"), [])


if __name__ == "__main__":
    unittest.main()
