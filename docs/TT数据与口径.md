# TT 数据、计算与模型边界

这里的 TT 指产线节拍与产能改善。CT 指某站处理区间时长，不把单站 CT 缩短直接换算为整线收益。

## 事件 CSV

UTF-8 或带 BOM 的 UTF-16，英文逗号分隔，字段如下：

```csv
event_id,timestamp,station,equipment_id,glass_id,product,recipe,event,state
e1,2026-11-02T08:00:00+08:00,S1,S1-M1,G001,P1,R1,start,processing
e2,2026-11-02T08:00:10+08:00,S1,S1-M1,G001,P1,R1,end,processing
```

`event` 为 start/end。`state` 为 `processing/waiting/blocked/starved/transfer/down`。事件 ID 必须唯一，时间含时区，每条记录的工位、物理设备、玻璃、产品和配方必须明确。并行机要用不同 equipment_id；批处理和多轴同时动作不能伪装为同一串行设备。

质量失败包括缺字段、重复 ID、无时区、开始结束无法配对、逆序/非正时长、混产品/配方、同设备状态重叠和末站不存在。保留原始行号。现场还应独立核对设备时钟偏移、事件定义及完整性；基础检查通过不证明时钟已经校准。

## 统计口径

- 显式指定末站 `terminal_station`。统计窗口为 `[window_start,window_end)`，上边界事件不计产出。
- 未提供窗口时使用日志最早到最晚事件，并提示不能视为完整班次。完整配对区间才能进入 CT 分布。
- 完成数按末站处理结束的唯一 glass_id 统计。没有质量判定时称“完成数”，不称良品数。
- 平均 CT、P50/P95 线性插值按站计算。`3600 × 并行机数 / 平均CT` 是服务能力代理；没有稼动和物流证据时只能给瓶颈候选。
- 未指定并行机数时取日志出现设备数并提示未核实完整设备清单。可显式提供 `parallel={"S1":2}`。
- 状态时长为窗口内设备秒合计，允许多台设备同时贡献，不计算为整线互斥时间或 OEE。
- 待机、阻塞、缺料和停机须有对应状态记录；没有记录不能从处理 CT 凭空区分原因。

## SimPy 首版

支持串行路线、恒定处理时间、每站并行服务器、有限站间缓存、完工后阻塞及预热。投料队列在首站前，完成数、WIP 和阻塞/缺料设备秒分别返回。零容量缓存、批处理、重入、混产品、故障、质量和复杂搬送暂不支持；需实际路线扩展后评测。

```json
{
  "config": {
    "stations": [{"id":"S1","process_seconds":10,"parallel":1},{"id":"S2","process_seconds":20,"parallel":1}],
    "buffers": [1],
    "release_interval_seconds": 10,
    "duration_seconds": 3600,
    "warmup_seconds": 0
  },
  "scenario": {"stations":[{"id":"S1","process_seconds":10,"parallel":1},{"id":"S2","process_seconds":15,"parallel":1}]},
  "observed_completed": null,
  "tolerance": 0.1
}
```

仿真命令还须提供当前 `expected_revision` 及 `source_ids`。服务查找相同资料、相同输入版本且质量通过的 TT 分析，直接采用其完成数并绑定 `baseline_analysis_id`；手填完成数与日志不一致会拒绝。模型统计时长必须与该日志窗口一致。可显式选择分析 ID。

校准误差为 `abs(模型完成数-日志完成数)/日志完成数`。超过阈值不运行改善情景、不发布收益。通过只表示完成数这一项符合阈值，尚未证明 WIP、停机或所有动态行为已校准。模型预测、工程验证与实测效果分别保留。

合成标记从来源元数据继承，调用者不能用参数将已知合成资料改称现场数据。真实场景需补：工艺路线及站序、产品/配方、并行设备清单、状态定义、时钟依据、投料规则、缓存容量、质量与产出窗口。
