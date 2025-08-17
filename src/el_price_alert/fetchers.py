# src/el_price_alert/fetchers.py
from __future__ import annotations
import datetime as dt
import os
import requests
import certifi

def hks_url(area: str, day: dt.date) -> str:
    # https://www.hvakosterstrommen.no/api/v1/prices/YYYY/MM-DD_AREA.json
    return f"https://www.hvakosterstrommen.no/api/v1/prices/{day:%Y}/{day:%m-%d}_{area}.json"

def get_cert_path():
    """Get the best available certificate path for SSL verification."""
    # Check for corporate certificate first
    corporate_cert = os.environ.get('CORPORATE_CA_BUNDLE')
    if corporate_cert and os.path.isfile(corporate_cert):
        return corporate_cert
    
    # Check environment variables (set by PowerShell scripts)
    for env_var in ['SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE']:
        cert_path = os.environ.get(env_var)
        if cert_path and os.path.isfile(cert_path):
            return cert_path
    
    # Fall back to certifi's default
    try:
        return certifi.where()
    except Exception:
        # Last resort: use system default (True)
        return True

def fetch_hks(area: str, day: dt.date):
    url = hks_url(area, day)
    
    # Check if we should skip SSL verification (for environments with cert issues)
    skip_ssl = os.environ.get('SKIP_SSL_VERIFY', '').lower() in ('true', '1', 'yes')
    if skip_ssl:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        verify_setting = False
    else:
        verify_setting = get_cert_path()
    
    try:
        r = requests.get(url, timeout=20, verify=verify_setting)
        r.raise_for_status()
    except requests.exceptions.SSLError as e:
        if not skip_ssl:
            # Try different certificate approaches
            cert_options = [
                ("system default", True),
                ("certifi bundle", certifi.where()),
                ("no verification", False)
            ]
            
            for name, cert_option in cert_options:
                if cert_option == verify_setting:
                    continue  # Skip the one we already tried
                    
                try:
                    if cert_option is False:
                        import urllib3
                        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    r = requests.get(url, timeout=20, verify=cert_option)
                    r.raise_for_status()
                    break  # Success!
                except requests.exceptions.SSLError:
                    continue  # Try next option
            else:
                # All options failed
                raise requests.exceptions.SSLError(
                    f"SSL verification failed with all certificate options. "
                    f"This might be a certificate store issue. "
                    f"Try: 1) Update certificates with 'pip install --upgrade certifi' "
                    f"or 2) Set SKIP_SSL_VERIFY=true environment variable. "
                    f"Original error: {e}"
                ) from e
        else:
            raise
    
    data = r.json()
    if not isinstance(data, list) or len(data) not in (24, 25):
        raise ValueError(f"Unexpected HKS payload for {day}: {type(data)} len={len(data) if hasattr(data,'__len__') else 'n/a'}")
    
    # Normalize names: HKS uses fields: NOK_per_kWh, time_start, time_end
    rows = []
    for row in data: # keep 24 or 25 hours; downstream code tolerates both
        if not isinstance(row, dict):
            raise ValueError(f"Expected dict row but got {type(row)}: {row}")
        
        # Check for required fields first
        if "NOK_per_kWh" not in row or "time_start" not in row:
            raise ValueError(f"Missing required fields in row: {row}")
        
        # Convert price, handling potential None/invalid values
        try:
            price = float(row["NOK_per_kWh"])
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid NOK_per_kWh value '{row['NOK_per_kWh']}': {e}")
        
        # Check time_start
        t0 = row["time_start"]
        if not t0 or not isinstance(t0, str):
            raise ValueError(f"Invalid time_start value '{t0}' in row: {row}")
        
        rows.append({"NOK_per_kWh": price, "time_start": t0})
    
    return rows