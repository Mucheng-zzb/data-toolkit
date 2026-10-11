"""verify.py —— 独立复核参考（量尺，不是你的 explore.py）。

用法:
    python verify.py data/orders.csv

它用一套独立写法把该算的都算一遍。你只需要让 explore.py 的每个数字
在下面找到同一个值；对不上就是 explore.py 的问题，不要去改这个文件。
"""
import argparse
import sys
from pathlib import Path

import pandas as pd


def main() -> int:
    parser = argparse.ArgumentParser(description="独立复核 explore.py 的数字是否正确")
    parser.add_argument("csv", type=Path, help="要复核的 CSV 文件")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)

    print("=" * 52)
    print("参考答案（独立算一遍）")
    print("=" * 52)
    print(f"行数 len(df) : {len(df)}")
    print(f"形状 shape   : {df.shape}")
    print("-" * 52)
    print("每列 dtype:")
    for col, dt in df.dtypes.items():
        print(f"  {col:<10} {dt}")
    print("-" * 52)
    print("每列缺失值个数:")
    for col, n in df.isna().sum().items():
        print(f"  {col:<10} {n}")
    print("-" * 52)
    print("被当缺失值处理过的字面量（pandas 默认名单）:")
    raw = pd.read_csv(args.csv, keep_default_na=False)
    for col in raw.columns:
        hits = [v for v in raw[col].tolist() if v == ""]
        if hits:
            print(f"  {col:<10} 空字符串 x{len(hits)}")

    print("-" * 52)
    print("数值列统计（先 to_numeric 再算）:")
    numeric = {}
    for col in df.columns:
        s = pd.to_numeric(df[col], errors="coerce")
        if s.notna().sum() == 0:
            continue
        numeric[col] = s
        converted = int(s.isna().sum() - df[col].isna().sum())
        print(f"  {col:<10} 有效 {int(s.notna().sum())}/{len(s)}"
              f"  mean={s.mean():.4f}  median={s.median():.4f}"
              f"  (转换时报废 {converted} 个)")
    print("-" * 52)
    print("分组计数（用第一个非数值列分组）:")
    cats = [c for c in df.columns if c not in numeric]
    if cats and numeric:
        g = df.groupby(cats[0])
        for col in numeric:
            print(f"  分组列={cats[0]}  计数列={col}")
            print(f"    count: {g[col].count().to_dict()}")
            print(f"    size : {g[col].size().to_dict()}")
    else:
        print("  跳过：没同时找到分类列和数值列")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())
