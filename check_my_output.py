"""check_my_output.py -- 成绩单。

用法:
    python explore.py > my_output.txt
    python check_my_output.py my_output.txt data/orders.csv

它不重新实现 pandas 逻辑，只做一件事：把你输出里的数字和独立算出的
期望值逐项对照，然后打印 PASS/FAIL 和分数。
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd


def expected(csv: Path) -> dict:
    df = pd.read_csv(csv)
    return {
        "rows": len(df),
        "cols": df.shape[1],
        "missing": {c: int(n) for c, n in df.isna().sum().items()},
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="给 explore.py 的输出打分")
    parser.add_argument("output", type=Path, help="explore.py 的输出保存成的文件")
    parser.add_argument("csv", type=Path, help="对应的输入 CSV")
    args = parser.parse_args()

    text = args.output.read_text(encoding="utf-8", errors="replace")
    exp = expected(args.csv)
    checks = []

    def check(name, ok, detail=""):
        checks.append((name, bool(ok), detail))

    check("打印了行数 10", re.search(r"\b10\b", text) is not None)
    check("打印了列数 5", re.search(r"\b5\b", text) is not None)
    check("出现 float64", "float64" in text)
    check("出现 3（缺失值个数）", re.search(r"\b3\b", text) is not None)
    for col, n in exp["missing"].items():
        if n:
            check(f"缺失列 {col} = {n}", col in text)
    for col in exp["dtypes"]:
        check(f"输出里出现列名 {col}", col in text)
    check("出现 str（说明打印了 dtype）", "str" in text)

    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    print(f"成绩单: {passed}/{total}")
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")
    print("-" * 40)
    print("期望缺失计数:", exp["missing"])
    print("期望 dtype   :", exp["dtypes"])
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
