#!/usr/bin/env python3
# run_alert.py
from __future__ import annotations
import os
import json, sys, time, datetime as dt, csv, logging
from pathlib import Path
from typing import Optional
from src.el_price_alert.fetchers import fetch_hks
from src.el_price_alert.logic import normalize_rows, daily_stats, select_hours
import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT/"config.json").read_text(encoding="utf-8"))

def setup_logging():
    """Set up logging to both file and Windows Event Log."""
    log_dir = ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('el_price_alert')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()  # Clear any existing handlers
    
    # File handler - rotating daily logs
    log_file = log_dir / f"el_price_alert_{dt.datetime.now():%Y%m%d}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler (for when run manually)
    if sys.stdout.isatty():  # Only add console handler if running interactively
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Windows Event Log handler
    try:
        import win32evtlog, win32evtlogutil, win32con
        class WindowsEventHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.app_name = "El Price Alert"
                
            def emit(self, record):
                try:
                    msg = self.format(record)
                    # Map Python logging levels to Windows event types
                    event_type = win32evtlog.EVENTLOG_INFORMATION_TYPE
                    if record.levelno >= logging.ERROR:
                        event_type = win32evtlog.EVENTLOG_ERROR_TYPE
                    elif record.levelno >= logging.WARNING:
                        event_type = win32evtlog.EVENTLOG_WARNING_TYPE
                    
                    win32evtlogutil.ReportEvent(
                        self.app_name, 1000 + record.levelno, 
                        eventType=event_type, strings=[msg]
                    )
                except:
                    pass  # Silently fail if Windows Event Log isn't available
        
        event_handler = WindowsEventHandler()
        logger.addHandler(event_handler)
    except ImportError:
        pass  # pywin32 not installed, skip Windows Event Log
    
    return logger

