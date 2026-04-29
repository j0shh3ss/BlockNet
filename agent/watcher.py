import re
import json
import time
import os
import asyncio
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_FILE = "config.json"

# Define regex patterns for different event types
PATTERNS = {
    "not_whitelisted": re.compile(
        r"Disconnecting\s+/(\d+\.\d+\.\d+\.\d+)(?::(\d+))?\s+([^\s]+).*\(You are not whitelisted\)"
    ),
    "failed_username": re.compile(
        r"Failed to verify username.*['\"]?(\w+)['\"]?"
    ),
}

# This pattern is used to extract the IP address from log lines, even if the line doesn't match the specific event patterns
IP_PATTERN = re.compile(r"/(\d+\.\d+\.\d+\.\d+):\d+")

# Load configuration from JSON file
def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception as e:
        print("❌ Failed to load config:", e)
        exit(1)

# Parse a log line and extract event data if it matches known patterns
def parse_line(line, server_id):
    time_match = re.match(r"\[(\d{2}:\d{2}:\d{2})\]", line)
    if not time_match:
        return None

    time_str = time_match.group(1)
    timestamp = datetime.now().strftime(f"%Y-%m-%dT{time_str}")

    ip_match = IP_PATTERN.search(line)
    ip = ip_match.group(1) if ip_match else None
    # Check each pattern to see if the line matches a known event
    for reason, pattern in PATTERNS.items():
        match = pattern.search(line)
        # If we have a match, extract the relevant data and return an event dict
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

# Safely write event to output file in JSONL format (one JSON object per line)
def write_event_sync(event, output_file):
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        with open(output_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        print(f"✅ Event written to {output_file}")  # Add confirmation
    except Exception as e:
        print(f"❌ Failed to write event to {output_file}: {e}")
        raise  # Re-raise so executor captures it
    

# Async wrapper for write_event_sync to be used in async contexts
async def save_event_async(event, output_file):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, write_event_sync, event, output_file)


class LogHandler(FileSystemEventHandler):
    # Initialize with file path, server ID, output file, and queue
    def __init__(self, path, server_id, output_file, queue, loop):
        self.path = os.path.abspath(path)
        self.server_id = server_id
        self.output_file = output_file
        self.queue = queue
        self.loop = loop

        self.file = open(self.path, "r")
        self.file.seek(0, 2)

        self.inode = os.fstat(self.file.fileno()).st_ino

    # Check if file was rotated and reopen if needed
    def _reopen_if_rotated(self):
        try:
            current_inode = os.stat(self.path).st_ino
            # If inode changed, file was rotated
            if current_inode != self.inode:
                print(f"🔄 Log rotated for {self.server_id}, reopening...")
                self.file.close()
                self.file = open(self.path, "r")
                self.inode = current_inode
        except FileNotFoundError:
            # File temporarily missing during rotation
            pass

    # Watchdog calls this on file modifications
    def on_modified(self, event):
        if os.path.abspath(event.src_path) != self.path:
            return
        # Check for log rotation
        self._reopen_if_rotated()
        # Read new lines and put them in the queue
        for line in self.file:
            self.loop.call_soon_threadsafe(
                self.queue.put_nowait,
                (line, self.server_id)
            )

# Worker task to process events from the queue
async def process_events(queue, output_file):
    while True:
        line, server_id = await queue.get()
    # Process the line and save event if found
        event = parse_line(line, server_id)
        if event:
            print("🚨", event)
            await save_event_async(event, output_file)

        queue.task_done()


async def async_main():
    config = load_config()
    output_file = config["output"]
    # Create an asyncio queue to communicate between file handlers and worker tasks
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    observer = Observer()
    handlers = []

    # Create log handlers based on config
    for log in config["logs"]:
        path = log["path"]
        server_id = log["server"]
    # Create log handler and schedule it
        try:
            handler = LogHandler(path, server_id, output_file, queue, loop)
            observer.schedule(handler, path=os.path.dirname(path), recursive=False)
            handlers.append(handler)

            print(f"✅ Watching {server_id} -> {path}")
        except Exception as e:
            print(f"❌ Failed to watch {path}:", e)
    # Check if we have any valid handlers
    if not handlers:
        print("❌ No valid log files to watch.")
        exit(1)

    print(f"👀 Watching {len(handlers)} log file(s)...")

    observer.start()
    # Start worker tasks to process events
    workers = [asyncio.create_task(process_events(queue, output_file)) for _ in range(4)]

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

    for w in workers:
        w.cancel()

# Entry point
def watch_logs():
    asyncio.run(async_main())


if __name__ == "__main__":
    watch_logs()
