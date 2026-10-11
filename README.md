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

终端输出（用上面那条命令原样跑出来）:

```text
[shape] 49 行 x 5 列
[missing] 每列缺失值个数:
  订单号        0
  门店         0
  数量         12
  单价         0
  日期         0
[dtypes] 每列类型:
  订单号        str
  门店         str
  数量         float64
  单价         str
  日期         str
[numeric] 数值列统计:
  数量         有效 37/49  mean=3.2973  median=3.0000
  单价         有效 41/49  mean=11.6098  median=12.0000
[group] 按 门店 分组计数:
  东区         19
  西区         11
  北区         10
  南区         9
[plot] 已写出 C:\Users\zzb12\Desktop\data-toolkit\out\by_group.png
[plot] 已写出 C:\Users\zzb12\Desktop\data-toolkit\out\hist.png
```

## 已知限制

- 统计只打到终端，没有写进文件；要留档得自己重定向（`> report.txt`）。
- "哪一列是数值列"用的是比例启发式（能被 `to_numeric` 转换的值 >= 60%），
  所以一列里混了太多文字时，它会被当成分类列而不是数值列。
- 日期列没有解析成 `datetime`，全程当字符串处理，因此做不了"按月聚合"。
- `--out` 目前只用来放图，还没有别的产物。
- `数量`/`单价` 这类"看起来是数字但有脏值"的列，转换时报废掉的值（如 `未知`）只体现在
  `有效 41/49` 里，没有单独报出"有几个值转不动"。
- `zeros`/`negatives` 是按转换后的数值列统计的；如果一列里混了日期字符串，它整列都不会进数值统计。

## 目录结构

```text
cli.py             命令行入口（清洗 -> 统计 -> 出图）
explore.py         第一步的教学脚本（只读 + 打印）
check_my_output.py 成绩单: python check_my_output.py --run explore.py data/orders.csv
verify.py          独立量尺: python verify.py data/orders.csv --by 门店
data/              示例输入
out/               生成的图（已 gitignore）
```
