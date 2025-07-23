#!/bin/bash

# Copy the service file to the systemd directory
sudo cp lzeroserver.service /etc/systemd/system/

# Reload systemd to recognize the new unit
sudo systemctl daemon-reload

# Enable automatic start at boot
sudo systemctl enable lzeroserver

# Start the service
sudo systemctl start lzeroserver

# Check service status
sudo systemctl status lzeroserver

# View real-time logs
journalctl -u lzeroserver -f