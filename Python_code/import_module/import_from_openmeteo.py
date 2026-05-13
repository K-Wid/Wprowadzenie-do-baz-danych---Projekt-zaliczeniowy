import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import openmeteo_requests
import requests_cache
from retry_requests import retry

from datetime import datetime, timezone, timedelta
from typing import Tuple

class CurrentMeteoResponse:
    def __init__(self, response):
        response = response.Current()
        self.current_temperature_2m = response.Variables(0).Value()
        self.current_relative_humidity_2m = response.Variables(1).Value()
        self.current_apparent_temperature = response.Variables(2).Value()
        self.current_weather_code = response.Variables(3).Value()
        self.current_cloud_cover = response.Variables(4).Value()
        self.current_pressure_msl = response.Variables(5).Value()
        self.current_precipitation = response.Variables(6).Value()
        self.current_rain = response.Variables(7).Value()
        self.current_snowfall = response.Variables(8).Value()
        self.current_wind_speed_10m = response.Variables(9).Value()
        self.current_wind_direction_10m = response.Variables(10).Value()
        self.current_wind_gusts_10m = response.Variables(11).Value()

        current_time = datetime.fromtimestamp(response.Time(), tz=timezone.utc).isoformat()
        date, time, timezone_offset = split_timestamp(current_time)

        self.date = date
        self.time = time
        self.timezone_offset = timezone_offset+":00"


def split_timestamp(timestamp: str) -> Tuple[str, str, str]:
    date, time = timestamp.split('T')
    if '+' in time:
        time, timezone_offset = time.split('+')
        return date, time, timezone_offset
    return date, time, ""

def get_responses(params):
    """
    Function that handles OpenMeteo API.

    :params params: Dictionary of parameters.
    :type params: Dict

    params = {
    
        "latitude": float

        "longitude": float

        "elevation": float

        "current": [param names: str]

        "minutely_15": [param names: str]

        "hourly": [param names: str]

        "daily": [param names: str]

        "start_date": str [YYY-MM-DD]

        "end_date": str [YYY-MM-DD]

    }
    """
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params = params)
    return responses