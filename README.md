# el-price-alert

⚡ Cross-platform Python tool that alerts you when Nordic electricity prices drop below your chosen threshold.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What it does
- Fetches **tomorrow’s** day-ahead electricity prices (via HvaKosterStrømmen API).
- Converts to local time (Europe/Oslo).
- Includes 25% VAT (configurable).
- Lists cheap hours and highlights the 3 cheapest.
- Always shows min/median/avg/max.
- Excludes grid tariff (by design).

Example output:
```
INFO: Starting el-price-alert for 2025-08-18, area NO1, threshold 0.40 kr/kWh  
Date: 2025-08-18 Area: NO1  
≤ 0.40 kr/kWh: 13:00 0.38 kr/kWh  
Cheapest 3: 13:00 0.38 kr/kWh, 14:00 0.46 kr/kWh, 12:00 0.71 kr/kWh  
Stats: min 0.38 median 1.49 avg 1.45 max 2.55  
INFO: Notification sent: ⚡ El Price Alert - Cheap hours 2025-08-18: 13:00

```

---

## Quick start

```bash
git clone https://github.com/kebman/el-price-alert.git
cd el-price-alert

python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp config.example.json config.json
python run_alert.py               # uses tomorrow by default
# or:
python run_alert.py --date=YYYY-MM-DD
```

---

## Scheduling

### Windows (Task Scheduler)

```powershell
# from repo root
.\scripts\setup_venv.ps1         # optional helper
.\scripts\register_task.ps1      # uses check_time in config.json (default 15:00)
# remove later:
.\scripts\unregister_task.ps1
```

### macOS/Linux (cron)

```bash
0 15 * * * /usr/bin/env bash -lc 'cd <repo> && . .venv/bin/activate && python run_alert.py'
```

---

## Config

Edit `config.json`:

```json
{
  "area": "NO1",
  "threshold": 0.40,
  "include_vat": true,
  "check_time": "15:00",
  "retries": 3,
  "retry_interval_min": 20,
  "show_notifications": true
}
```

---

## Output

- CSV/JSON in `data/outputs/` (auto-created).
- Optional desktop notification (Windows, macOS, Linux).

---

## License

MIT — see [LICENSE](LICENSE) file.