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

## 步骤 8：GitHub 提交与推送（完成）

- 已使用仓库本地 Git 身份 `anonymousguestme-ctrl` 创建提交。
- 首次项目提交：`f7502ce52fe719e015b0a61824e7ff98cc41a51a`，提交说明为
  `Build Codex approval traffic light`。
- 已通过普通 fast-forward 推送到 `origin/main`：`3f6222f..f7502ce`，未使用 force push。
- `git ls-remote` 已确认 GitHub `main` 指向 `f7502ce52fe719e015b0a61824e7ff98cc41a51a`。
- GitHub 仓库确认公开，默认分支为 `main`：
  `https://github.com/anonymousguestme-ctrl/Codex-Traffic-Light`。
- 用户硬件选择补充：Arduino IDE 应选择 `Arduino AVR Boards -> Arduino Uno`；ATmega328P
  不需要额外处理器选项，CH340 兼容版仍选择 Arduino Uno。

## 步骤 9：README 标题优化（完成）

- README 主标题由较抽象的 `Codex Traffic Light：为了少盯屏幕而做的实体审批信号灯`
  改为更直白的 `Codex 等待审批提醒灯｜Arduino 实体红绿灯`。
- 保留原有副标题，继续明确红灯、绿灯与黄灯各自代表的状态。
- 未修改 GitHub 仓库名和地址，避免已有链接失效。

## 步骤 10：改为监控 CMD/PowerShell Codex CLI（完成）

- 用户明确目标：读取 CMD 或 PowerShell 窗口中运行的 Codex CLI 审批状态。
- 复核发现旧版独立 app-server 查询不能保证取得另一个终端进程的实时审批态，因此旧方案已停用。
- 依据官方 Codex Hooks 文档，改用稳定的 `PermissionRequest` 生命周期事件；该事件只在 Codex
  准备真正请求审批时触发。
- 新增 `hook_state.py`：审批出现时写本地状态标记，`PostToolUse`、`Stop`、会话开始/结束等
  hook 负责清理标记。标记只含 session id、turn id、时间和事件名，不保存命令或会话正文。
- 新增 `install_hooks.py` 与 `install-hooks.ps1`：安全合并用户级 `~/.codex/hooks.json`，保留
  其他 hooks，已有文件会先备份，并支持 `-Uninstall`。
- 已在本机安装到 `C:\Users\anony\.codex\hooks.json`。当前运行中的 Codex CLI 需要完全退出并
  重新打开，首次加载时需审查并信任 hook 路径。
- 模拟 `PermissionRequest` 后 DryRun 输出 `RED`；模拟 `PostToolUse` 清理后输出 `GREEN`。
- Python 编译通过；状态测试 4 项、hook/安装器测试 3 项，合计 7 项全部通过。
- README 已改写为 CMD/PowerShell Codex CLI hook 架构和安装步骤。
- 当前硬件诊断只发现蓝牙 COM3/4/6/7，未发现 Arduino 或 CH340 串口；在系统识别开发板并
  持续运行 `start.ps1` 之前，Arduino 固件超时亮黄灯属于预期行为。

## 步骤 11：COM8 实物连接与后台监听（完成）

- 用户确认开发板与交通灯已连接，端口为 COM8。
- pyserial 已识别 `USB-SERIAL CH340 (COM8)`，硬件 ID 为 `VID:PID=1A86:7523`。
- 以 115200 baud 打开 COM8 并发送 `PING`，Arduino 正确返回
  `PONG CODEX_TRAFFIC_LIGHT_V1`，证明驱动、USB 数据链路和固件通信正常。
- 已创建本机忽略文件 `config.json`，固定 `serial_port` 为 `COM8`。
- 已在隐藏 PowerShell 中启动持续监听程序；启动器 PID 45888，Python 父子进程
  PID 55616/9196，COM8 由监听程序持续占用。
- 手动写入模拟审批标记后 DryRun 检测为 `RED`，持续 5 秒后清除标记，检测恢复为
  `GREEN`，待处理标记数量为 0。
- 当前 CMD 中已运行的 Codex 进程是在 hooks 安装前启动的；必须完全退出并重新运行
  `codex`，审查并信任 hook 后，真实审批事件才能驱动红灯。

## 步骤 12：CLI hook 修正版发布（完成）

- 已创建提交 `83a1241b07fa95433e14cd736456f17e7f6fb910`，提交说明为
  `Monitor terminal Codex approvals with hooks`。
- 提交包含官方 PermissionRequest hook 架构、安装/卸载器、7 项测试、COM 配置说明、
  约 813 行 README，以及旧 app-server 入口的删除。
- 已通过 fast-forward 推送到 GitHub `origin/main`，远端 main 已确认指向 `83a1241`。
- 本机 `config.json`、`.venv`、`runtime` 审批标记与监听日志均被忽略，未上传 GitHub。
## 2026-08-28：调整三色语义（进行中）

- 已确认用户要求的新语义：Codex 工作中亮绿灯、需要审批亮黄灯、完成本轮工作亮红灯。
- 已检查仓库状态和现有实现；当前旧版仍是“审批红、无审批绿、异常黄”，接下来将整体替换为会话三态状态机。
- 已实现会话三态：`UserPromptSubmit/PostToolUse → working → GREEN`、`PermissionRequest → approval → YELLOW`、`Stop/SessionStart → finished → RED`、`SessionEnd → 删除会话状态`。
- 已实现多会话优先级：审批（黄）高于工作（绿），全部完成或无会话时为红。
- 已把 Arduino 新版固件的启动状态与 15 秒心跳超时状态改为红灯。
- 已更新自动测试和 README 的主要状态说明；8 项测试全部通过。
- 已安装 Arduino CLI 1.5.1 到项目内忽略提交的 `tools/arduino-cli`，没有把运行工具散落到其他项目目录。
- 已重新安装用户级 Codex hooks，配置文件为 `C:\Users\anony\.codex\hooks.json`，原配置备份为 `hooks.json.backup-20260828-174623`。
- 已停止旧监听器，使用 `arduino:avr:uno` 编译固件并成功上传到 COM8；串口 `PING` 返回 `PONG CODEX_TRAFFIC_LIGHT_V1`。
- 已启动新版隐藏监听器（PowerShell PID 48924），并依次模拟验证 `working → GREEN`、`approval → YELLOW`、`finished → RED`；最终保留红灯状态。
- 注意：安装 hooks 前已经打开的 Codex CLI 进程需要完全退出并重新运行 `codex`，新生命周期 hooks 才能稳定接管真实会话。
