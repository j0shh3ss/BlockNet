# BlockNet
A Python daemon that monitors server logs to detect and record unauthorized join attempts. By exporting this data in JSONL format, it builds a centralized log to help you analyze connection locations and identify malicious IPs that require broader network-level blocking.

Currently there is no installer file due to possible user config editing (to add additional ignored/whitelisted players) so manual installation instructions listed below, assuming Ubuntu OS. Use AI to convert to whatever OS you are using.

# INSTALLER INSTRUCTIONS

## List of dependencies:
> Python3 (Normally pre-installed, can verify with python3 --version)
> WatchDog

## To install dependencies (assuming Ubuntu)
```
sudo apt install python3
sudo apt install python3-watchdog
```
