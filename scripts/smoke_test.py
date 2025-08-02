import datetime as dt
import os
import subprocess
import sys

DATE = os.getenv("TARGET_DATE", (dt.date.today() - dt.timedelta(days=1)).isoformat())

cmd = [
    "psql",
    "-h",
    "localhost",
    "-U",
    "tsadmin",
    "-d",
    "bikedb",
    "-v",
    f"env_target_date={DATE}",
    "-f",
    "sql/sanity_check.sql",
    "-t",
    "-A",  # rows only, no headers
]

rows = int(subprocess.check_output(cmd, text=True).strip())
print(f"sanity_check → {rows} rows joined for {DATE}")

if rows < 50000:
    sys.exit("❌ smoke test failed: too few rows")
