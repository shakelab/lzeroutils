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
LZEROClient: TCP client for querying POS data from an LZEROServer.

Implements commands for retrieving GNSS-derived time series 
and metadata via a socket interface.
"""
import socket


class LZEROClient:
    """
    TCP client to request POS data from LZEROServer.

    Attributes:
        host (str): Server IP address.
        port (int): Server port.
        data (dict): Dictionary of arrays with last retrieved data.
    """

    def __init__(self, host, port=5000):
        """
        Initialize the LZEROClient.

        Args:
            host (str): Server IP address.
            port (int): Server port.
        """
        self.host = host
        self.port = port
        self.data = None

    def get_data(self, station, starttime, endtime):
        """
        Request POS data for a station and time interval.
        Stores results internally as dict of arrays.
    
        Args:
            station (str): Station code.
            starttime (str): Start time (ISO format).
            endtime (str): End time (ISO format).
        """
        request = f"GET_DATA,{station},{starttime},{endtime}"
        response = self._send_request(request)
        self.data = self._parse_response(response)

        return self.data

    def list_available_stations(self):
        """
        Request list of available stations from server.
    
        Returns:
            list: Station codes available on server.
        """
        request = "LIST_STATIONS"
        response = self._send_request(request)
        lines = response.strip().split('\n')
        return lines if lines != [''] else []

    def list_available_time(self, station):
        """
        Request list of time availability for a given station.
    
        Args:
            station (str): Station code.
    
        Returns:
            list: Dates available for this station.
        """
        request = f"LIST_TIME,{station}"
        response = self._send_request(request)
        lines = response.strip().split('\n')
        return lines if lines != [''] else []

    def _send_request(self, request):
        """
        Send request string to server and receive response.

        Args:
            request (str): Request string.

        Returns:
            str: Response string from server.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((self.host, self.port))
                s.sendall(request.encode('utf-8'))
                chunks = []
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                return b''.join(chunks).decode('utf-8')

        except socket.error as e:
            raise ConnectionError(f"LZEROClient connection error: {e}")

    def _parse_response(self, response):
        """
        Parse server response string into dict of arrays.

        Args:
            response (str): Server response.

        Returns:
            dict: POS data with keys as field names.
        """
        lines = response.strip().split('\n')
        result = {
            'datetime': [],
            'lat': [],
            'lon': [],
            'h': [],
            'fix': [],
            'nsat': [],
            'dx': [],
            'dy': [],
            'dz': [],
            'vx': [],
            'vy': [],
            'vz': [],
            'pdop': [],
            'temp': []
        }
        for line in lines:
            line = line.strip()
            if line and not line.startswith('ERROR'):
                parts = line.split()
                parts[0] = parts[0].replace('/', '-')
                try:
                    dt = parts[0] + 'T' + parts[1]
                    result['datetime'].append(dt)
                    result['lat'].append(float(parts[2]))
                    result['lon'].append(float(parts[3]))
                    result['h'].append(float(parts[4]))
                    result['fix'].append(int(parts[5]))
                    result['nsat'].append(int(parts[6]))
                    result['dx'].append(float(parts[7]))
                    result['dy'].append(float(parts[8]))
                    result['dz'].append(float(parts[9]))
                    result['vx'].append(float(parts[10]))
                    result['vy'].append(float(parts[11]))
                    result['vz'].append(float(parts[12]))
                    result['pdop'].append(float(parts[13]))
                    result['temp'].append(float(parts[14]))
                except (IndexError, ValueError):
                    continue
        return result

    def list_fields(self):
        """
        Return list of available fields.
        """
        if self.data:
            return list(self.data.keys())
        return []

    def get_field(self, field):
        """
        Get a specific field array from stored data.

        Args:
            field (str): Field name.

        Returns:
            list: Array of values for requested field, or None.
        """
        if self.data and field in self.data:
            return self.data[field]
        return None

