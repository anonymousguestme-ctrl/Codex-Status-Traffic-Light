# Codex Status Traffic Light

**Language / 语言:** [English](README.en.md) | [中文](README.md)

> A physical Arduino traffic light for Codex CLI status. Green means working, yellow means human review is required, and red means finished, idle, or unable to read state.

## Why This Exists

Codex can work for several minutes and then pause while waiting for approval. This project puts that state on a desk-visible Arduino Uno traffic light, so you can leave the terminal without repeatedly checking the screen.

The device is intentionally simple: it is a notification light, not an approval mechanism. You still read every request and decide whether to allow or reject it.

## Status Mapping

| Codex state | Light | Meaning |
|---|---|---|
| `UserPromptSubmit`, `PostToolUse`, or `task_started` | Green | A session is actively working. |
| `PermissionRequest` or an approval/request rollout event | Yellow | At least one session is waiting for human review. |
| `Stop`, `SessionStart`, `task_complete`, or `turn_aborted` | Red | Work is complete, idle, or safely treated as finished. |

Approval has priority over working, and working has priority over finished. Multiple sessions are aggregated with the same priority.

## Supported Setup

- Windows 10/11
- Codex CLI 0.150.1 or later with lifecycle hooks enabled
- PowerShell or CMD, including local wrappers such as `codex-wenwen` and `codex-timi` when they delegate to `codex --profile wenwen` / `codex --profile timi`
- Arduino Uno R3 (ATmega328P)
- Four-pin traffic-light module (`GRN/GND`, `G`, `Y`, `R`)
- Python 3.9+ (Python 3.11 recommended)

The wrapper scripts, relay endpoints, and API keys for `codex-wenwen` and `codex-timi` are private local files and are not included in this repository.

## Hardware and Wiring

| Traffic-light pin | Arduino Uno pin | Purpose |
|---|---|---|
| `GRN` / `GND` | `GND` | Common ground |
| `G` | `D8` | Green LED |
| `Y` | `D9` | Yellow LED |
| `R` | `D10` | Red LED |

```text
Traffic-light module             Arduino Uno R3
GRN / GND  --------------------> GND
G          --------------------> D8
Y          --------------------> D9
R          --------------------> D10
```

Disconnect USB power before wiring. Confirm the common pin is really `GND`; never connect it to `5V`. Do not connect the module to `VIN`, `3.3V`, or analog pins. Check for loose Dupont wires and exposed solder joints before powering the board.

## Upload the Firmware

Firmware: `firmware/codex_traffic_light/codex_traffic_light.ino`

1. Connect the Uno with a USB data cable.
2. Open the sketch in Arduino IDE 2.x.
3. Select **Tools -> Board -> Arduino AVR Boards -> Arduino Uno**.
4. Select the new port under **Tools -> Port**.
5. Click Verify, then Upload.
6. The firmware starts with the red LED on. This is expected until the monitor reports a Codex state.

To test the board independently, open Serial Monitor at `115200` baud with newline enabled and send `GREEN`, `YELLOW`, `RED`, `OFF`, and `PING`. Expected responses are `OK GREEN`, `OK YELLOW`, `OK RED`, `OK OFF`, and `PONG CODEX_TRAFFIC_LIGHT_V1`. Close Serial Monitor before starting this project because both programs cannot own the same COM port. If the LEDs are inverted, change `ACTIVE_HIGH` in the sketch to `false` and upload again.

## Install Codex Hooks

From the project directory in PowerShell:

```powershell
.\install-hooks.ps1
```

The installer creates an isolated `.venv`, installs `pyserial`, safely merges the user-level `~/.codex/hooks.json`, preserves unrelated hooks, and writes an installation marker. Codex may ask you to review and trust the hook definition in `/hooks`; trust only the command that points to this repository's `src/hook_state.py`.

Restart all already-running Codex CLI sessions after installation. To remove only this project's handlers:

```powershell
.\install-hooks.ps1 -Uninstall
```

Hook markers are stored by default in `%USERPROFILE%\.codex\traffic-light\sessions`. This location is writable when Codex is running in a restricted workspace. Set `CODEX_TRAFFIC_LIGHT_STATE_DIR` in both environments if you need a different shared directory.

## Dry Run and Start

Close Arduino Serial Monitor, then test state detection without hardware:

