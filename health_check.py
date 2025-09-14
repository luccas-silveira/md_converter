#!/usr/bin/env python3
"""
Health check script para verificar se a aplicação está funcionando
"""

import requests
import sys
import time

def health_check():
    """Verifica se a aplicação está respondendo"""
    try:
        response = requests.get('http://localhost:5000/', timeout=10)
        if response.status_code == 200:
            print("✅ Application is healthy")
            return True
        else:
            print(f"❌ Application returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        if health_check():
            sys.exit(0)

        if attempt < max_retries - 1:
            print(f"Retrying in 5 seconds... (attempt {attempt + 1}/{max_retries})")
            time.sleep(5)

    print("❌ Health check failed after all retries")
    sys.exit(1)