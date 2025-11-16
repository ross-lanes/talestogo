"""
Run manual collection for sl40@princeton.edu using the WORKING code path
This mimics exactly what the "Run Collection & Analysis" button does
"""
import os
import sys
import subprocess

# Set up environment
project_root = "/Users/rachelkremen/Documents/Code/tales_project"
os.environ['DATABASE_URL'] = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"

user_id = 15
brand_id = 5

print("="*80)
print("MANUAL COLLECTION FOR sl40@princeton.edu - Princeton Engineering")
print("Using the WORKING manual button code path")
print("="*80 + "\n")

# === RUN COLLECTION ===
script_path = os.path.join(project_root, "scripts", "admin", "collect_responses.py")
cmd = [
    "python3", script_path,
    str(user_id),
    "--brand-id", str(brand_id),
    "--task-id", "0"  # Dummy task ID for manual run
]

# Set PYTHONPATH like the manual button does
env = os.environ.copy()
env['PYTHONPATH'] = project_root

print(f"Running: {' '.join(cmd)}\n")
print("Starting collection process...\n")

# Run exactly like the manual button does
process = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env
)

# Send "1\n" to stdin like the manual button does
stdout, stderr = process.communicate(input="1\n", timeout=3600)

print("="*80)
print("COLLECTION OUTPUT:")
print("="*80)
print(stdout)
if stderr:
    print("\nSTDERR:")
    print(stderr)

if process.returncode != 0:
    print(f"\n❌ Collection failed with exit code {process.returncode}")
    sys.exit(1)

print("\n✅ Collection completed successfully!")
print("\n" + "="*80)
print("Now running analysis...")
print("="*80 + "\n")

# === RUN ANALYSIS ===
analysis_script = os.path.join(project_root, "analyze_responses.py")
analysis_cmd = [
    "python3", analysis_script,
    str(user_id),
    "--brand-id", str(brand_id),
    "--task-id", "0",
    "--auto-generate-report"
]

print(f"Running: {' '.join(analysis_cmd)}\n")

analysis_process = subprocess.Popen(
    analysis_cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env
)

# Send inputs for analysis
analysis_stdout, analysis_stderr = analysis_process.communicate(input="1\n1\n", timeout=3600)

print("="*80)
print("ANALYSIS OUTPUT:")
print("="*80)
print(analysis_stdout)
if analysis_stderr:
    print("\nSTDERR:")
    print(analysis_stderr)

if analysis_process.returncode != 0:
    print(f"\n❌ Analysis failed with exit code {analysis_process.returncode}")
    sys.exit(1)

print("\n" + "="*80)
print("✅ COMPLETE - Collection and analysis finished successfully!")
print("sl40@princeton.edu now has his data for today")
print("="*80)
