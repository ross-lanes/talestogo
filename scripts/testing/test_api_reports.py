#!/usr/bin/env python3
"""Test the reports API endpoint to verify database connectivity."""

import requests
import json

# Test the health/info endpoint first
try:
    response = requests.get("http://localhost:8000/")
    print(f"API Root endpoint: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    print()
except Exception as e:
    print(f"Error connecting to API: {e}")
    exit(1)

# Test reports endpoint (this will require authentication)
# We'll just check if it responds with 401 or 403 (auth required) rather than 500 (server error)
try:
    response = requests.get("http://localhost:8000/reports/")
    print(f"Reports endpoint: {response.status_code}")

    if response.status_code == 401:
        print("✓ Server is responding correctly (authentication required)")
    elif response.status_code == 500:
        print("✗ Server error - database connection issue?")
        print(f"Response: {response.text}")
    else:
        print(f"Response status: {response.status_code}")

except Exception as e:
    print(f"Error: {e}")
