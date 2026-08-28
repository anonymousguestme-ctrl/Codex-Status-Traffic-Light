# Codex Traffic Light — Handoff

> 本文件按步骤持续记录，便于中断后继续。按用户原要求使用文件名 `handoof.md`。

## 步骤 1：环境与硬件确认（完成）

- 日期：2026-08-28（Asia/Singapore）。
- 项目目标：Codex 等待用户审批/审查时亮红灯，其余时间亮绿灯。
- 开发板：Arduino Uno R3，ATmega328P。
- 信号灯模块：四针 `GRN / G / Y / R`；`GRN` 按模块地线（GND）处理。
- 接线：`GRN(GND) -> GND`、`G -> D8`、`Y -> D9`、`R -> D10`。
- 检查时 Windows 未发现串口设备，说明开发板当时未插入或尚未枚举。

## 步骤 2：Codex 状态检测方案（完成）

- 本机 Codex CLI 版本：`0.150.1`。
- 本机 app-server 协议的 `Thread.status.activeFlags` 明确包含
  `waitingOnApproval` 与 `waitingOnUserInput`。
- 采用本地只读 `thread/list` 轮询；不截屏、不读取会话正文、不修改 Codex 配置。
- 任一活动线程含 `waitingOnApproval` => 红灯；否则 => 绿灯。
- 串口或 Codex 状态连接异常 => 黄灯。

## 步骤 3：程序实现（完成）

- Arduino 固件实现 `GREEN / YELLOW / RED / OFF / PING` 串口协议，115200 baud。
- 固件带 15 秒电脑端心跳超时保护：程序断开后自动亮黄灯。
- Windows 监听程序实现串口自动识别、配置文件、Codex RPC 轮询和状态映射。
- Windows 使用独立 stdio app-server；未使用只支持已有 daemon 的 proxy 路径。
- `start.ps1` 首次运行在项目目录内创建 `.venv` 并安装 `pyserial`。

## 步骤 4：验证与交付（完成）

- Python 主程序语法编译通过。
- 三项状态映射单元测试全部通过：待审批红、空闲绿、普通用户输入可选。
- 与本机 Codex app-server 真实握手和 `thread/list` 查询通过；检测输出为 `GREEN`，退出码 0。
- 尚未完成的实物验证：上传固件、确认 COM 端口、实际观察红/绿/黄灯。验证时 Arduino 未连接。

## 步骤 5：目录迁移与清理（完成）

- 最终文件已从 `G:\codex-traffic-light` 路径直接完成三项单元测试与一次真实状态检测。
- G 盘实测结果：三项测试全部通过，Codex 当前状态输出 `GREEN`，退出码 0。
- 已永久删除 `C:\Users\anony\codex-traffic-light` 临时开发目录。
- 已永久删除 `C:\Users\anony\codex-traffic-light-schema` 临时协议目录。
- 所有交付程序、固件、说明和 handoff 现在只保留在 `G:\codex-traffic-light`。

## 步骤 6：GitHub 发布文档准备（完成）

- 目标仓库：`https://github.com/anonymousguestme-ctrl/Codex-Traffic-Light.git`。
- 远端检查结果：公开仓库，`main` 分支已有 1 个初始提交，包含 README 与 MIT LICENSE。
- README 已重写为 UTF-8 中文完整教程，共约 510 行。
- 文档明确说明项目目的就是少盯 Codex 窗口、方便“偷懒”。
- 已补充最终效果、工作原理、完整采购清单、针脚安全确认、接线、固件上传、
  DryRun、正式运行、配置、开机启动、测试、隐私、安全、限制与十二类故障排查。
- 已增加 `.gitignore`，排除 `.venv`、本机 `config.json`、Python 缓存及编辑器文件。
- 下一步：接入远端 Git 历史、保留 LICENSE、验证后提交并推送。

## 步骤 7：Git 接入与发布前验证（完成）

- 本地目录已初始化为 Git 仓库并连接 `origin`，未使用 force push。
- 已拉取并接入远端 `main` 的初始提交 `3f6222f`，MIT LICENSE 已保留。
- 从最终 G 盘路径重新执行 `start.ps1 -DryRun -Once`：成功安装隔离环境依赖，
  Codex 状态查询输出 `GREEN`，退出码 0。
- 两个 Python 文件通过 `py_compile`。
- 三项状态映射单元测试全部通过。
- `git diff --check` 通过；`.venv` 和 `__pycache__` 已确认被忽略。
- 已增加 `.gitattributes`，统一仓库文本换行规则。
- 当前机器未安装 `arduino-cli`，因此本轮无法执行命令行固件编译；README 已提供 Arduino IDE
  验证与上传步骤，实物板仍需连接后完成最终硬件验收。
- 下一步：检查暂存内容、创建提交并推送 `origin/main`。
