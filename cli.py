"""cli.py -- 命令行入口。

用法:
    python cli.py input.csv --out out/
    python cli.py input.csv --no-plot
    python cli.py input.csv --encoding gbk --by 门店 --value 数量
    python cli.py input.csv --report report.txt

做三件事: 清洗（只去掉完全空白的行）-> 统计（行数/缺失/dtype/均值中位数/分组计数）-> 出图。
"""
import argparse
import contextlib
import sys
from pathlib import Path

import pandas as pd

# 能被 to_numeric 转换的值占比达到这个数，就把该列当成数值列
NUMERIC_THRESHOLD = 0.6


class UserError(Exception):
    """输入或参数的问题。main 捕获后只打印一行消息，不打印堆栈。"""


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
    parser.add_argument(
        "--encoding", default="utf-8",
        help="读 CSV 用的编码（默认 utf-8；中文的 GBK 文件可试 gbk）",
    )
    parser.add_argument(
        "--by", default=None, help="指定分组列（默认按启发式自动猜）"
    )
    parser.add_argument(
        "--value", default=None, help="指定统计与直方图用的数值列（默认按启发式自动猜）"
    )
    parser.add_argument(
        "--report", type=Path, default=None,
        help="把统计同时写进这个文件（UTF-8，会覆盖已有文件）",
    )
    return parser.parse_args()


class Tee:
    """把写进来的东西同时送到多个流（终端 + 报告文件）。"""

    def __init__(self, *streams) -> None:
        self.streams = streams

    def write(self, text: str) -> None:
        for s in self.streams:
            s.write(text)

    def flush(self) -> None:
        for s in self.streams:
            s.flush()


@contextlib.contextmanager
def report_stream(path: Path | None):
    """--report 给出时产出一个「终端 + 文件」的流，没给就产出 None。"""
    if path is None:
        yield None
        return
    try:
        handle = path.open("w", encoding="utf-8")
    except OSError as exc:
        raise UserError(f"写不了报告文件 {path}: {exc.strerror or exc}") from None
    try:
        yield Tee(sys.stdout, handle)
    finally:
        handle.close()


def load(path: Path, encoding: str = "utf-8") -> pd.DataFrame:
    # is_dir 要排在 exists 前面：目录也是"存在"的
    if path.is_dir():
        raise UserError(f"这是一个目录，不是文件: {path}")
    if not path.exists():
        raise UserError(f"找不到文件: {path}")
    try:
        df = pd.read_csv(path, encoding=encoding)
    except UnicodeDecodeError:
        raise UserError(
            f"这个文件可能不是 {encoding} 编码，试试 --encoding gbk: {path}"
        ) from None
    except pd.errors.EmptyDataError:
        raise UserError(f"CSV 是空的或没有表头: {path}") from None
    if len(df.columns) == 0:
        raise UserError(f"CSV 是空的或没有表头: {path}")
    return df


def check_column(df: pd.DataFrame, name: str, role: str) -> str:
    """--by / --value 点名的列必须真的存在，否则报错并列出可用列名。"""
    if name not in df.columns:
        cols = ", ".join(str(c) for c in df.columns)
        raise UserError(f"{role}列不存在: {name}\n可用列名: {cols}")
    return name


def check_value_column(df: pd.DataFrame, name: str) -> str:
    check_column(df, name, "数值")
    nums = numeric_cols(df)
    if name not in nums:
        raise UserError(
            f"列 {name} 不是数值列（能转成数字的值不到 {NUMERIC_THRESHOLD:.0%}），"
            f"可用的数值列: {', '.join(nums) if nums else '（没有）'}"
        )
    return name


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """清洗：目前只去掉完全空白的行，并打印丢掉了几行。"""
    before = len(df)
    df = df.dropna(how="all")
    dropped = before - len(df)
    if dropped:
        print(f"[clean] 去掉了 {dropped} 个全空行")
    return df


def numeric_cols(df: pd.DataFrame, threshold: float = NUMERIC_THRESHOLD) -> list[str]:
    """能转成数字的值占比 >= threshold 的列，算数值列。"""
    return [
        c for c in df.columns
        if pd.to_numeric(df[c], errors="coerce").notna().mean() >= threshold
    ]


def report(df: pd.DataFrame, value: str | None = None) -> None:
    """--value 指定时只统计那一列，否则统计所有数值列。"""
    print(f"[shape] {df.shape[0]} 行 x {df.shape[1]} 列")

    print("[missing] 每列缺失值个数:")
    for col, n in df.isna().sum().items():
        print(f"  {col:<10} {n}")

    print("[dtypes] 每列类型:")
    for col, dt in df.dtypes.items():
        print(f"  {col:<10} {dt}")

    print("[numeric] 数值列统计:")
    for col in ([value] if value else numeric_cols(df)):
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


def print_group(df: pd.DataFrame, col: str) -> None:
    print(f"[group] 按 {col} 分组计数:")
    for key, n in df[col].value_counts(dropna=False).items():
        print(f"  {key:<10} {n}")


def group_counts(df: pd.DataFrame, by: str | None = None) -> None:
    """按取值少的非数值列分组计数；--by 指定时直接用它，跳过启发式。"""
    if by is not None:
        print_group(df, by)
        return
    nums = numeric_cols(df)
    for col in df.columns:
        if col in nums:
            continue
        if 1 < df[col].nunique(dropna=False) < max(2, len(df) * 0.5):
            print_group(df, col)
            return
    print("[group] 没找到合适的分类列，跳过")


def plot(
    df: pd.DataFrame,
    out_dir: Path,
    by: str | None = None,
    value: str | None = None,
) -> None:
    """出两张图: 分组柱状图 + 数值分布直方图。"""
    import matplotlib
    matplotlib.use("Agg")  # 无界面渲染，必须写在 pyplot 之前
    import matplotlib.pyplot as plt

    # Windows 自带中文字体；不设这两行，图里的中文会变成方框
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    out_dir.mkdir(parents=True, exist_ok=True)
    nums = [value] if value else numeric_cols(df)
    if by is not None:
        cats = [by]
    else:
        num_cols = numeric_cols(df)
        cats = [
            c for c in df.columns
            if c not in num_cols and 1 < df[c].nunique(dropna=False) < max(2, len(df) * 0.5)
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
    try:
        df = clean(load(args.csv, args.encoding))
        # 先把列名校验做掉，再打印统计：不然报错前会先刷一屏没用的输出
        value = check_value_column(df, args.value) if args.value else None
        by = check_column(df, args.by, "分组") if args.by else None
        with report_stream(args.report) as stream:
            with contextlib.redirect_stdout(stream or sys.stdout):
                report(df, value)
                group_counts(df, by)
                if not args.no_plot:
                    plot(df, args.out, by, value)
    except UserError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
