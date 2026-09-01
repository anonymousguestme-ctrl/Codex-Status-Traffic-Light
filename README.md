<div align=center>

# 🚦 Codex Status Traffic Light

### 为了不用一直盯着 Codex 终端，我做了一个 Arduino 实体状态交通灯

Codex 工作时亮绿灯，需要人工审批时亮黄灯，完成或空闲时亮红灯。

[English](./README.en.md)　|　中文

</div>

---

## ✨ 为什么做它

Codex 经常会连续工作几分钟，然后停下来等待审批或返回结果。如果一直盯着 CMD 或 PowerShell，时间很容易被切碎；切到别的窗口后，又可能错过审批提示。

这个项目把 Codex CLI 的状态变成桌面上的实体交通灯：

- 🟢 **绿灯：Codex 正在工作。** 可以继续做别的事。
- 🟡 **黄灯：Codex 正在等你。** 回到终端阅读并决定是否批准。
- 🔴 **红灯：Codex 已完成或空闲。** 可以回来查看结果。

它不会替你点击批准，也不会降低 Codex 的安全限制，只把本机状态转换成一个远处也能看到的颜色。

GitHub：<https://github.com/anonymousguestme-ctrl/Codex-Status-Traffic-Light>

## 🚥 状态说明

| Codex 状态 | 灯色 | 含义 |
| --- | --- | --- |
| 任意会话正在处理任务 | 🟢 绿灯 | Codex 正在工作 |
| 任意会话触发 `PermissionRequest` | 🟡 黄灯 | 等待人工审查或批准 |
| 所有会话已完成、尚未开始或监听异常 | 🔴 红灯 | 查看结果或检查监听器 |

多终端同时运行时，优先级为：

```text
等待审批（黄） > 正在工作（绿） > 完成或空闲（红）
```

Arduino 超过 15 秒没有收到电脑心跳时会自动回到红灯，避免监听程序退出后一直显示旧状态。

## 它是怎么工作的？

```text
Codex hooks / 本地 rollout 生命周期
                │
                ▼
      Windows Python 监听程序
                │ USB 串口 115200 baud
                ▼
          Arduino Uno R3
                │
                ▼
        三色交通灯模块 G/Y/R
```

监听程序优先使用 Codex 生命周期 hooks，并用本地 rollout 中的 `task_started`、`task_complete` 和 `turn_aborted` 事件补充判断，约每 0.75 秒刷新一次。

## 📦 需要准备什么

| 数量 | 名称 | 搜索关键词 | 用途 |
| ---: | --- | --- | --- |
| 1 | Arduino Uno R3 | `Arduino Uno R3 ATmega328P` | 接收状态并控制灯 |
| 1 | 四针三色交通灯模块 | `Arduino 交通灯模块 GND G Y R` | 显示三种状态 |
| 4 | 母对母杜邦线 | `2.54mm 母对母杜邦线` | 连接模块和 Uno |
| 1 | USB 数据线 | USB-A 转 USB-B | 供电、固件上传和串口通信 |
| 1 | Windows 电脑 | Windows 10/11 | 运行 Codex CLI 和监听器 |

软件需要 Python 3、Arduino IDE 2.x、Codex CLI 和 Windows PowerShell。桌面底座、立柱、遮光罩和 USB 延长线均为可选配件。

## ⚡ 快速开始

### 1. 下载项目

```powershell
git clone https://github.com/anonymousguestme-ctrl/Codex-Status-Traffic-Light.git
cd Codex-Status-Traffic-Light
```

### 2. 断电接线

| 交通灯模块 | Arduino Uno R3 | 固件定义 |
| --- | --- | --- |
| `GRN` 或 `GND` | `GND` | 公共地 |
| `G` | `D8` | 绿灯 |
| `Y` | `D9` | 黄灯 |
| `R` | `D10` | 红灯 |

### 3. 上传固件

用 Arduino IDE 打开：

```text
firmware/codex_traffic_light/codex_traffic_light.ino
```

选择 **Arduino AVR Boards → Arduino Uno** 和对应 COM 端口，然后上传。启动后默认亮红灯，这是正常的空闲状态。

