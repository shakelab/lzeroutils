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
LZEROStreamClient: client interface for retrieving displacement time series
from an LZEROServer instance, integrated with the ShakeLab StreamCollection
structure.
"""
from lzeroutils import LZEROClient, convert_to_streams
from shakelab.signals.base import Record, StreamCollection


class LZEROStreamClient:
    """
    Client interface to retrieve POS-based displacement waveforms from a
    running LZEROServer.

    Parameters
    ----------
    host : str
        IP address or hostname of the LZEROServer.
    port : int
        Port number to connect to.
    """

    def __init__(self, host='localhost', port=5000):
        self.client = LZEROClient(host, port)

    def get_waveform(self, station, starttime, endtime):
        """
        Retrieve waveform data and return it as a StreamCollection.

        Parameters
        ----------
        station : str
            Station code (e.g., 'ST01').
        starttime : str
            Start time in ISO8601 format.
        endtime : str
            End time in ISO8601 format.

        Returns
        -------
        StreamCollection
            Collection of Record objects for E, N, U components
            with channel codes LGE, LGN, LGU.
        """
        data_dict = self.client.get_data(
            station=station,
            starttime=starttime,
            endtime=endtime
        )

        stream_chunks = convert_to_streams(data_dict)
        sc = StreamCollection()

        for chunk in stream_chunks:
            sc.append(Record(
                data=chunk['x_data'],
                delta=chunk['delta'],
                time=chunk['starttime'],
                sid=f'.{station}..LGE'
            ))
            sc.append(Record(
                data=chunk['y_data'],
                delta=chunk['delta'],
                time=chunk['starttime'],
                sid=f'.{station}..LGN'
            ))
            sc.append(Record(
                data=chunk['z_data'],
                delta=chunk['delta'],
                time=chunk['starttime'],
                sid=f'.{station}..LGU'
            ))

        return sc

