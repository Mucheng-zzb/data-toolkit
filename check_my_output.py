"""check_my_output.py -- 成绩单（也给下一步复用）。

用法一：直接评你的脚本（推荐）
    python check_my_output.py --run explore.py data/orders.csv

用法二：评一个已经保存好的输出文件
    python check_my_output.py my_output.txt data/orders.csv

评判标准全部从 CSV 现算，不写死任何数字：
- 行数 / 列数是否出现；
- 每个列名是否出现；
- 每列的缺失计数是否能对得上；
- 数值列（dtype 是 float64/int64 的列）的 dtype 是否和输出绑定在一起。
"""
import argparse
import io
import re
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pandas as pd


def expected(csv: Path) -> dict:
    df = pd.read_csv(csv)
    return {
        "rows": len(df),
        "cols": df.shape[1],
        "missing": {c: int(n) for c, n in df.isna().sum().items()},
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "numeric_cols": [c for c, t in df.dtypes.items() if pd.api.types.is_numeric_dtype(t)],
    }


def run_script(script: Path, cwd: Path) -> str:
    """在子进程里跑学生的脚本，捕获 stdout（和终端里 python 跑出来的一致）。"""
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        print("!! 你的脚本非正常退出（这就是要修的东西）：")
        print((proc.stderr or "").strip()[-1500:])
        print()
    return (proc.stdout or "")


def grade(text: str, exp: dict) -> int:
    checks = []

    def check(name, ok):
        checks.append((name, bool(ok)))

    if "\ufffd" in text:
        print("!! 警告: 输出不是有效 UTF-8。先设置 $env:PYTHONIOENCODING = \"utf-8\" 再重跑。\n")

    check(f"行数 = {exp['rows']}", re.search(rf"\b{exp['rows']}\b", text) is not None)
    check(f"列数 = {exp['cols']}", re.search(rf"\b{exp['cols']}\b", text) is not None)
    for col in exp["dtypes"]:
        check(f"列名出现在输出里: {col}", col in text)
    for col, n in exp["missing"].items():
        check(f"缺失计数可核对: {col} = {n}", col in text and re.search(rf"\b{n}\b", text) is not None)
    for col in exp["numeric_cols"]:
        check(f"{col} 的 dtype 标为数值类型", re.search(rf"{re.escape(col)}[^\n]*\b(float64|int64)\b", text) is not None)
    check("打印了 str（说明确实输出了 dtype）", "str" in text)

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    print(f"成绩单: {passed}/{total}")
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print("-" * 44)
    print("期望缺失计数:", exp["missing"])
    print("期望 dtype   :", exp["dtypes"])
    return 0 if passed == total else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="给 explore.py 打分（标准从 CSV 现算）")
    parser.add_argument("target", type=Path, help="explore.py 的输出文件，或用 --run 时传脚本路径")
    parser.add_argument("csv", type=Path, help="对应的输入 CSV")
    parser.add_argument("--run", action="store_true", help="把 target 当成脚本直接运行并评分")
    args = parser.parse_args()

    if args.run:
        text = run_script(args.target, args.csv.resolve().parent.parent)
    else:
        text = args.target.read_text(encoding="utf-8", errors="replace")

    return grade(text, expected(args.csv))


if __name__ == "__main__":
    sys.exit(main())
