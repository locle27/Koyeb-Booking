#!/usr/bin/env python3
"""
Simple test for dashboard fix
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def main():
    print("Testing Dashboard Fix...")
    
    try:
        from app import app
        print("SUCCESS: App import OK")
        
        with app.test_client() as client:
            response = client.get('/')
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("SUCCESS: Dashboard works!")
                return True
            else:
                print(f"ERROR: Status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
