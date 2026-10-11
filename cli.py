"""cli.py -- 命令行入口。

用法:
    python cli.py input.csv --out out/
    python cli.py input.csv --no-plot

做三件事: 清洗（去掉全空行）-> 统计（行数/缺失/dtype/均值中位数/分组计数）-> 出图。
"""
import argparse
import sys
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="读一个 CSV，打印基础统计并出图"
    )
    parser.add_argument("csv", type=Path, help="输入的 CSV 文件路径")
    parser.add_argument(
        "--out", type=Path, default=Path("out"), help="输出目录（图写到这里）"
    )
    parser.add_argument(
        "--no-plot", action="store_true", help="只打印统计，不出图"
    )
    return parser.parse_args()


def load(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"找不到文件: {path}")
    return pd.read_csv(path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """清洗：目前只去掉完全空白的行，并打印丢掉了几行。"""
    before = len(df)
    df = df.dropna(how="all")
    dropped = before - len(df)
    if dropped:
        print(f"[clean] 去掉了 {dropped} 个全空行")
    return df


def numeric_cols(df: pd.DataFrame, threshold: float = 0.6) -> list[str]:
    """能转成数字的值占比 >= threshold 的列，算数值列。"""
    return [
        c for c in df.columns
        if pd.to_numeric(df[c], errors="coerce").notna().mean() >= threshold
    ]


def report(df: pd.DataFrame) -> None:
    print(f"[shape] {df.shape[0]} 行 x {df.shape[1]} 列")

    print("[missing] 每列缺失值个数:")
    for col, n in df.isna().sum().items():
        print(f"  {col:<10} {n}")

    print("[dtypes] 每列类型:")
    for col, dt in df.dtypes.items():
        print(f"  {col:<10} {dt}")

    print("[numeric] 数值列统计:")
    for col in numeric_cols(df):
        s = pd.to_numeric(df[col], errors="coerce")
        # NaN 参与比较时总是 False，所以 == 和 < 不会被 NaN 污染；
        # 但 (s != 0).sum() 会把 NaN 算进去（NaN != 0 是 True），别用那个写法。
        zeros = int((s == 0).sum())
        negatives = int((s < 0).sum())
        print(
            f"  {col:<10} 有效 {int(s.notna().sum())}/{len(s)}"
            f"  mean={s.mean():.4f}  median={s.median():.4f}"
            f"  zeros={zeros}  negatives={negatives}"
        )


def group_counts(df: pd.DataFrame) -> None:
    """按取值少的非数值列分组计数。"""
    nums = numeric_cols(df)
    for col in df.columns:
        if col in nums:
            continue
        if 1 < df[col].nunique(dropna=False) < max(2, len(df) * 0.5):
            print(f"[group] 按 {col} 分组计数:")
            for key, n in df[col].value_counts(dropna=False).items():
                print(f"  {key:<10} {n}")
            return
    print("[group] 没找到合适的分类列，跳过")


def plot(df: pd.DataFrame, out_dir: Path) -> None:
    """出两张图: 分组柱状图 + 数值分布直方图。"""
    import matplotlib
    matplotlib.use("Agg")  # 无界面渲染，必须写在 pyplot 之前
    import matplotlib.pyplot as plt

    # Windows 自带中文字体；不设这两行，图里的中文会变成方框
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    out_dir.mkdir(parents=True, exist_ok=True)
    nums = numeric_cols(df)
    cats = [
        c for c in df.columns
        if c not in nums and 1 < df[c].nunique(dropna=False) < max(2, len(df) * 0.5)
    ]

    if cats and nums:
        cat, num = cats[0], nums[0]
        agg = df.groupby(cat)[num].count().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(6, 4))
        agg.plot(kind="bar", ax=ax, color="#4c78a8", edgecolor="white")
        ax.set_title(f"各{cat}的{num}有效记录数")
        ax.set_xlabel(cat)
        ax.set_ylabel(f"{num}（条）")
        ax.tick_params(axis="x", rotation=0)
        fig.tight_layout()
        target = out_dir / "by_group.png"
        fig.savefig(target, dpi=140)
        plt.close(fig)
        print(f"[plot] 已写出 {target}")

    if nums:
        num = nums[0]
        s = pd.to_numeric(df[num], errors="coerce").dropna()
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(s, bins=min(10, max(3, int(s.nunique()))), color="#f58518", edgecolor="white")
        ax.set_title(f"{num} 的分布（{len(s)} 个有效值）")
        ax.set_xlabel(num)
        ax.set_ylabel("频数")
        fig.tight_layout()
        target = out_dir / "hist.png"
        fig.savefig(target, dpi=140)
        plt.close(fig)
        print(f"[plot] 已写出 {target}")


def main() -> int:
    args = parse_args()
    df = clean(load(args.csv))
    report(df)
    group_counts(df)
    if not args.no_plot:
        plot(df, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
