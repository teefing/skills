# 说明
本阶段主要用于生成与展示单元测试生成结果。

## 执行阶段
### Report-A 失败时生成 FAILED_REASON
在执行 utree flush 之前，判断本次运行是否产生了有效的生成测试用例。如果没有生成有效用例，请总结FAILED_REASON，要求512个字符以内。
如果有生成有效的用例，FAILED_REASON留空。

### Report-B 执行 flush[强制要求]
flush 用于单测总结的本地落盘，必须执行。
```bash
FAILED_REASON="<computed_failed_reason_or_empty>" AGENT_SOURCE=<agent_name> MODEL_SOURCE=<model_name> SKILL_ROOT=${SKILL_ROOT} TMP_ROOT=${TMP_ROOT} \
$HOME/.local/bin/utree flush --repo-path ${PROJECT_ROOT}
```

### Report-C 总结生成结果报告内容：总结生成的用例、和发现的缺陷数据

#### 缺陷展示要求
- 展示缺陷时，建议包含缺陷等级，触发场景，缺陷描述，函数及源码位置，复现缺陷的单测代码位置，修复建议等内容。
- 所列缺陷的源码位置、复现单测位置都展示成可点击跳转到对应代码的链接的形式。

## 全局约束
- 不允许跳过 Report-B 中的 flush 指令。
- 禁止在总结中提示BUG_MAP等不容易给人理解的变量，如果未发现缺陷，则不需要提示缺陷相关内容。
- 当且仅当 `EXEC_SOURCE` 为 `flux` 或 `flux-web` 时，需要根据 `${SKILL_ROOT}/assets/templates/flux_report.md` 的要求来生成报告。其他情况不需要写文件。
- 当且仅当 `${EXEC_SOURCE}` 为 `PIPELINE` 时，需要根据 `${SKILL_ROOT}/assets/artifacts/defects.md` 中的要求写入缺陷文件。