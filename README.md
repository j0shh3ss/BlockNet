# BlockNet
A Python daemon that monitors server logs to detect and record unauthorized join attempts. By exporting this data in JSONL format, it builds a centralized log to help you analyze connection locations and identify malicious IPs that require broader network-level blocking.

Currently there is no installer file due to possible user config editing (to add additional ignored/whitelisted players) so manual installation instructions listed below, assuming Ubuntu OS. Use AI to convert to whatever OS you are using.

## INSTALLER INSTRUCTIONS

### List of dependencies:
>Python3 (Normally pre-installed, can verify with python3 --version)\
>WatchDog

### Install dependencies (assuming Ubuntu)
```
sudo apt install python3
sudo apt install python3-watchdog
```
---
## Step 1: 📦 Installing BlockNet
Click:
**Code → Download ZIP**

Or clone:
```
git clone https://github.com/j0shh3ss/BlockNet.git
cd BlockNet
cd agent
```
Or web link: https://github.com/j0shh3ss/BlockNet/releases/latest
```
wget https://github.com/j0shh3ss/BlockNet/archive/refs/tags/v1.0.tar.gz
```
---
## Step 2: ⚙️ Modifications
DIR = BlockNet/agent
```
cd BlockNet
cd agent
nano config.json
```
Please edit this file accordingly. Here is example:
```
{
  "output": "events.jsonl",
  "ignore_usernames": ["j0ssh3ss", "usr2"],
  "logs": [
    {
      "path": "/mnt/server/minecraft/world/logs/latest.log",
      "server": "world"
    }, # must add comma for additional logs
    {
      "path": "/mnt/server/minecraft/other_world/logs/latest.log",
      "server": "other_world"
    } # I would add a comma here if I was gonna add a third log to monitor, since this is the last log to monitor, no comma.
  ]
}
```
>In this example, I have added "j0ssh3ss" and usr2 as "ignored_usernames" these are users that will be ignored in event logging.\
>In the "logs" section, you must direct the path to the designated path of your worlds latest.log file.\
>You can keep adding more files to log as shown in other_world. Just add a comma "," after closing the bracket "}".\
>You can also edit the "output" location by editing events.jsonl to be say /var/log/mc_watcher/events.jsonl but you must ensure write privledges match the user that will make the daemon service. For ease of use, I recommend keeping it in this folder.

---
## Step 3: 🧪 Testing
After modifications have been made, please run a test script. You will need 2 shells open in order to run this test.\
**Shell 1:**
```
python3 watcher.py
```
**Shell 2:** *NOTE* Please change the ending of these test scripts to match the directory of the log you want to test, enter one at a time for ease
```
echo "[12:01:33] [Server thread/INFO]: Disconnecting /1.2.3.4:4525 Player123 (You are not whitelisted)" >> /mnt/server/minecraft/world/logs/latest.log
echo "[12:01:33] [Server thread/INFO]: Disconnecting /1.2.3.4 Player123 (You are not whitelisted)" >> /mnt/server/minecraft/world/logs/latest.log
echo "[14:44:22] [Server thread/INFO]: Player123 (/1.2.3.4:38328) lost connection: Disconnected" >> /mnt/server/minecraft/world/logs/latest.log
```
If you get these results, you pass ✅
```
🚨 {'timestamp': '2026-04-30T12:01:33', 'server': 'world', 'username': 'Player123', 'ip': '1.2.3.4', 'port': '4525', 'reason': 'not_whitelisted'}
✅ Event written to events.jsonl
🚨 {'timestamp': '2026-04-30T12:01:33', 'server': 'world', 'username': 'Player123', 'ip': '1.2.3.4', 'port': None, 'reason': 'not_whitelisted'}
✅ Event written to events.jsonl
🚨 {'timestamp': '2026-04-30T14:44:22', 'server': 'world', 'username': 'Player123', 'ip': '1.2.3.4', 'port': '38328', 'reason': 'lost_connection'}
✅ Event written to events.jsonl
```
If you do not get these results, please check config file for accuracy, restart instructions if issue persists.

---
## Step 4: ⏱️ Creating Daemon Service for auto start/stop
```
sudo nano /etc/systemd/system/blocknet.service
```
Paste below and make adjustments accordlingy:
```
[Unit]
Description=BlockNet Log Watcher
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/dir
ExecStart=/usr/bin/python3 /path/to/watcher.py
StandardOutput=inherit
StandardError=inherit
Restart=always

[Install]
WantedBy=multi-user.target
```
Things needed to be changed:
>User = *your ubuntu user*\
>WorkingDirectory = ex: /home/usr/BlockNet/agent (just needs to be the directory that watcher.py exists in)\
>ExecStart= ex:/usr/bin/python3 <ins>/home/usr/BlockNet/agent/watcher.py</ins> (underlined portion needs to match the path to watcher.py, do not change /usr/bin/python3)
```
sudo systemctl enable blocknet.service
sudo systemctl start blocknet.service
sudo systemctl status blocknet.service
```
Output of last command should give something like this:
```
● blocknet.service - BlockNet Log Watcher
     Loaded: loaded (/etc/systemd/system/blocknet.service; enabled; preset: enabled)
     Active: active (exited)
```
If you recieved above output. Install is complete and logging will persist until system daemon is stopped. You can check the output by navigating to /BlockNet/agent/events.jsonl after an event has posted. To test again, refer to step 3.

---
## 🚨 Uninstalling
```
sudo systemctl stop blocknet.service
sudo systemctl disable blocknet.service
sudo systemctl status blocknet.service
```
Last command should indicate the service is no longer active. Delete all files associated with BlockNet with rm.
