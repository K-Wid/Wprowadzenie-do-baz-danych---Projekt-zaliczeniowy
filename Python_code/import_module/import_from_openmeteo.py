import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import openmeteo_requests
import requests_cache
from retry_requests import retry

from typing import Tuple, Any

class MeteoResponse:
    """
    Class containing OpenMeteo response data in more intuitive way.

    ### Methods:

    #### __init__(self, api_response, *< specific parameters >*)
        If *api_response* parameter is None then new object is created from *< specific parameters >*. 
        If *api_response* is a response object from OpenMeteo (like one returned from *get_responses* function), then object is created from that response and *< specific parameters >* are disregarded.

    ### Attributes:

    | Attribute            | Value range |       Unit |
    |----------------------|:-----------:|-----------:|
    | temperature_2m       |      -      |         °C |
    | relative_humidity_2m |   0 - 100   |          % |
    | apparent_temperature | -           |         °C |
    | weather_code         | 0 - 99      |          - |
    | cloud_cover          | 0 - 100     | %          |
    | pressure_msl         | -           | hPa        |
    | precipitation        | -           | mm         |
    | rain                 | -           | mm         |
    | snowfall             | -           | cm         |
    | wind_speed_10m       | -           | km/h       |
    | wind_direction_10m   | 0 - 360     | °          |
    | wind_gusts_10m       | -           | km/h       |
    | date                 | -           | YYYY-MM-DD |
    | time                 | -           | HH:MM:SS   |
    """
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
    """
    Class containing multiple OpenMeteo responses. 

    Attributes are in *numpy.ndarray* format - each containing one parameter of all measurements.
    
    Example:
    |          Index   |  0  |  1  |  2  |  3  |  3  |   |
    |-----------------:|:---:|:---:|:---:|:---:|:---:|:--|
    |  Temperature = [ | 22, | 25, | 30, | 27, | 15, | ] |
    | weather_code = [ |  0, |  1, |  0, | 45, |  3, | ] |
    
    First measurement occupies index 0, second - 1 and so on.

    ### Methods:
    #### __init__(self, response)
        
        Function receives OpenMeteo response with multiple measurements (like Hourly() and Daily())

    #### __getitem__(self, index: int) -> MeteoResponse

        Function allows for array-like indexing of individual measurements in object.

    #### iterator(self)

        Function allows for extraction of individual measurements in `for` loop.


    ### Attributes
    Attribures are analogous to the **MeteoResponse** class.
    """
    def __init__(self, response):
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

    ```
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
    ```

    :return: OpenMeteo API response
    :rtype: Openmeteo Response
    """
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params = params)
    return responses

