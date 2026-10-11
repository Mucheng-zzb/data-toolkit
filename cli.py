"""cli.py -- 命令行入口。

目标形态:
    python cli.py input.csv --out out/

这一版先做到: 接受任意 CSV 路径，打印 行数 / 缺失 / dtype / 数值列均值与中位数。
TODO 只有一处（第 30 行附近），其余是结构。
"""
import argparse
import sys
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="读一个 CSV，打印基础统计（行数 / 缺失 / dtype / 均值与中位数）"
    )
    parser.add_argument("csv", type=Path, help="输入的 CSV 文件路径")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("out"),
        help="输出目录（本轮还不写文件，先留着）",
    )
    return parser.parse_args()


def load(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"找不到文件: {path}")
    return pd.read_csv(path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """清洗：这里目前只做一件事，把完全空白的行去掉。"""
    before = len(df)
    df = df.dropna(how="all")
    dropped = before - len(df)
    if dropped:
        print(f"[clean] 去掉了 {dropped} 个全空行")
    return df


def report(df: pd.DataFrame) -> None:
    print(f"[shape] {df.shape[0]} 行 x {df.shape[1]} 列")

    print("[missing] 每列缺失值个数:")
    for col, n in df.isna().sum().items():
        print(f"  {col:<10} {n}")

    print("[dtypes] 每列类型:")
    for col, dt in df.dtypes.items():
        print(f"  {col:<10} {dt}")

    print("[numeric] 数值列统计:")
    for col in df.columns:
        # 这一列像不像数值列：能转成数字的值占比 >= 60%
        s = pd.to_numeric(df[col], errors="coerce")
        if s.notna().mean() < 0.6:
            continue
        # TODO: 用 s 打印这一列的 mean 和 median（提示: s.mean(), s.median()）
        print(f"  {col:<10} 有效 {int(s.notna().sum())}/{len(s)}")


def main() -> int:
    args = parse_args()
    df = clean(load(args.csv))
    args.out.mkdir(parents=True, exist_ok=True)
    report(df)
    return 0


if __name__ == "__main__":
    sys.exit(main())
