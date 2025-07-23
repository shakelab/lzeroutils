# lzeroutils

Client/server utilities for accessing and processing real-time seismic data in the LZERO system.

## Overview

`lzeroutils` provides a lightweight and extensible Python implementation of a TCP-based communication system for the distribution of GNSS-derived displacement time series.

It includes:

- `LZEROServer`: a TCP server that shares local POS data organized by station and time.
- `LZEROClient`: a client that can request station lists, time availability, and time series from the server.
- Conversion utilities to transform WGS84 coordinate time series into continuous UTM-based displacement streams.

This toolkit is designed for integration into rapid-response seismic monitoring frameworks, but can be adapted for any distributed GNSS data acquisition setup.

---

## Installation

### 🔹 Install from GitHub (standard mode)

```bash
pip install git+https://github.com/your-org/lzeroutils.git
```

### 🔹 Install from a local copy

Clone the repository first:

```bash
git clone https://github.com/your-org/lzeroutils.git
cd lzeroutils
pip install .
```

### 🔹 Developer mode (editable install)

To make local modifications without reinstalling:

```bash
pip install -e .
```

This mode is useful during development, as changes to the source files will take effect immediately.

---

## Usage

### Starting the server manually

```bash
python -m lzeroutils.server --root /path/to/data --port 5000
```

### Using the client

```python
from lzeroutils import LZEROClient, convert_to_streams

client = LZEROClient('your.server.ip', port=5000)

# List available stations
stations = client.list_available_stations()

# List time availability
times = client.list_available_time('ST01')

# Request data
data = client.get_data('ST01', '2025-07-01T00:00:00', '2025-07-01T01:00:00')

# Convert to UTM displacement streams
streams = convert_to_streams(data)
```

Each stream is a dictionary with:
- `starttime` (ISO string)
- `delta` (sampling interval in seconds)
- `x_data`, `y_data`, `z_data` (displacement values in meters)

---

## Running as a system service

For Linux-based deployments, the server can be installed as a `systemd` service.

### Step-by-step instructions:

```bash
cd services
sudo cp lzeroserver.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lzeroserver
sudo systemctl start lzeroserver
```

To check the status:

```bash
sudo systemctl status lzeroserver
```

To view logs:

```bash
journalctl -u lzeroserver -f
```

---

## License

This software is released under the **GNU Affero General Public License v3.0**.  
See the LICENSE file for details.
