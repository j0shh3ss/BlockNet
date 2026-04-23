import re
import json
import time
from datetime import datetime

#Note to self: put patterns in config so user can add/customize

CONFIG_FILE = "config.json"

PATTERNS = {
    "not_whitelisted": re.compile(
        r"Disconnecting\s+/(\d+\.\d+\.\d+\.\d+)(?::(\d+))?\s+([^\s]+).*\(You are not whitelisted\)"
    ),
    "failed_username": re.compile(
        r"Failed to verify username.*['\"]?(\w+)['\"]?"
    ),
}

IP_PATTERN = re.compile(r"/(\d+\.\d+\.\d+\.\d+):\d+")


def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception as e:
        print("❌ Failed to load config:", e)
        exit(1)


def parse_line(line, server_id):
    time_match = re.match(r"\[(\d{2}:\d{2}:\d{2})\]", line)
    if not time_match:
        return None

    time_str = time_match.group(1)
    timestamp = datetime.now().strftime(f"%Y-%m-%dT{time_str}")

    ip_match = IP_PATTERN.search(line)
    ip = ip_match.group(1) if ip_match else None

    for reason, pattern in PATTERNS.items():
        match = pattern.search(line)
        if match:
            port = match.group(2) if match.groups() else "UNKNOWN"
            username = match.group(3) if match.groups() else "UNKNOWN"

            return {
                "timestamp": timestamp,
                "server": server_id,
                "username": username,
                "ip": ip,
                "port": port,
                "reason": reason
            }

    return None


def save_event(event, output_file):
    try:
        with open(output_file, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        print("❌ Failed to write event:", e)


def watch_logs():
    config = load_config()
    output_file = config["output"]

    files = []

    for log in config["logs"]:
        try:
            f = open(log["path"], "r")
            f.seek(0, 2)
            files.append((f, log["server"]))
            print(f"✅ Watching {log['server']} -> {log['path']}")
        except Exception as e:
            print(f"❌ Failed to open {log['path']}:", e)

    if not files:
        print("❌ No valid log files to watch.")
        exit(1)

    print(f"👀 Watching {len(files)} log file(s)...")

    while True:
        for f, server_id in files:
            line = f.readline()

            if not line:
                continue

            event = parse_line(line, server_id)

            if event:
                print("🚨", event)
                save_event(event, output_file)

        time.sleep(0.05)


if __name__ == "__main__":
    watch_logs()
