# GuanCLI vs Parquet 日期维度对比记录

测试时间：2026-06-02

## 测试对象

GuanCLI 数据集：

- URL: `https://guandata.shuixing.com/data-center/data-sets/se1ce25d4080c471fa5f2bb9/w24ef49e5ebbd4a6ba556995/details/overview?limit=50&nameLike=%E6%AF%9B%E5%88%A9`
- dsId: `w24ef49e5ebbd4a6ba556995`
- 名称: `毛利表-剔除订单维度_数据集`
- 类型: `DATAFLOW`
- 存储: `ETL_PARQUET`
- 元数据行数: `30,941,181`
- 字段数: `61`
- 更新时间: `2026-06-02 06:39:15+0800`
- 安全配置: `securityFilterColumnLevelEnabled=true`, `securityFilterRowLevelEnabled=true`

Parquet Gateway 数据集：

- dataset: `dmk_sale_margin_delivery_dtl`
- 数据目录: `/home/ai_ds/sale/dmk_sale_margin_delivery_dtl/`
- 网关路径: `/home/ai_ds/sd_data_center/dmk_sale_margin_delivery_dtl`
- 数据规模: `25` 个文件，约 `11G`

## 查询能力差异

GuanCLI 当前环境：

- `guancli ds get <dsId> --brief` 可用。
- `guancli ds preview <dsId> --filter ...` 可用。
- `guancli ds execute-sql` 不可用，BI 返回 `Request method 'POST' is not supported`，因此当前不能通过 GuanCLI 对该数据集做完整服务端 SQL 聚合。
- `ds preview --raw` 会返回过滤后的 `rowCount`，可用于验证日期窗口行数，但不能返回聚合指标。

Parquet Gateway 当前环境：

- `opencli parquet query` 可用。
- 支持 `where`、`group-by`、`aggregate`。
- 可直接在服务器侧按日期维度做完整聚合。

## 日期窗口行数对比

业务窗口：`20250101-20260331`

| 来源 | 日期字段/过滤 | 行数 |
|---|---|---:|
| GuanCLI | `立账日期 BT 20250101,20260331` | `1,513,337` |
| GuanCLI | `发货日期 BT 20250101,20260331` | `1,512,807` |
| Parquet Gateway | `ar_date>=20250101 AND ar_date<=20260331` | `19,940,428` |

判断：

- 当前 GuanCLI 账号看到的日期窗口行数约 `151万`，明显小于 Parquet Gateway 的 `1994万`。
- GuanCLI 数据集本身启用了行级和列级安全过滤，预览接口返回的数据很可能是当前用户权限下的可见数据，不等同于全量底表。
- 不能直接拿 GuanCLI 当前账号的预览结果与 Parquet 全量结果做数值一致性校验。

## 单日样本对比

测试日期：`20250108`

Parquet Gateway，`ar_date=20250108`：

| 指标 | 数值 |
|---|---:|
| 行数 | `46,848` |
| 销售数量 `actual_output_qty` | `69,157.34` |
| 退货数量 `return_qty` | `7,105.00` |
| 销售金额 `local_amount` | `12,518,055.69` |
| 退货金额 `local_return_amount` | `1,891,368.27` |

GuanCLI，`立账日期=20250108`，本地只聚合必要列：

| 指标 | 数值 |
|---|---:|
| 行数 | `2,987` |
| 销售量 | `27,272.34` |
| 发货数量 | `28,619.34` |
| 退货数量 | `1,347.00` |
| 销售金额未税 | `4,534,100.81` |
| 销售金额含税 | `5,123,533.92` |
| 退货金额未税 | `307,903.27` |

GuanCLI，`发货日期=20250108`，本地只聚合必要列：

| 指标 | 数值 |
|---|---:|
| 行数 | `3,039` |
| 销售量 | `21,336.34` |
| 退货数量 | `1,347.00` |
| 销售金额未税 | `4,636,882.83` |
| 销售金额含税 | `5,239,677.60` |
| 退货金额未税 | `307,903.27` |