```powershell
.\start.ps1 -DryRun -Once
```

Normal output is `Signal light: GREEN`, `YELLOW`, or `RED` (localized output is also possible). Start the physical monitor with:

```powershell
.\start.ps1
```

The process polls every 0.75 seconds, sends heartbeats to the Arduino, and returns the firmware to red on exit. `Ctrl+C` stops the foreground process. `start-background.ps1` starts a hidden background listener.

## Configuration

Copy the template when needed:

```powershell
Copy-Item .\config.example.json .\config.json
```

```json
{
  "serial_port": "auto",
  "baud_rate": 115200,
  "poll_interval_seconds": 0.75,
  "hook_state_dir": "auto",
  "hook_state_max_age_seconds": 7200,
  "codex_sessions_dir": "auto"
}
```

- `serial_port`: use `auto` for Arduino/CH340 detection, or set `COM8` explicitly.
- `baud_rate`: must match the firmware (`115200`).
- `poll_interval_seconds`: minimum enforced value is 0.2 seconds; 0.5-1.0 is sufficient.
- `hook_state_dir`: `auto` uses the shared Codex user directory described above.
- `hook_state_max_age_seconds`: stale markers are removed after this period; the default is two hours.
- `codex_sessions_dir`: `auto` follows `~/.codex/sessions` for rollout events created before hooks were installed.

## Verification

1. **Green:** launch `codex`, submit a task, and confirm `UserPromptSubmit` creates a green state.
2. **Yellow:** wait for a real approval request. The physical yellow LED should turn on within about one polling interval. Never approve an unsafe command just to test the light; use the documented simulation command if necessary.
3. **Red:** finish or abort the turn. `Stop`/`task_complete` should return the light to red.

Run the automated tests with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The suite covers state transitions, approval precedence, stale cleanup, transcript tracking, hook installation, and preservation of unrelated hooks.

## How It Works and Privacy

The monitor combines two local sources: lifecycle hooks for precise approval events and the Codex rollout files for task-start/task-complete events. It stores only session id, turn id, state, event name, and timestamps. It does not capture screenshots, OCR terminal text, read message content, upload transcripts, or call the OpenAI API.

If a hook cannot write its marker, the hook records a local diagnostic when possible and exits successfully so it cannot turn a successful Codex tool call into `PostToolUse hook (failed)`. The physical light falls back to red on monitor errors.

## Troubleshooting

1. **No COM port:** reconnect the USB data cable, install the CH340 driver if needed, and check Device Manager.
2. **Upload stuck:** select the correct Uno board and port, close Serial Monitor, and try another data cable.
3. **Monitor says no serial port:** set `serial_port` to the exact COM number in `config.json`.
4. **Several candidate ports:** set an explicit port instead of `auto`.
5. **Always yellow:** inspect `%USERPROFILE%\.codex\traffic-light\sessions` for stale `approval` JSON and remove it only after confirming the session is no longer waiting.
6. **Approval is not yellow:** run `/hooks`, review/trust the current hook hash, restart Codex, and confirm the hook command points to this checkout.
7. **`PostToolUse hook (failed)` or exit code 1:** update to this version. The hook is now fail-open; inspect `hook-errors.log` for the underlying local write/input error.
8. **Always red:** confirm the listener is running, hooks are installed, and the configured state directory is shared by Codex and the listener.
9. **Wrong colors:** verify `G -> D8`, `Y -> D9`, `R -> D10`, then check `ACTIVE_HIGH`.
10. **All LEDs on:** disconnect USB immediately and re-check the common ground and wiring.
11. **Python or pyserial missing:** run `start.ps1` once so the project `.venv` is created, or reinstall dependencies with `pip install -r requirements.txt`.
12. **Codex upgrade changed behavior:** check `/hooks`, review the new hook definition, restart Codex, and rerun the dry run. Hook schemas and event coverage can change between CLI releases.

## Autostart and Safety

After manual verification, create a Startup-folder shortcut for:

```text
powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "G:\codex-traffic-light\start.ps1"
```

Do not use a removable drive whose letter changes at boot. The traffic light never approves or rejects commands, bypasses Codex security, or replaces your review. Disconnect power before changing wiring. Keep API keys and relay configuration outside this repository.

## License

MIT. See [LICENSE](LICENSE).