def send_windows_notification(title: str, message: str, logger=None):
    """Send a Windows toast notification."""
    success = False
    try:
        import plyer
        plyer.notification.notify(
            title=title,
            message=message,
            app_name="El Price Alert",
            timeout=15  # Increased timeout so it stays longer
        )
        success = True
    except ImportError:
        # Fallback: try using built-in Windows notifications
        try:
            import subprocess
            # Use PowerShell to show notification with longer timeout
            ps_script = f'''
            Add-Type -AssemblyName System.Windows.Forms
            $notification = New-Object System.Windows.Forms.NotifyIcon
            $notification.Icon = [System.Drawing.SystemIcons]::Information
            $notification.Visible = $true
            $notification.ShowBalloonTip(10000, "{title}", "{message}", [System.Windows.Forms.ToolTipIcon]::Info)
            Start-Sleep -Seconds 11
            $notification.Dispose()
            '''
            subprocess.run(["powershell", "-Command", ps_script], 
                         capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            success = True
        except:
            pass
    
    if logger:
        if success:
            logger.info(f"Notification sent: {title} - {message}")
        else:
            logger.warning(f"Failed to send notification: {title} - {message}")
    
    if not success:
        # If all else fails, just print (will go to log file if configured)
        print(f"NOTIFICATION: {title} - {message}")

def parse_cli_date(argv) -> Optional[dt.date]:
    for a in argv[1:]:
        if a.startswith("--date="):
            return dt.date.fromisoformat(a.split("=",1)[1])
    return None

def fetch_with_retries(area: str, day: dt.date, retries: int, wait_min: int):
    attempt = 0
    while True:
        attempt += 1
        try:
            return fetch_hks(area, day)
        except Exception as e:
            if attempt > max(1, retries):
                print(f"[el-price-alert] fetch failed after {attempt-1} retries: {e}", file=sys.stderr)
                sys.exit(2)  # scheduler or user will run again next time
            wait_sec = max(1, int(wait_min))*60
            print(f"[el-price-alert] not published yet or fetch error: {e} -> retry {attempt}/{retries} in {wait_sec//60} min")
            time.sleep(wait_sec)

def main(argv):
    logger = setup_logging()
    
    area        = CONFIG.get("area","NO1")
    include_vat = bool(CONFIG.get("include_vat", True))
    threshold   = float(CONFIG.get("threshold", 0.50))
    retries     = int(CONFIG.get("retries", 0))
    wait_min    = int(CONFIG.get("retry_interval_min", 30))
    notify      = bool(CONFIG.get("show_notifications", True))

    target_day = parse_cli_date(argv) or (dt.datetime.now().date() + dt.timedelta(days=1))
    
    logger.info(f"Starting el-price-alert for {target_day}, area {area}, threshold {threshold:.2f} kr/kWh")

    try:
        raw  = fetch_with_retries(area, target_day, retries=retries, wait_min=wait_min)
        rows = normalize_rows(raw, include_vat)
        prices = [r["price"] for r in rows]
        stats  = daily_stats(prices)
        hits, show, cheapest3 = select_hours(rows, threshold, stats["median"])

        def t(x): return x["t"].strftime("%H:%M")
        def p(x): return f"{t(x)} {x['price']:.2f} kr/kWh"

        header = f"Date: {target_day}  Area: {area}"
        title  = f"≤ {threshold:.2f} kr/kWh:" if hits else "Below median:"

        # Console output (only if running interactively)
        print(header)
        print(title, " | ".join(map(p, show)))
        print("Cheapest 3:", ", ".join(map(p, cheapest3)))
        print(f"Stats: min {stats['min']:.2f}  median {stats['median']:.2f}  avg {stats['avg']:.2f}  max {stats['max']:.2f}")

        # Log the results
        hits_text = " | ".join(map(p, show)) if show else "None"
        cheapest_text = ", ".join(map(p, cheapest3))
        
        logger.info(f"Results for {target_day}: {len(hits)} hours ≤ {threshold:.2f} kr/kWh")
        logger.info(f"Cheap hours: {hits_text}")
        logger.info(f"Cheapest 3: {cheapest_text}")
        logger.info(f"Price stats: min {stats['min']:.2f}, median {stats['median']:.2f}, avg {stats['avg']:.2f}, max {stats['max']:.2f}")

        # Windows notification
        if notify:
            if hits:
                cheap_times = ", ".join([t(r) for r in hits[:3]])  # Show max 3 times
                notification_msg = f"Cheap hours {target_day}: {cheap_times}"
                if len(hits) > 3:
                    notification_msg += f" (+{len(hits)-3} more)"
                logger.info(f"Found {len(hits)} cheap hours at or below {threshold:.2f} kr/kWh")
            else:
                cheapest_time = t(cheapest3[0])
                notification_msg = f"No hours ≤{threshold:.2f} kr. Cheapest: {cheapest_time} ({cheapest3[0]['price']:.2f} kr)"
                logger.warning(f"No hours found at or below {threshold:.2f} kr/kWh threshold")
            
            send_windows_notification("⚡ El Price Alert", notification_msg, logger)

        # Save files
        outdir = ROOT / "data" / "outputs"
        outdir.mkdir(parents=True, exist_ok=True)

        # CSV per day
        csv_path = outdir / f"{target_day}_{area}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["time","price_kr_per_kWh_incl_vat"])
            for r in rows:
                w.writerow([r["t"].strftime("%Y-%m-%d %H:%M"), f"{r['price']:.6f}"])

        # JSON summary
        summary = {
            "date": str(target_day), "area": area, "threshold": threshold,
            "min": stats["min"], "median": stats["median"], "avg": stats["avg"], "max": stats["max"],
            "hits": [{"time": t(r), "price": r["price"]} for r in hits],
            "cheapest3": [{"time": t(r), "price": r["price"]} for r in cheapest3]
        }
        (outdir / f"{target_day}_{area}_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        
        logger.info(f"Saved data files: {csv_path.name}, {target_day}_{area}_summary.json")
        logger.info("El-price-alert completed successfully")
        
    except Exception as e:
        logger.error(f"El-price-alert failed: {e}", exc_info=True)
        if notify:
            send_windows_notification("❌ El Price Alert Error", f"Failed to get prices: {str(e)[:100]}", logger)
        raise

if __name__ == "__main__":
    main(sys.argv)