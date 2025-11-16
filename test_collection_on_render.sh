#!/bin/bash
# Test script to run collection and see actual errors
# Upload this to Render and run it manually

cd /app
python3 scripts/admin/collect_responses.py 15 --brand-id 5 --task-id 999
