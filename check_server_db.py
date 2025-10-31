#!/usr/bin/env python3
"""Check what database the current app instance would connect to."""

import os
from dotenv import load_dotenv

# Load .env file exactly like the app does
load_dotenv()

db_url = os.getenv("DATABASE_URL")
print(f"DATABASE_URL from .env: {db_url}")

if db_url and "localhost" in db_url:
    print("✓ Server should be using LOCAL PostgreSQL")
elif db_url and "render.com" in db_url:
    print("✗ Server is using RENDER PostgreSQL (production)")
else:
    print(f"? Unknown database URL pattern: {db_url}")
