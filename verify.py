"""verify.py -- 独立复核参考（量尺，不是你的 explore.py）。

用法:
    python verify.py data/orders.csv
    python verify.py data/orders.csv --by 门店 --json

它用一套独立写法把该算的都算一遍。你只需要让 explore.py 的每个数字
在下面找到同一个值；对不上就是 explore.py 的问题，不要去改这个文件。

判定是启发式的（所以留了 --by 覆盖口子），阈值写在下面的常量里。
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

NUMERIC_FRACTION = 0.6   # 能转成数字的比例超过它，就当数值列
GROUP_MAX_RATIO = 0.5    # 非数值列取值数 < 行数*0.5，才有资格当分组列


def to_numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce")


def numeric_fraction(df: pd.DataFrame, col: str) -> float:
    return float(to_numeric_series(df, col).notna().mean())


def is_numeric_like(df: pd.DataFrame, col: str) -> bool:
    if pd.api.types.is_numeric_dtype(df[col]):
        return True
    return numeric_fraction(df, col) >= NUMERIC_FRACTION


def pick_group_col(df: pd.DataFrame) -> str | None:
    limit = max(2, int(len(df) * GROUP_MAX_RATIO))
    for col in df.columns:
        if is_numeric_like(df, col):
            continue
        if 1 < df[col].nunique(dropna=False) <= limit:
            return col
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="独立复核 explore.py 的数字是否正确")
    parser.add_argument("csv", type=Path, help="要复核的 CSV 文件")
    parser.add_argument("--by", default=None, help="分组列名（默认自动挑一个取值少的非数值列）")
    parser.add_argument("--json", action="store_true", help="只输出 JSON 摘要")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)

    numeric = {c: to_numeric_series(df, c) for c in df.columns if is_numeric_like(df, c)}
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
