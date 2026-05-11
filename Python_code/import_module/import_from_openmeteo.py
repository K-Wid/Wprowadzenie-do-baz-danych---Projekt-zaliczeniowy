import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import openmeteo_requests
import requests_cache
from retry_requests import retry

from datetime import datetime, timezone, timedelta


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