#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI to manage LZEROServer for FREDNET LZERO POS data.

Provides commands to start, stop, restart, and check the status
of the LZEROServer. Designed to be used standalone or as a systemd
service entry point.

Author: Valerio Poggi
Date: 2025-07-08
"""

import argparse
import signal
import sys
from lzeroutils import LZEROServer

# Constants
ROOT = '/mnt/EXTDISK/data/TMPNETS/2024.CAMPIFLEGREI'
PORT = 5000

server = None

def start_server(root, port):
    """
    Start the LZEROServer.

    Args:
        root (str): Root data directory.
        port (int): Port to bind the server.
    """
    global server
    server = LZEROServer(root=root, port=port)
    server.start()
    server.status()

def stop_server():
    """
    Stop the LZEROServer.
    """
    global server
    if server:
        server.stop()
    else:
        print("Server not running.")

def signal_handler(sig, frame):
    """
    Handle termination signals to stop the server gracefully.

    Args:
        sig (int): Signal number.
        frame (object): Current stack frame.
    """
    print("Signal received, stopping server...")
    stop_server()
    sys.exit(0)

def main():
    """
    Parse CLI arguments and execute the requested command.
    """
    parser = argparse.ArgumentParser(
        description="Manage the LZEROServer service."
    )
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'status', 'restart'],
        help="Command to execute."
    )
    parser.add_argument(
        '--root',
        type=str,
        default=ROOT,
        help=f"Root data directory (default: {ROOT})."
    )
    parser.add_argument(
        '--port',
        type=int,
        default=PORT,
        help=f"Port to bind the server (default: {PORT})."
    )

    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.command == 'start':
        start_server(args.root, args.port)
    elif args.command == 'stop':
        stop_server()
    elif args.command == 'status':
        if server:
            server.status()
        else:
            print("Server not running.")
    elif args.command == 'restart':
        stop_server()
        start_server(args.root, args.port)

if __name__ == '__main__':
    main()
