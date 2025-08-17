# Scheduling

## Windows (Task Scheduler)

```powershell
# from repo root
.\scripts\register_task.ps1          # defaults to 15:00 unless you edit config.json -> check_time
# remove later:
.\scripts\unregister_task.ps1
```

### macOS/Linux (cron)

```bash
0 15 * * * /usr/bin/env bash -lc 'cd <repo> && . .venv/bin/activate && python run_alert.py'
```

## Output

- CSV/JSON in `data/outputs/` (created on first run).

Optional desktop notification (Windows via `plyer` or PowerShell fallback).

## Config Example

`config.json`:

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

- Prices are converted to local time (Europe/Oslo) and include 25% VAT when include_vat=true.
- Handles 24/25 hours on DST days.
- Grid tariff is intentionally excluded.