# Trace

<p align="center">
  本地文件证据捕获模块，专为 AI 驱动的开发工作流而设计
</p>

<p align="center">

[![Version][version-shield]][version-url]
[![License][license-shield]][license-url]
[![Python][python-shield]][python-url]
[![Build][build-shield]][build-url]

</p>

<p align="center">
  <a href="#快速开始">快速开始</a> &middot;
  <a href="#cli">CLI</a> &middot;
  <a href="#库使用">库使用</a> &middot;
  <a href="#布局">布局</a> &middot;
  <a href="#模式">模式</a> &middot;
  <a href="README.md">🇬🇧 English</a>
</p>

---

`trace` 是 Chariot 的本地文件证据捕获模块。其名称即 `trace`（无 `chariot-` 前缀），以普通文件方式存储运行记录，而非后端服务。

## 问题

AI 驱动的开发管线的可观测性通常要么太重（专用数据库、追踪后端、队列），要么太临时（分散的日志文件、缺少上下文、没有结构化检索）。当多个代理在不同阶段生成产物时，重构发生的事情需要拼接不一致的格式。

Trace 通过将事件、产物和日志捕获为一致布局的纯文件来解决这个问题——可用任何文本编辑器检查，可在运行之间组合，且足够轻量，适合本地 AI 代理工作流。

## 特性

- **零基础设施捕获** — 无需数据库、队列或守护进程。每次运行都是一个纯文件目录。
- **结构化时间线** — JSONL 事件流，每个步骤包含模块、阶段、类型和状态。
- **产物注册表** — 自描述的产物索引，具有内容可寻址的负载存储。
- **运行消毒** — `trace redact` 在共享前剥离本地路径和标识符。
- **静态可检查** — 任何文本编辑器、CLI 工具或 AI 代理都可以读取已完成的运行。
- **多详细级别** — 从紧凑的 `export-summary` 单行摘要到完整的证据包。

## 快速开始

```bash
# 启动新运行
python cli.py start --run-id demo --out trace-run

# 记录事件和产物
python cli.py event --run trace-run --module relay --phase query-plan --type phase_completed --message ok
python cli.py artifact --run trace-run --module relay --phase query-plan --path result.json --type json --role output

# 完成运行
python cli.py finalize --run trace-run --status passed

# 检查
python cli.py inspect --run trace-run
```

## 安装

```bash
pip install trace
```

需要 Python 3.11+。无运行时依赖。

## CLI

```bash
python cli.py start --run-id demo --out trace-run --json
python cli.py event --run trace-run --module relay --phase query-plan --type phase_completed --message ok --json
python cli.py artifact --run trace-run --module relay --phase query-plan --path result.json --type json --role output --json
python cli.py log --run trace-run --module relay --phase query-plan --level warning --message "rate limit approaching" --json
python cli.py finalize --run trace-run --status passed --json
python cli.py inspect --run trace-run --json
python cli.py doctor --json
python cli.py validate --run trace-run --json
python cli.py redact --run trace-run --out trace-run-redacted --json
python cli.py export-summary --run trace-run --json
python cli.py bundle --run trace-run --out trace-run-bundle --json
```

- `log` 记录警告/错误消息，无需结构化产物载荷。
- `validate` 检查运行目录的一致性和必需文件的存在性。
- `redact` 复制运行目录，剥离本地路径和标识元数据。
- `export-summary` 打印适用于编排的紧凑单行摘要。
- `bundle` 将运行目录打包为自包含存档。

## 布局

```text
trace-run/
  run.json
  timeline.jsonl
  artifacts/index.json
  artifacts/<artifact-id>/payload/<复制的文件>
  summary.json
  evidence.md
```

## 库使用

```python
from pathlib import Path
from trace_core import TraceRun

trace = TraceRun.start("demo", Path("trace-run"))
trace.record_event("relay", "query-plan", "phase_completed", "ok", "planned queries")
trace.copy_artifact("relay", "query-plan", Path("result.json"), "json", "output")
trace.finalize("passed")
```

生产者适配器也可以直接编写记录的 JSONL/清单协议。Python 生产者应使用可选导入或子进程边界，默认保持非严格状态；Harness 和 Trial 使用经 `trace inspect` 验证的 TypeScript 原生协议写入器。

`trace inspect` 和 `trace finalize` 摘要包含 `warning_count`、`error_count` 以及采样的 `warnings` / `errors`。这使完整协议文件的运行区别于真正干净地运行；编排层可以在产品质量需要时将警告升级为硬性门禁。

Python 生产者副本的 `trace_capture.py` 通过 `python3 tools/chariot/sync/sync_trace_capture.py --check` 或 `--write` 从 Chariot 工作空间模板同步。这使 Relay、Scout、Course 和 Scribe 在运行时独立于兄弟 `trace` 仓库，同时避免辅助工具漂移。

## 架构

```
trace/
├── cli.py                 # CLI 入口
├── src/
│   ├── trace_core.py      # 核心 TraceRun 库
│   ├── commands/          # CLI 命令实现
│   └── schemas/           # 协议模式
├── schemas/               # JSON 模式（artifact-index、timeline、summary、manifest）
└── probe/                 # 测试资产
```

## 模式

Trace 定义版本化的 JSON 模式以强制执行协议一致性：

| 模式 | 描述 |
| --- | --- |
| `trace-manifest-1.0.json` | 顶级运行清单 |
| `timeline-1.0.json` | 时间线事件条目 |
| `artifact-index-1.0.json` | 产物注册表索引 |
| `summary-1.0.json` | 运行摘要 |
| `evidence-bundle-1.0.json` | 证据包格式 |

## 原理

**为何使用纯文件？**

- **零基础设施** — 无需数据库、无需队列、无需守护进程。
- **可检查性** — 任何文本编辑器或 CLI 都可以读取运行。
- **可消毒性** — `redact` 在共享前剥离路径和标识符。
- **可重播性** — 时间线适合 AI 驱动的重放分析和调试。
- **可组合性** — 多个运行可以合并、比较或馈送到审核工具。

## 贡献

欢迎贡献。请在 [GitHub](https://github.com/cosmo-wise/trace) 上提交 Issue 或 Pull Request。

## 许可

根据 Apache License, Version 2.0 许可。详见 [LICENSE](LICENSE)。

<!-- Badge reference links -->
[version-shield]: https://img.shields.io/badge/version-0.1.0-blue
[version-url]: https://github.com/cosmo-wise/trace/releases
[license-shield]: https://img.shields.io/badge/license-Apache%202.0-blue
[license-url]: https://github.com/cosmo-wise/trace/blob/main/LICENSE
[python-shield]: https://img.shields.io/badge/python-%3E%3D3.11-3776AB?logo=python
[python-url]: https://python.org
[build-shield]: https://img.shields.io/badge/build-passing-brightgreen
[build-url]: #
