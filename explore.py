"""explore.py -- 读一个 CSV，打印基础统计。

这一版的三处关键代码已填好，并逐行写了注释。
你要做的是读懂每一行，然后回答我在聊天里问的两个问题。
"""
from pathlib import Path

import pandas as pd

CSV = Path("data/orders.csv")


def main() -> None:
    # ① 读进来。read_csv 会自己猜类型：全数字 -> 数值列；
    #    只要混进一个 "未知" 这种文字，整列就变成字符串（dtype=str）。
    df = pd.read_csv(CSV)

    # ② shape 是 (行数, 列数) 的元组。
    print("shape:", df.shape)

    # ③ isna() 给你一张 True/False 表，sum() 把它按列加起来 -> 每列缺几个。
    print("missing:", df.isna().sum())

    print("dtypes:")
    for col, dt in df.dtypes.items():
        print(f"  {col:<10} {dt}")


if __name__ == "__main__":
    main()
