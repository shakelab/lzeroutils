# ****************************************************************************
#
# Copyright (C) 2019-2025, ShakeLab Developers.
# This file is part of ShakeLab.
#
# ShakeLab is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# ShakeLab is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# with this download. If not, see <http://www.gnu.org/licenses/>
#
# ****************************************************************************
"""
LZEROServer: TCP server for distributing POS data over socket connections.

Handles client commands for station listing, time availability,
and retrieval of GNSS-derived position time series.
"""
import os
import socket
import threading
import datetime

from .utils import (
    _doy_to_ymd_str,
    _doy_to_monthday_str,
    _hour_to_letter,
    _format_interval
)


class LZEROServer:
    """
    TCP server providing POS data to LZEROClient requests.

    Attributes:
        root (str): Root directory containing station data.
        port (int): Port to bind the server socket.
    """

    def __init__(self, root, port=5000):
        """
        Initialize the LZEROServer.

        Args:
            root (str): Root directory with station data.
            port (int): Port to bind the server socket.
        """
        self.root = root
        self.port = port
        self.sock = None
        self.thread = None
        self.running = False

    def start(self):
        """
        Start the server and listen for incoming connections.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', self.port))
        self.sock.listen(5)
        print(f'LZEROServer listening on port {self.port}...')

        self.running = True
        self.thread = threading.Thread(target=self._accept_loop)
        self.thread.start()

    def stop(self):
        """
        Stop the server and close the socket.
        """
        if self.sock:
            self.running = False
            self.sock.close()
            self.sock = None
            if self.thread:
                self.thread.join()
            print('LZEROServer stopped.')
        else:
            print('LZEROServer is not running.')

    def restart(self):
        """
        Restart the server by stopping and starting it again.
        """
        print('Restarting LZEROServer...')
        self.stop()
        self.start()
        print('LZEROServer restarted.')

    def status(self):
        """
        Print current server status information.
        """
        if self.sock:
            print('LZEROServer status:')
            print(f'  Root directory: {self.root}')
            print(f'  Port: {self.port}')
            print('  Socket: active')
            if self.thread and self.thread.is_alive():
                print('  Listener thread: running')
            else:
                print('  Listener thread: not running')
        else:
            print('LZEROServer is not running.')

    def list_available_stations(self):
        """
        Return list of available station codes.
    
        Returns:
            list: Station codes found in root directory.
        """
        stations = []
        try:
            for name in os.listdir(self.root):
                path = os.path.join(self.root, name)
                if os.path.isdir(path):
                    stations.append(name)
        except Exception as e:
            print(f'Error listing stations: {e}')
        return stations

    def list_available_time(self, station):
        """
        Return list of continuous time intervals for a station,
        based only on presence of hour-letter directories.
    
        Args:
            station (str): Station code.
    
        Returns:
            list: Intervals as strings, e.g.
                'From 2025-07-03T22:00:00.000 To 2025-07-03T23:00:00.000'
        """
        from datetime import datetime, timedelta
    
        letters = 'abcdefghijklmnopqrstuvwx'
        hour_map = {l: i for i, l in enumerate(letters)}
        times = []
    
        station_path = os.path.join(self.root, station)
        if not os.path.isdir(station_path):
            return []
    
        # Collect all available datetime timestamps
        for year in sorted(os.listdir(station_path)):
            year_path = os.path.join(station_path, year)
            if not os.path.isdir(year_path):
                continue
            for doy in sorted(os.listdir(year_path)):
                doy_path = os.path.join(year_path, doy)
                if not os.path.isdir(doy_path):
                    continue
                for hour_letter in sorted(os.listdir(doy_path)):
                    hour_path = os.path.join(doy_path, hour_letter)
                    if not os.path.isdir(hour_path):
                        continue
                    if hour_letter not in hour_map:
                        continue
                    hour = hour_map[hour_letter]
                    date_str = _doy_to_ymd_str(int(year), int(doy))
                    dt = datetime.strptime(f"{date_str}T{hour:02d}:00:00.000",
                                           '%Y-%m-%dT%H:%M:%S.%f')
                    times.append(dt)
    
        # Sort timestamps
        times.sort()
    
        # Build continuous intervals
        intervals = []
        if times:
            start = end = times[0]
            for current in times[1:]:
                if current == end + timedelta(hours=1):
                    end = current
                else:
                    intervals.append(_format_interval(start, end))
                    start = end = current
            intervals.append(_format_interval(start, end))
    
        return intervals

    def _accept_loop(self):
        """
        Internal loop to accept and handle client connections.
        """
        while self.running:
            try:
                conn, addr = self.sock.accept()
                print(f'Connection from {addr}')
                handler = threading.Thread(
                    target=self._handle_client, args=(conn,))
                handler.start()
            except OSError:
                break

    def _handle_client(self, conn):
        """
        Handle a single client request.

        Args:
            conn (socket.socket): Client connection.
        """
        try:
            data = conn.recv(4096).decode('utf-8')
            print(f'Received request: {data}')
            response = self._process_request(data)
            conn.sendall(response.encode('utf-8'))
        except Exception as e:
            print(f'Error handling client: {e}')
        finally:
            conn.close()

    def _process_request(self, request):
        """
        Process client request with COMMAND,param1,param2,...
    
        Args:
            request (str): Request string.
    
        Returns:
            str: Response string.
        """
        parts = request.strip().split(',')
        command = parts[0].upper()
    
        if command == 'LIST_STATIONS':
            stations = self.list_available_stations()
            return '\n'.join(stations) + '\n'
    
        elif command == 'GET_DATA':
            if len(parts) != 4:
                return 'ERROR: GET_DATA requires station,start,end.\n'
            station, starttime, endtime = parts[1:4]
            try:
                start_dt = datetime.datetime.fromisoformat(starttime)
                end_dt = datetime.datetime.fromisoformat(endtime)
            except ValueError:
                return 'ERROR: Invalid datetime format.\n'
            lines = self._get_pos_data(station, start_dt, end_dt)
            return '\n'.join(lines) + '\n'
    
        elif command == 'LIST_TIME':
            if len(parts) != 2:
                return 'ERROR: LIST_TIME requires station.\n'
            station = parts[1]
            dates = self.list_available_time(station)
            return '\n'.join(dates) + '\n'
    
        else:
            return f'ERROR: Unknown command {command}.\n'

    def _get_pos_data(self, station, start_dt, end_dt):
        """
        Retrieve POS data for a station and time range.

        Args:
            station (str): Station code.
            start_dt (datetime): Start time.
            end_dt (datetime): End time.

        Returns:
            list[str]: List of POS data lines within interval.
        """
        result = []
        current_dt = start_dt

        while current_dt <= end_dt:
            year = current_dt.year
            doy = current_dt.timetuple().tm_yday
            hour = current_dt.hour

            filepath = self._build_filepath(station, year, doy, hour)
            if os.path.isfile(filepath):
                lines = self._read_file_lines(filepath)
                for line in lines:
                    line_time = self._parse_line_time(line)
                    if line_time and start_dt <= line_time <= end_dt:
                        result.append(line)
            current_dt += datetime.timedelta(hours=1)

        return result

    def _build_filepath(self, station, year, doy, hour):
        """
        Build full filepath for POS data file.
    
        Args:
            station (str): Station code.
            year (int): Year.
            doy (int): Day of year.
            hour (int): Hour.
    
        Returns:
            str: Full POS filepath.
        """
        letter = _hour_to_letter(hour)
        dirpath = os.path.join(
            self.root, station, str(year), f"{doy:03d}", letter)
        filename = f"{station}.{year}.{_doy_to_monthday_str(year,doy)}." \
                   f"{doy:03d}.{letter}.pos"
        return os.path.join(dirpath, filename)

    def _read_file_lines(self, filepath):
        """
        Read all lines from a file.

        Args:
            filepath (str): Path to file.

        Returns:
            list[str]: Lines in file.
        """
        with open(filepath, 'r') as f:
            return f.readlines()

    def _parse_line_time(self, line):
        """
        Parse datetime from POS line.
    
        Args:
            line (str): POS data line.
    
        Returns:
            datetime: Parsed datetime or None if failed.
        """
        try:
            parts = line.strip().split()
            date_str = parts[0].replace('/', '-')
            time_str = parts[1]
            dt_str = f"{date_str}T{time_str}"
            return datetime.datetime.fromisoformat(dt_str)
        except Exception:
            return None
