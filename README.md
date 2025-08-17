# el-price-alert

Fetches tomorrow’s day-ahead electricity prices (HvaKosterStrømmen API), selects cheap hours, and saves CSV/JSON. Works on Windows/macOS/Linux.

- **Source:** HvaKosterStrømmen (area like `NO1`)
- **Rule:** If any hour ≤ `threshold` (NOK/kWh incl. VAT) → list those hours and mark 3 cheapest.  
  Else → list hours below the day’s median and mark 3 cheapest.  
  Always print min/median/avg/max.
- **Grid tariff is excluded** by design.

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
copy config.example.json config.json   # (Windows)
# or: cp config.example.json config.json

# Run for a specific date (optional):
python run_alert.py --date=YYYY-MM-DD
# Or just:
python run_alert.py  # (uses tomorrow)
