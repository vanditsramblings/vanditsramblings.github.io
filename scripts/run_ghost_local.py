#!/usr/bin/env python3
import requests
import time
import sys
import os
import json

# Configuration from environment or defaults
GHOST_URL = os.getenv("GHOST_URL", "http://localhost:2368").rstrip('/')
ADMIN_NAME = os.getenv("GHOST_ADMIN_NAME", "Senior Intern")
ADMIN_EMAIL = os.getenv("GHOST_ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("GHOST_ADMIN_PASSWORD", "password123")
BLOG_TITLE = os.getenv("GHOST_BLOG_TITLE", "Senior Intern")
THEME_NAME = os.getenv("GHOST_THEME_NAME", "senior-intern")

def wait_for_ghost():
    """Wait for Ghost to start up and be ready for requests."""
    print(f"Waiting for Ghost at {GHOST_URL}...")
    max_retries = 120  # 2 minutes total
    for i in range(max_retries):
        try:
            # We check the setup endpoint specifically to see if it's reachable
            resp = requests.get(f"{GHOST_URL}/ghost/api/admin/setup/", timeout=2)
            if resp.status_code in [200, 403]: # 200 = setup needed, 403 = already setup
                print(f"Ghost is reachable (Status: {resp.status_code})")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if i % 5 == 0 and i > 0:
            print(f"Still waiting for Ghost... ({i*2}s elapsed)")
        time.sleep(2)
    
    print("Error: Ghost timed out and was never reachable.")
    return False

def check_setup_status():
    """Check if Ghost has already been configured with an owner account."""
    url = f"{GHOST_URL}/ghost/api/admin/setup/"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # If setup status is true, it means it's ALREADY set up
            # In some Ghost versions, it returns a list: {"setup": [{"status": false}]}
            setup_info = data.get("setup", [{}])[0]
            status = setup_info.get("status", False)
            return status
        elif resp.status_code == 403:
            # Ghost often returns 403 if setup is already complete
            return True
    except Exception as e:
        print(f"Warning: Could not check setup status: {e}")
    
    return False

def main():
    if not wait_for_ghost():
        sys.exit(1)

    print("Ghost is ready!")
    if not check_setup_status():
        print("\n[IMPORTANT] Ghost is NOT set up.")
        print("As per instructions.md (Snapshot Method):")
        print("1. Complete the setup at http://localhost:2368/ghost (create admin, select theme).")
        print("2. Export the SQL: docker exec ghost-local-db mysqldump -u ghost -pghostlocal ghost > ./init-db/seed.sql")
        print("3. Future starts will use seed.sql for automatic initialization.")
    else:
        print("Ghost is already set up and ready for use.")

if __name__ == "__main__":
    main()
