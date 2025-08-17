#!/usr/bin/env python3
# tests/test_ssl.py - Quick SSL connection test
import os
import sys
import requests
import certifi
from pathlib import Path

def test_ssl_connection():
    """Test SSL connection to hvakosterstrommen.no with different approaches."""
    test_url = "https://www.hvakosterstrommen.no/api/v1/prices/2025/08-17_NO1.json"
    
    print("SSL Connection Test")
    print("=" * 50)
    
    # Show environment
    print(f"Python version: {sys.version}")
    print(f"Requests version: {requests.__version__}")
    print(f"SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE', 'Not set')}")
    print(f"REQUESTS_CA_BUNDLE: {os.environ.get('REQUESTS_CA_BUNDLE', 'Not set')}")
    print(f"CURL_CA_BUNDLE: {os.environ.get('CURL_CA_BUNDLE', 'Not set')}")
    print(f"Certifi path: {certifi.where()}")
    print()
    
    # Test approaches
    approaches = [
        ("System default (verify=True)", True),
        ("Certifi bundle", certifi.where()),
        ("Environment SSL_CERT_FILE", os.environ.get('SSL_CERT_FILE')),
        ("Environment REQUESTS_CA_BUNDLE", os.environ.get('REQUESTS_CA_BUNDLE')),
        ("No verification (verify=False)", False),
    ]
    
    for name, verify_value in approaches:
        if verify_value is None:
            print(f"⏭️  Skipping {name}: Not available")
            continue
            
        print(f"🧪 Testing {name}...")
        try:
            response = requests.get(test_url, timeout=10, verify=verify_value)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS: Got {len(data)} price records")
            else:
                print(f"   ⚠️  HTTP {response.status_code}: {response.reason}")
        except requests.exceptions.SSLError as e:
            print(f"   ❌ SSL Error: {str(e).split('(')[0]}...")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request Error: {str(e).split('(')[0]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()
    
    print("💡 Recommendations:")
    print("   - If 'System default' works, remove SSL environment variables")
    print("   - If 'Certifi bundle' works, ensure certifi is properly installed")
    print("   - If only 'No verification' works, there may be a corporate firewall")

if __name__ == "__main__":
    test_ssl_connection()