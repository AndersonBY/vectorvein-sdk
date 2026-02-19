import os

if os.getenv("VECTORVEIN_RUN_LIVE_TESTS", "").strip().lower() not in {"1", "true", "yes", "on"}:
    collect_ignore_glob = ["live/test_*.py"]
