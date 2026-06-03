# DevTicket-Agent

面向研发工单归因的轻量 Agentic RAG 助手。

这个项目把一个研发工单处理流程拆成可解释的 Agentic workflow：工单分类、知识检索、工具调用、回答生成和离线评测。它不依赖外部大模型 API，先用纯 Python 实现核心链路，方便理解代码和准备面试；后续可以替换为 LangChain/LangGraph、向量库和真实 LLM。

## 项目亮点

- **Agentic RAG**：先判断工单类型，再检索历史工单/技术文档，最后结合工具结果生成建议。
- **Tool Calling**：模拟服务状态查询、错误码查询和日志查询，体现 Agent 调用外部工具的链路。
- **半真实工具层**：工具结果来自 `data/error_codes.json`、`data/service_status.json` 和 `data/mock_logs.json`，后续可替换成真实监控/日志 API。
- **Evaluation**：内置 10 条离线 case，评估分类、检索、工具调用和回答依据。
- **Trace Observability**：每次请求生成 `trace_id`，记录分类、检索、工具调用和生成阶段的耗时与关键 metadata。
- **Critic Guardrail**：基于分类、检索分数和工具调用结果做回答自检，判断是否需要升级人工。
- **SQLite Trace Store**：`/ask` 请求会保存 trace，可通过 `/traces` 和 `/traces/{trace_id}` 复盘。
- **Metrics & Cache**：提供 `/metrics` Prometheus 风格指标，并为轻量检索加入内存缓存。
- **Tests & CI**：补充 pytest 用例和 GitHub Actions workflow。
- **Interview-ready**：包含架构说明、简历 bullet 和面试追问答案。

## 快速运行

```bash
python3 -m devticket_agent.demo
python3 -m devticket_agent.failure_demo
python3 -m devticket_agent.eval_runner
```

如果要以 API 形式演示：

```bash
pip install -r requirements.txt
uvicorn devticket_agent.api:app --host 0.0.0.0 --port 8000
```

页面演示：

```text
http://127.0.0.1:8000/
```

请求示例：

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"订单创建接口最近总是 500，日志里有 DB_CONN_TIMEOUT，应该怎么排查？"}'
```

其他接口：

```bash
curl http://127.0.0.1:8000/traces
curl http://127.0.0.1:8000/metrics
```

测试：

```bash
pytest -q
```

## 目录结构

```text
devticket_agent/
  agent.py          # Agent 编排入口
  classifier.py     # 工单分类
  retriever.py      # 轻量检索
  tools.py          # 模拟工具调用
  critic.py         # 回答自检与升级人工判断
  generator.py      # 基于证据生成回答
  observability.py  # trace_id、阶段耗时和 metadata 记录
  storage.py        # SQLite trace 持久化
  metrics.py        # Prometheus 风格指标
  api.py            # FastAPI 服务入口
  eval_runner.py    # 离线评测
  demo.py           # 单条工单演示
  failure_demo.py   # 失败 case 与升级人工演示
tests/
  test_*.py
data/
  knowledge_base.json
  eval_cases.json
  error_codes.json
  service_status.json
  mock_logs.json
docs/
  interview_pack.md
  resume_project.md
```



## Baseline Run

本地最小路径、API 路径和 4G 云服务器方案见 [docs/baseline_run_plan.md](docs/baseline_run_plan.md)。
