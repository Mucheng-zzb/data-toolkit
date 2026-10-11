"""verify.py —— 独立复核参考（量尺，不是你的 explore.py）。

用法:
    python verify.py data/orders.csv
    python verify.py data/orders.csv --by 门店 --json

它用一套独立写法把该算的都算一遍。你只需要让 explore.py 的每个数字
在下面找到同一个值；对不上就是 explore.py 的问题，不要去改这个文件。
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def to_numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce")


def is_numeric_like(df: pd.DataFrame, col: str) -> bool:
    """这一列像不像数字列：转得动，且大部分值有效。"""
    s = to_numeric_series(df, col)
    return s.notna().sum() >= len(df) * 0.8


def pick_group_col(df: pd.DataFrame) -> str | None:
    """挑一个"取值少"的非数值列当分组列。"""
    for col in df.columns:
        if is_numeric_like(df, col):
            continue
        if 1 < df[col].nunique(dropna=False) <= max(2, len(df) // 4):
            return col
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="独立复核 explore.py 的数字是否正确")
    parser.add_argument("csv", type=Path, help="要复核的 CSV 文件")
    parser.add_argument("--by", default=None, help="分组列名（默认自动挑一个取值少的非数值列）")
    parser.add_argument("--json", action="store_true", help="只输出 JSON 摘要")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)

    # 数值列：这一列"像数字"，才算数值列
    numeric = {}
    for col in df.columns:
        if is_numeric_like(df, col):
            numeric[col] = to_numeric_series(df, col)

    group_col = args.by or pick_group_col(df)

    summary = {
        "rows": int(len(df)),
        "shape": list(df.shape),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing": {c: int(n) for c, n in df.isna().sum().items()},
        "numeric": {
            c: {
                "valid": int(s.notna().sum()),
                "mean": round(float(s.mean()), 4),
                "median": round(float(s.median()), 4),
                "broken_in_conversion": int(s.isna().sum() - df[c].isna().sum()),
            }
            for c, s in numeric.items()
        },
        "group_col": group_col,
        "group_count": {},
        "group_size": {},
    }
    if group_col and numeric:
        g = df.groupby(group_col)
        for c in numeric:
            summary["group_count"][c] = {str(k): int(v) for k, v in g[c].count().items()}
            summary["group_size"][c] = {str(k): int(v) for k, v in g[c].size().items()}

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    print("=" * 52)
    print("参考答案（独立算一遍）")
    print("=" * 52)
    print(f"行数 len(df) : {summary['rows']}")
    print(f"形状 shape   : {tuple(summary['shape'])}")
    print("-" * 52)
    print("每列 dtype:")
    for col, dt in summary["dtypes"].items():
        print(f"  {col:<10} {dt}")
    print("-" * 52)
    print("每列缺失值个数:")
    for col, n in summary["missing"].items():
        print(f"  {col:<10} {n}")
    print("-" * 52)
    print("数值列统计:")
    for col, st in summary["numeric"].items():
        print(f"  {col:<10} 有效 {st['valid']}/{summary['rows']}"
              f"  mean={st['mean']:.4f}  median={st['median']:.4f}"
              f"  (转换时报废 {st['broken_in_conversion']} 个)")
    print("-" * 52)
    if group_col and summary["group_count"]:
        print(f"分组计数（分组列 = {group_col}）:")
        for col in summary["group_count"]:
            print(f"  计数列 {col}")
            print(f"    count: {summary['group_count'][col]}")
            print(f"    size : {summary['group_size'][col]}")
    else:
        print("分组计数: 跳过（没找到合适的分类列，可用 --by 指定）")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())
