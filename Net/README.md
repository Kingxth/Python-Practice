# NetScanner

A lightweight Python script for local network monitoring and device tracking using nmap.

## Features

- Auto detects default gateway and local subnet
- Identifies active devices, IP addresses, MAC addresses, and hostnames
- Real-time terminal alerts for new devices, disconnections, and reconnections
- Generates custom text reports stored in a local file

## Requirements

- Python 3.10+
- `nmap` installed on your system.

## Usage

Run the script with administrative privileges (required for ARP scanning):

```bash
sudo python network.py