### 4. 安装 Codex hooks

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install-hooks.ps1
```

安装器会创建 `.venv`、安装 `pyserial`、合并用户级 `~/.codex/hooks.json`、保留其他 hooks，并在修改前创建备份。

安装后请**完全退出所有 Codex CLI，再重新启动**。已经打开的进程不会热加载新 hooks。

### 5. 测试并运行

```powershell
.\start.ps1 -DryRun -Once   # 只检查状态
.\start.ps1                 # 前台持续运行
.\start-background.ps1      # 隐藏后台运行
```

## 🔌 硬件接线

```text
交通灯模块                     Arduino Uno R3
┌──────────┐                  ┌──────────────┐
│ GRN/GND  ├─────────────────►│ GND          │
│ G        ├─────────────────►│ D8           │
│ Y        ├─────────────────►│ D9           │
│ R        ├─────────────────►│ D10          │
└──────────┘                  └──────────────┘
```

> [!CAUTION]
> 某些模块把公共针标成 `GRN`，这里通常表示 Ground，而不是 Green。必须确认模块是公共地版本，不能在不确定时把公共针接到 5V。

常见成品模块自带限流电阻，但不同厂商可能不同。若模块没有电阻，不要直接连接 LED。

### 串口监视器测试

将波特率设为 `115200`、行尾设为“新行”，可以发送：

```text
GREEN
YELLOW
RED
OFF
PING
```

`PING` 应返回 `PONG CODEX_TRAFFIC_LIGHT_V1`。测试后关闭串口监视器，因为 Arduino IDE 和监听器不能同时占用同一个 COM 端口。

## ⚙️ 配置

```powershell
Copy-Item .\config.example.json .\config.json
```

```json
{
  serial_port: auto,
  baud_rate: 115200,
  poll_interval_seconds: 0.75,
  hook_state_dir: auto,
  hook_state_max_age_seconds: 7200,
  codex_sessions_dir: auto
}
```

| 字段 | 说明 |
| --- | --- |
| `serial_port` | 自动识别 Arduino/CH340，或填写 `COM8` 等固定端口 |
| `baud_rate` | 必须与固件一致，默认 `115200` |
| `poll_interval_seconds` | 状态刷新间隔，默认 `0.75` 秒 |
| `hook_state_dir` | `auto` 使用 `~/.codex/traffic-light/sessions` |
| `hook_state_max_age_seconds` | 异常退出后状态失效时间，默认两小时 |
| `codex_sessions_dir` | Codex rollout 目录，通常保持 `auto` |

`config.json` 已被 `.gitignore` 排除，不会上传本机 COM 端口配置。

## 🧪 验证三种状态

### 绿灯：工作中

启动监听器后，在 Codex CLI 中发送任务。收到新任务并开始处理后，应在约一秒内变绿。

### 黄灯：等待审批

Codex 出现审批界面并触发 `PermissionRequest` 时，应变黄。交通灯只负责提醒，不代表请求安全；请先阅读命令、路径和理由，再决定是否批准。

### 红灯：完成或空闲

本轮回复结束并触发 `Stop` 或 `task_complete` 后，应变红。监听器退出、状态读取失败或 Arduino 超过 15 秒收不到心跳时，也会保守地显示红灯。

## 🖥️ 开机自动运行

让 Windows 任务计划程序在登录时运行：

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 完整路径\start-background.ps1
```

“起始于”填写项目目录。移动项目后，应重新运行 `install-hooks.ps1`。

## 🔐 数据与隐私

- hook 状态默认保存在 `%USERPROFILE%\.codex\traffic-light\sessions`；
- 状态文件只记录会话 ID、轮次 ID、状态、事件名和更新时间；
- 不把提示词、命令正文、审批理由或回答内容写入交通灯状态文件；
- rollout 补充检测只用于识别生命周期事件及时间；
- 不上传会话内容，不连接项目作者的服务器；
- 不会自动批准、拒绝或执行任何请求。

卸载 hooks：

```powershell
.\install-hooks.ps1 -Uninstall
```

## 📁 项目结构

```text
firmware/codex_traffic_light/   Arduino Uno 固件
src/codex_traffic_light.py      状态监听与串口控制
src/hook_state.py               Codex 生命周期状态写入器
src/install_hooks.py            hooks 安装、合并与卸载
tests/                          自动化测试
config.example.json             配置模板
install-hooks.ps1               hooks 安装入口
start.ps1                       前台启动入口
start-background.ps1            隐藏后台启动入口
README.en.md                    English guide
LICENSE                         MIT License
```

## ✅ 开发检查

```powershell
.\.venv\Scripts\python.exe -m py_compile .\src\*.py
.\.venv\Scripts\python.exe -m unittest discover -s .\tests -v
```

## 🛠️ 故障排查

### 一直亮绿灯

运行 `.\start.ps1 -DryRun -Once`。多会话模式下，只要任意 Codex 会话仍是 `working`，就会保持绿色。若所有任务都结束，完全退出旧 Codex 进程并重新打开。

### 一直亮黄灯

至少有一个会话仍记录为等待审批。检查所有 Codex 终端；进程异常退出留下的旧状态默认两小时后失效。

### 一直亮红灯

- 确认已运行 `.\install-hooks.ps1`；
- 安装后完全退出并重启 Codex CLI；
- 用 `.\start.ps1 -DryRun -Once` 检查软件状态；
- 检查监听器是否仍在运行。

### 找不到 Arduino 或 COM 端口

- 换一根确认支持数据传输的 USB 线；
- 在设备管理器中查找 Arduino 或 `USB-SERIAL CH340`；
- 关闭 Arduino IDE 串口监视器和其他串口助手；
- 在 `config.json` 中固定实际端口，例如 `COM8`。

### 红、黄、绿对应错误

先核对 `G → D8`、`Y → D9`、`R → D10`。如果亮灭逻辑整体相反，把固件中的：

```cpp
const bool ACTIVE_HIGH = true;
```

改成 `false`，然后重新上传固件。

### 出现 hook timeout 或 hook failed

当前安装器使用 Codex 支持的 3 秒超时，状态 hook 会返回合法 JSON `{}`。更新项目后重新运行 `.\install-hooks.ps1`，再完全退出并重启 Codex CLI。

## 当前限制

- 目前面向 Windows、Codex CLI 和 Arduino Uno R3；
- Codex hooks 或 rollout 格式未来可能变化；
- 多个会话共用一盏灯，只显示最高优先级状态；
- 红灯同时表示“完成/空闲”和“异常时的保守状态”；
- 不同厂商模块的针脚、电平和限流设计可能不同；
- 这是低压 Arduino LED 项目，不能直接控制市电交通灯。

## 可以继续怎么改？

- 给灯模块增加桌面立柱和稳定底座；
- 增加遮光罩，让颜色在明亮环境中更清楚；
- 增加蜂鸣器或静音按钮；
- 改用 ESP32，支持无线状态灯；
- 为不同 Codex 会话分配独立灯组。

## License

本项目使用 [MIT License](./LICENSE)。
