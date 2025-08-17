# src/el_price_alert/logic.py
from __future__ import annotations
import sys
import statistics
import datetime as dt

# Handle timezone compatibility: zoneinfo (Python 3.9+) or pytz fallback
if sys.version_info >= (3, 9):
    from zoneinfo import ZoneInfo
    def get_timezone(tz_name: str):
        return ZoneInfo(tz_name)
else:
    try:
        import pytz
        def get_timezone(tz_name: str):
            return pytz.timezone(tz_name)
    except ImportError:
        raise ImportError(
            "Python < 3.9 requires 'pytz' for timezone support. "
            "Install with: pip install pytz"
        )

def normalize_rows(raw: list[dict], include_vat: bool, tz_name="Europe/Oslo"):
    """
    Convert raw API data to normalized format with local timezone.
    
    Args:
        raw: List of dicts with 'NOK_per_kWh' and 'time_start' keys
        include_vat: If True, multiply prices by 1.25 (25% VAT)
        tz_name: Target timezone name (default: Europe/Oslo)
    
    Returns:
        List of dicts with 't' (datetime) and 'price' (float) keys, sorted by time
    """
    tz = get_timezone(tz_name)
    factor = 1.25 if include_vat else 1.0
    
    rows = []
    for r in raw:
        # Parse ISO datetime string to UTC, then convert to target timezone
        time_str = r["time_start"].replace("Z", "+00:00")
        try:
            utc_dt = dt.datetime.fromisoformat(time_str)
            local_dt = utc_dt.astimezone(tz)
        except ValueError as e:
            raise ValueError(f"Invalid time_start format '{r['time_start']}': {e}")
        
        price = round(r["NOK_per_kWh"] * factor, 6)
        rows.append({"t": local_dt, "price": price})
    
    rows.sort(key=lambda x: x["t"])
    return rows

def daily_stats(prices: list[float]) -> dict[str, float]:
    """Calculate min, median, average, and max from a list of prices."""
    if not prices:
        raise ValueError("Cannot calculate stats for empty price list")
    
    s = sorted(prices)
    return {
        "min": s[0], 
        "median": statistics.median(s), 
        "avg": sum(s) / len(s), 
        "max": s[-1]
    }

def select_hours(rows: list[dict], threshold: float, median: float) -> tuple[list, list, list]:
    """
    Select hours based on threshold and find cheapest options.
    
    Args:
        rows: List of dicts with 't' and 'price' keys
        threshold: Price threshold for "hit" hours
        median: Median price for fallback selection
    
    Returns:
        Tuple of (hits, show, cheapest3) where:
        - hits: Hours at or below threshold
        - show: Hours to display (hits if any, otherwise below median)
        - cheapest3: Three cheapest hours of the day
    """
    hits = [r for r in rows if r["price"] <= threshold]
    show = hits if hits else [r for r in rows if r["price"] < median]
    cheapest3 = sorted(rows, key=lambda r: r["price"])[:3]
    return hits, show, cheapest3