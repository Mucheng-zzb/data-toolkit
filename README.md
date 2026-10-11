# data-toolkit

一个读 CSV、清洗、打印统计并出图的小工具。只依赖 pandas 和 matplotlib。

## 装什么

需要 Python 3.11 或更高。在项目根目录执行:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows PowerShell
python -m pip install -r requirements.txt
```

> 非 Windows: 把激活那行换成 `source .venv/bin/activate`。

## 一条能跑的命令

```powershell
python cli.py data/orders_big.csv --out out/
```

它会在终端打印: 形状、每列缺失数、每列 dtype、数值列均值与中位数、分组计数；
并把两张图写进 `out/`。

只想看数字不出图:

```powershell
python cli.py data/orders_big.csv --no-plot
```

## 示例输入

`data/orders_big.csv`（49 行，故意留了缺失值和"未知"）:

```csv
订单号,门店,数量,单价,日期
A001,东区,2,9.5,2025-03-01
A002,西区,1,12.0,2025-03-01
...
```

## 示例输出

![各门店的有效记录数](out/by_group.png)

![数量的分布](out/hist.png)

终端输出:

```text
<!-- TODO: 把你跑出来的终端输出粘进来 -->
```

## 已知限制

<!-- TODO: 写 2-3 条。例如:
- 只把统计打到终端，没有写进文件
- "哪列是数值列"用的是比例启发式（>= 60% 可转换），可能判错
- 日期列没有解析成 datetime，只当字符串
-->

## 目录结构

```text
cli.py             命令行入口（清洗 -> 统计 -> 出图）
explore.py         第一步的教学脚本（只读 + 打印）
check_my_output.py 成绩单: python check_my_output.py --run explore.py data/orders.csv
verify.py          独立量尺: python verify.py data/orders.csv --by 门店
data/              示例输入
out/               生成的图（已 gitignore）
```
