import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import openmeteo_requests
import requests_cache
from retry_requests import retry

from typing import Tuple, Any

class MeteoResponse:
    def __init__(self, 
                api_response = Any | None,
                temperature_2m: float = -1, 
                relative_humidity_2m: float = -1,
                apparent_temperature: float = -1,
                weather_code: int = -1,
                cloud_cover: float = -1,
                pressure_msl: float = -1,
                precipitation: float = -1,
                rain: float = -1,
                snowfall: float = -1,
                wind_speed_10m: float = -1,
                wind_direction_10m: float = -1,
                wind_gusts_10m: float = -1,
                date: str = "",
                time: str = ""):
        if api_response is None:
            self.temperature_2m = temperature_2m
            self.relative_humidity_2m = relative_humidity_2m
            self.apparent_temperature = apparent_temperature
            self.weather_code = weather_code
            self.cloud_cover = cloud_cover
            self.pressure_msl = pressure_msl
            self.precipitation = precipitation
            self.rain = rain
            self.snowfall = snowfall
            self.wind_speed_10m = wind_speed_10m
            self.wind_direction_10m = wind_direction_10m
            self.wind_gusts_10m = wind_gusts_10m
            self.date = date
            self.time = time
        else:
            self.temperature_2m = api_response.Variables(0).Value()
            self.relative_humidity_2m = api_response.Variables(1).Value()
            self.apparent_temperature = api_response.Variables(2).Value()
            self.weather_code = api_response.Variables(3).Value()
            self.cloud_cover = api_response.Variables(4).Value()
            self.pressure_msl = api_response.Variables(5).Value()
            self.precipitation = api_response.Variables(6).Value()
            self.rain = api_response.Variables(7).Value()
            self.snowfall = api_response.Variables(8).Value()
            self.wind_speed_10m = api_response.Variables(9).Value()
            self.wind_direction_10m = api_response.Variables(10).Value()
            self.wind_gusts_10m = api_response.Variables(11).Value()

            date_time = pd.to_datetime(api_response.Time(), unit = "s", utc = True)
            self.date = date_time.date()
            self.time = date_time.time()
        

class MultipleMeteoResponses:
    def __init__(self, response):
        response = response.Hourly()
        self.temperature_2m = response.Variables(0).ValuesAsNumpy()
        self.relative_humidity_2m = response.Variables(1).ValuesAsNumpy()
        self.apparent_temperature = response.Variables(2).ValuesAsNumpy()
        self.weather_code = response.Variables(3).ValuesAsNumpy()
        self.cloud_cover = response.Variables(4).ValuesAsNumpy()
        self.pressure_msl = response.Variables(5).ValuesAsNumpy()
        self.precipitation = response.Variables(6).ValuesAsNumpy()
        self.rain = response.Variables(7).ValuesAsNumpy()
        self.snowfall = response.Variables(8).ValuesAsNumpy()
        self.wind_speed_10m = response.Variables(9).ValuesAsNumpy()
        self.wind_direction_10m = response.Variables(10).ValuesAsNumpy()
        self.wind_gusts_10m = response.Variables(11).ValuesAsNumpy()

        date = pd.date_range(
            start = pd.to_datetime(response.Time(), unit = "s", utc = True),
            end =  pd.to_datetime(response.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = response.Interval()),
            inclusive = "left"
        )
        self.date = [str(d.date()) for d in date]
        self.time = [str(d.time()) for d in date]

    def __getitem__(self, index: int) -> MeteoResponse:
        return MeteoResponse(None, 
                             self.temperature_2m[index],
                             self.relative_humidity_2m[index],
                             self.apparent_temperature[index],
                             self.weather_code[index],
                             self.cloud_cover[index],
                             self.pressure_msl[index],
                             self.precipitation[index],
                             self.rain[index],
                             self.snowfall[index],
                             self.wind_speed_10m[index],
                             self.wind_direction_10m[index],
                             self.wind_gusts_10m[index],
                             self.date[index],
                             self.time[index])

    def iterator(self):
        i = 0
        while i < len(self.date):
            yield self[i]
            i += 1


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

