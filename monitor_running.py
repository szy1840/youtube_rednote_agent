# is_videolingo_running.py
# Returns True if *any* python.exe is currently executing
# `-m batch.utils.batch_processor`, else False.

import psutil, re

PATTERN = re.compile(r"batch\.utils\.batch_processor")   # literal dot must be escaped

def videolingo_running() -> bool:
    """Return True if the VideoLingo batch job is alive."""
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            if proc.info["name"].lower() != "python.exe":
                continue
            if any(PATTERN.search(arg) for arg in proc.info["cmdline"]):
                return True          # found one, no need to keep looking
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue                 # process ended between iteration steps
    return False

if __name__ == "__main__":
    print("Running!" if videolingo_running() else "Not running.")
