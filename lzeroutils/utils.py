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
Utility functions for converting POS data to UTM streams and 
handling internal formatting.

Includes UTM projection, time series segmentation, 
and file naming helpers.
"""
import datetime
import pyproj


def convert_to_streams(data):
    """
    Convert WGS84 lon/lat to UTM x/y and split data into continuous
    chunks with automatic dt detection.

    Args:
        data (dict): Dict containing at least:
            - 'datetime' : list of ISO strings
            - 'lon' : list of floats
            - 'lat' : list of floats
            - 'h' : list of floats

    Returns:
        list: Each element is a dict:
            {
                'starttime': str,
                'delta': float,
                'x_data': list,
                'y_data': list,
                'z_data': list
            }
    """
    if not all(k in data for k in ('datetime', 'lon', 'lat', 'h')):
        raise ValueError(
            "Data must contain 'datetime', 'lon', 'lat', and 'h' keys."
        )

    times = [datetime.datetime.fromisoformat(t.replace('/', '-'))
             for t in data['datetime']]

    coords = list(zip(data['lon'], data['lat']))
    utms = _lonlat_to_utm(coords)
    x = [u[0] for u in utms]
    y = [u[1] for u in utms]
    z = data['h']

    if len(times) < 2:
        raise ValueError("At least two samples required to compute dt.")

    dts = [(t2 - t1).total_seconds()
           for t1, t2 in zip(times[:-1], times[1:])]
    dt_median = sorted(dts)[len(dts)//2]

    chunks = []
    indices = [0]
    for i in range(1, len(times)):
        delta = (times[i] - times[i-1]).total_seconds()
        if abs(delta - dt_median) > dt_median * 0.5:
            chunk = _extract_displacement_chunk(
                x, y, z, times, indices, dt_median
            )
            chunks.append(chunk)
            indices = [i]
        else:
            indices.append(i)

    if indices:
        chunk = _extract_displacement_chunk(
            x, y, z, times, indices, dt_median
        )
        chunks.append(chunk)

    return chunks


def _extract_displacement_chunk(x, y, z, times, indices, dt):
    """
    Extract a displacement chunk as a dict.

    Args:
        x (list): x coordinates.
        y (list): y coordinates.
        z (list): z coordinates.
        times (list): datetime objects.
        indices (list): Indices of the chunk.
        dt (float): Sampling interval.

    Returns:
        dict: Chunk with starttime, delta, x/y/z data.
    """
    starttime = times[indices[0]].isoformat(timespec='milliseconds')
    x_chunk = [x[i] for i in indices]
    y_chunk = [y[i] for i in indices]
    z_chunk = [z[i] for i in indices]

    return {
        'starttime': starttime,
        'delta': dt,
        'x_data': x_chunk,
        'y_data': y_chunk,
        'z_data': z_chunk
    }


def _lonlat_to_utm(coords):
    """
    Convert longitude and latitude coordinates to UTM.

    Args:
        coords (list or tuple): Either
            - Single tuple (lon, lat), or
            - List of (lon, lat) tuples.

    Returns:
        list: List of tuples
            (easting, northing, zone_number, hemisphere)
            for each input coordinate.
    """
    if isinstance(coords, tuple):
        coords = [coords]

    results = []
    for lon, lat in coords:
        zone_number = int((lon + 180) / 6) + 1
        hemisphere = 'N' if lat >= 0 else 'S'
        proj = pyproj.Proj(proj='utm', zone=zone_number, ellps='WGS84',
                           south=lat<0)
        easting, northing = proj(lon, lat)
        results.append((easting, northing, zone_number, hemisphere))

    return results


def _doy_to_monthday_str(year, doy):
    """
    Convert year and day-of-year to month-day string.

    Args:
        year (int): Year.
        doy (int): Day of year.

    Returns:
        str: Month-day in MM.DD format.
    """
    date = datetime.datetime(year, 1, 1) + datetime.timedelta(doy - 1)
    return f"{date.month:02d}.{date.day:02d}"


def _doy_to_ymd_str(year, doy):
    """
    Convert year and day-of-year to YYYY-MM-DD string.

    Args:
        year (int): Year.
        doy (int): Day of year.

    Returns:
        str: Date string in YYYY-MM-DD format.
    """
    date = datetime.datetime(year, 1, 1) + datetime.timedelta(doy - 1)
    return date.strftime('%Y-%m-%d')


def _hour_to_letter(hour):
    """
    Convert an integer hour (0-23) to corresponding letter code.

    Args:
        hour (int): Hour of day (0-23).

    Returns:
        str: Corresponding lowercase letter.
    """
    letters = 'abcdefghijklmnopqrstuvwx'
    if 0 <= hour <= 23:
        return letters[hour]
    raise ValueError('Hour must be between 0 and 23.')


def _letter_to_hour(letter):
    """
    Convert hour letter code to integer hour (0-23).

    Args:
        letter (str): Single lowercase letter.

    Returns:
        int: Hour of day.
    """
    letters = 'abcdefghijklmnopqrstuvwx'
    if letter in letters:
        return letters.index(letter)
    raise ValueError(f"Invalid hour letter: {letter}")


def _format_interval(start_dt, end_dt):
    """
    Format interval string with millisecond precision.

    Args:
        start_dt (datetime): Start timestamp.
        end_dt (datetime): End timestamp.

    Returns:
        str: Interval string.
    """
    fmt = '%Y-%m-%dT%H:%M:%S.%f'
    s = start_dt.strftime(fmt)[:-3]
    e = end_dt.strftime(fmt)[:-3]
    return f"From {s} To {e}"