判断：

- 单日样本也不一致，差异首先体现在行数，说明两边不是同一可见数据全集。
- `ar_date` 更接近 GuanCLI 的 `立账日期`，但即使用 `立账日期=20250108`，GuanCLI 可见行数也只有 `2,987`，远小于 Parquet 的 `46,848`。
- GuanCLI 的 `销售量` 包含退货负数；`发货数量` 更接近正向发货口径，但仍无法与 Parquet 全量直接对齐。

## GuanCLI 使用经验

本次经验：用 GuanCLI 做数据验证时，优先从数据集入手，而不是优先从看板卡片入手。

推荐路径：

1. 先定位数据集 `dsId`。
2. 用 `guancli ds get <dsId> --brief` 查看数据集名称、字段、字段类型、更新时间、行数和安全配置。
3. 明确日期字段和指标字段，例如本次同时存在 `立账日期`、`发货日期`、`发货日期-日期格式`，不能直接假设它们等同于 Parquet 的 `ar_date`。
4. 用 `guancli ds preview <dsId> --filter ... --columns ... --raw` 做服务端过滤和行数确认。
5. 如需本地聚合，只导出必要列和必要日期窗口；不要拉取全量明细进入上下文。

为什么优先数据集：

- 数据集是字段和口径的源头，能直接看到字段类型、维度/度量属性、更新时间、行级/列级安全配置。
- 数据集查询更适合做跨系统口径校验，因为可以明确筛选字段、日期字段和指标字段。
- 看板卡片往往叠加了筛选器、计算字段、展示层聚合、排序、Top N、权限和页面交互状态，直接用卡片做底层数据对比容易把展示口径误认为数据口径。

什么时候使用看板卡片：

- 已经确认要复现业务人员在看板上看到的结果时，可以查卡片。
- 需要确认某个页面实际展示逻辑、筛选器传参或卡片口径时，可以查卡片。
- 如果 BI 侧已经有专门为校验建立的聚合卡片或指标，并且该卡片口径被业务确认，可以用 GuanCLI 查卡片结果作为对照。

本次限制：

- 当前 BI 的 `ds execute-sql` 不可用，因此数据集路径只能完成字段确认、过滤预览和有限样本聚合，不能完成全量服务端 sum/group-by。
- 当前账号受行级/列级安全过滤影响。GuanCLI 查到的是当前用户可见口径，不等同于 Parquet 全量底表口径。
- 后续要做严谨对账，优先方案不是直接查看板，而是准备一个具备全量权限或明确业务过滤规则的数据集/指标，再通过 GuanCLI 查询。

## 结论

1. GuanCLI 对该数据集的结构识别、日期过滤、列裁剪和样本落盘测试通过。
2. 当前 BI 不支持 `ds execute-sql` 高级 SQL 聚合接口，因此 GuanCLI 不能像 Parquet Gateway 一样直接做完整服务端日期维度聚合。
3. 当前 GuanCLI 账号受行级/列级安全过滤影响，日期窗口可见行数约 `151万`；Parquet Gateway 同窗口全量行数为 `1994万`。两边不能直接做全量指标一致性校验。
4. 使用 GuanCLI 做数据验证时，优先查询数据集，再按需要追踪看板卡片；不要一开始就用看板卡片代表底层数据口径。
5. 在周五分享中应把 GuanCLI 定位为 BI 口径与权限下的业务数据查询入口，把 Parquet Gateway 定位为服务器侧全量 Parquet 聚合分析入口。
6. 若要继续做严格一致性校验，需要让 GuanCLI 使用具备全量权限的账号，或在 Guandata 中创建一个不受行级过滤影响的校验数据集/指标，再由 GuanCLI 查询该聚合结果。

## 本次未进入上下文的内容

- 未拉取全量明细。
- GuanCLI 单日样本只将必要列落盘到本地 CSV 后聚合。
- Parquet 只返回聚合结果。
