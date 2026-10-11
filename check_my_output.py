"""check_my_output.py -- 成绩单。

用法（Windows PowerShell，注意先设好 UTF-8）:
    $env:PYTHONIOENCODING = "utf-8"
    python explore.py > my_output.txt
    python check_my_output.py my_output.txt data/orders.csv

它不重新实现 pandas 逻辑，只做一件事：把你输出里的数字和独立算出的
期望值逐项对照，然后打印 PASS/FAIL 和分数。
如果它在列名上大面积 FAIL，先检查编码：my_output.txt 必须以 utf-8 保存。
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
        "shape": list(df.shape),
        "missing": {c: int(n) for c, n in df.isna().sum().items()},
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="给 explore.py 的输出打分")
    parser.add_argument("output", type=Path, help="explore.py 的输出保存成的文件")
    parser.add_argument("csv", type=Path, help="对应的输入 CSV")
    args = parser.parse_args()

    raw = args.output.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    if "\ufffd" in text:
        print("!! 警告: 输出文件不是有效的 UTF-8（出现替换字符）。")
        print("   先执行 $env:PYTHONIOENCODING = \"utf-8\" 再重跑 explore.py。")
        print()

    exp = expected(args.csv)
    checks = []

    def check(name, ok):
        checks.append((name, bool(ok)))

    check(f"行数 = {exp['rows']}", re.search(rf"\b{exp['rows']}\b", text) is not None)
    check(f"列数 = {exp['shape'][1]}", re.search(rf"\b{exp['shape'][1]}\b", text) is not None)
    for col, dt in exp["dtypes"].items():
        check(f"列名出现在输出里: {col}", col in text)
    check("打印了 float64", "float64" in text)
    for col, n in exp["missing"].items():
        check(f"缺失计数可用: {col} = {n}", col in text and re.search(rf"\b{n}\b", text) is not None)
    for col, dt in exp["dtypes"].items():
        if dt == "float64":
            check(f"{col} 的 dtype 应为 float64", re.search(rf"{re.escape(col)}[^\n]*float64", text) is not None)

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    print(f"成绩单: {passed}/{total}")
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print("-" * 44)
    print("期望缺失计数:", exp["missing"])
    print("期望 dtype   :", exp["dtypes"])
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
