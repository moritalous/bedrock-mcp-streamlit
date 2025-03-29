import zoneinfo
from datetime import datetime, timezone

now_utc = datetime.now(timezone.utc)
tz = zoneinfo.ZoneInfo("Asia/Tokyo")
currentDateTime = now_utc.astimezone(tz)

SYSTEM_PROMPT = f"""
Speak in Japanese.
The current date is {currentDateTime}.
""".strip()
