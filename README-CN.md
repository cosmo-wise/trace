# Trace

<p align="center">
  用本地文件协议捕获事件、产物和日志，让 AI 开发链路留下可检查、可打包、可脱敏的运行证据。
</p>

<p align="center">

[![Python][python-shield]][python-url]
[![Version][version-shield]][version-url]
[![Protocol][protocol-shield]][protocol-url]
[![License][license-shield]][license-url]

</p>

<p align="center">
  <a href="#快速开始">快速开始</a> &middot;
  <a href="#安装">安装</a> &middot;
  <a href="#cli">CLI</a> &middot;
  <a href="#库使用">库使用</a> &middot;
  <a href="README.md">🇬🇧 English</a>
</p>

---

## 为什么需要 Trace

AI 驱动开发里的运行证据常常要么太重，要么太散。接数据库和追踪后端会把本地链路变复杂，只有零散日志又很难在多模块、多阶段之间回溯到底发生了什么。

Trace 选择最轻的路径：每次运行都是一个普通目录，事件写进 `timeline.jsonl`，产物登记到 `artifacts/index.json`，最终可检查、可验证、可打包、可脱敏分享。

如果你需要为 agent、CLI、验证器或生成流程保留结构化运行证据，Trace 适合放在执行链路内部持续记录。

如果你需要的是高吞吐在线 observability、实时 dashboard 或长期海量采集，这不是它的目标。

## 特性

- **零基础设施运行捕获**：没有数据库、队列或守护进程，每个 run 都是普通文件目录。
- **结构化时间线**：事件以 JSONL 顺序落盘，包含 module、phase、type、status 等字段。
- **产物登记与复制**：文件和目录可复制进 artifact registry，并保留角色、哈希与大小信息。
- **脱敏与打包**：支持 `redact` 去除本地路径和标识，再用 `bundle` 生成可分享归档。
- **摘要与审计导出**：支持人类可读的 inspect 输出，也支持单行 summary 和审计类导出。
- **可嵌入库接口**：CLI 和 Python 库共用同一协议，方便在本地脚本或上游模块里嵌入。

## 何时使用

| 场景 | 推荐命令 |
|------|------|
| 初始化一个 run 目录 | `trace start` |
| 记录事件、日志、产物 | `trace event` / `trace log` / `trace artifact` |
| 检查或收尾一次运行 | `trace inspect` / `trace finalize` / `trace validate` |
| 分享或归档证据 | `trace redact` / `trace bundle` |
| 给编排层输出摘要 | `trace export-summary` |

## 快速开始

```bash
python -m pip install -e .
python cli.py start --run-id demo --out trace-run
python cli.py event --run trace-run --module relay --phase query-plan --type phase_completed --message ok
python cli.py artifact --run trace-run --module relay --phase query-plan --path result.json --type json --role output
python cli.py finalize --run trace-run --status passed
python cli.py inspect --run trace-run
```

## 安装

```bash
python -m pip install -e .
```

需要 Python 3.11+。

## CLI

```bash
trace start --run-id demo --out trace-run [--label <label>] [--module <module>] [--json]
trace event --run trace-run --module relay --phase query-plan --type phase_completed --message ok [--json]
trace artifact --run trace-run --module relay --phase query-plan --path result.json --type json --role output [--json]
trace log --run trace-run --module relay --phase query-plan --file logs.txt [--json]
trace finalize --run trace-run --status passed [--validate] [--json]
trace inspect --run trace-run [--json]
trace validate --run trace-run [--strict] [--json]
trace redact --run trace-run --out trace-run-redacted [--json]
trace export-summary --run trace-run [--json]
trace bundle --run trace-run --out trace-run.tar.gz [--redact] [--json]
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

## 运行目录布局

```text
trace-run/
  run.json
  timeline.jsonl
  artifacts/index.json
  artifacts/<artifact-id>/payload/
  summary.json
  evidence.md
```

## 工作原理

Trace 将运行元数据、时间线事件和复制的产物写入具有稳定文件名的协议目录。这使得每次运行都可以用文本编辑器读取，用普通 CLI 工具编写脚本，并且无需服务后端即可传输。

`inspect` 和 `finalize` 摘要包含警告和错误计数，使编排层能够区分"协议完整"和"干净运行"。

## 开发

```bash
python -m pip install -e .[dev]
pytest
ruff check .
mypy src
```

## 贡献

欢迎贡献。请在 [GitHub](https://github.com/cosmo-wise/trace) 上提交 Issue 或 Pull Request。

## 许可

根据 Apache License, Version 2.0 许可。详见 [LICENSE](LICENSE)。

<!-- Badge reference links -->
[python-shield]: https://img.shields.io/badge/python-%3E%3D3.11-3776AB?logo=python&logoColor=white
[python-url]: https://www.python.org/
[version-shield]: https://img.shields.io/badge/version-0.1.0-2563EB
[version-url]: ./pyproject.toml
[protocol-shield]: https://img.shields.io/badge/storage-JSONL%20%2B%20artifacts-0F766E
[protocol-url]: ./src/trace_core
[license-shield]: https://img.shields.io/badge/license-Apache%202.0-1D4ED8
[license-url]: ./LICENSE
