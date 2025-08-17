# el-price-alert

Fetches **tomorrow’s** day-ahead electricity prices (HvaKosterStrømmen API), converts to local time (Europe/Oslo), includes 25% VAT (optional), and tells you the cheap hours. Saves CSV/JSON.

- **Rule:** If any hour ≤ `threshold` (NOK/kWh incl. VAT) → list those hours and mark the 3 cheapest.  
  Else → list hours below the day’s median and still mark the 3 cheapest.  
  Always shows min/median/avg/max.
- **Grid tariff:** intentionally excluded.

## Quick start

```bash
git clone https://github.com/<your-username>/el-price-alert.git
cd el-price-alert

python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp config.example.json config.json
# edit config.json if you want (area, threshold, check_time)
python run_alert.py               # uses tomorrow by default
# or:
python run_alert.py --date=YYYY-MM-DD
```

## Scheduling

## Windows (Task Scheduler)

```powershell
# from repo root
.\scripts\setup_venv.ps1         # optional helper to keep venv outside sync folders
.\scripts\register_task.ps1      # uses check_time in config.json (default 15:00)
# remove later:
.\scripts\unregister_task.ps1
```

## macOS/Linux (cron)

```bash
0 15 * * * /usr/bin/env bash -lc 'cd <repo> && . .venv/bin/activate && python run_alert.py'
```

## Output

- CSV/JSON in `data/outputs/` (auto-created on first run).
- Optional desktop notification (Windows via `plyer` or PowerShell fallback).

## Config

`config.example.json` (copy to `config.json`):

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

## Notes

- Handles 24/25 hours on DST days.
- Prices come from HvaKosterStrømmen; times are converted to Europe/Oslo.