
import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import openmeteo_requests
import requests_cache
from retry_requests import retry

from import_module import config
from import_module import import_from_openmeteo

from typing import Tuple, List
from datetime import datetime, timezone, timedelta

global engine


def setup_engine(url: str):
    """
    Contains *sqlalchemy.create_engine* function. 

    # Has to be run before any other function in module!
    
    :param url: URL of database;
    :type url: str
    """
    global engine
    engine = create_engine(url)


def add_location(latitude: float, longitude: float, elevation: float, name: str) -> bool:
    """
    Adds location to database. Return True on successful insertion, return False if location already exists in database.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "elevation": elevation
    }
    responses = import_from_openmeteo.get_responses(params)
    response = responses[0]
    latitude = response.Latitude()
    longitude = response.Longitude()
    elevation = response.Elevation()

    with engine.connect() as connection:
        same_location = pd.DataFrame(connection.execute(text(f"SELECT 1 FROM location_table WHERE location_table.latitude = {latitude} AND location_table.longitude = {longitude} AND location_table.elevation = {elevation};")))
        if not same_location.empty: return False
        max_index = pd.DataFrame(connection.execute(text("SELECT MAX(location_table.location_id) FROM location_table;")))
        max_index = max_index.at[0, 'max']
        if max_index is None: max_index = 0
        connection.execute(text(f"INSERT INTO location_table (location_id, latitude, longitude, elevation, name) VALUES ({max_index+1}, {latitude}, {longitude}, {elevation}, '{name}');"))
        connection.commit()
    return True


def get_dataframe_from_sql(sql_command: str) -> pd.DataFrame:
    with engine.connect() as connection:
        result = connection.execute(text(sql_command))
        df = pd.DataFrame(result)
        return df


def get_locations_position() -> Tuple[List[int], List[float], List[float]]:
    """
    Gets all locations from database.

    :return: Tuple of lists like ([location_ids], [latitudes], [lingitudes], [elevations])
    :rtype: Tuple[List[int], List[float], List[float]]
    """
    df = get_dataframe_from_sql("SELECT location_id, latitude, longitude, elevation FROM location_table;")
    return (df['location_id'].values.tolist(), df['latitude'].values.tolist(), df['longitude'].values.tolist(), df['elevation'].values.tolist())


def get_or_create_date_id(date: str, create_new_entry: bool = False) -> int | None:
    """
    Function that gets date_id from given date. If specified date doesnt exists, then creates new entry or returns None.

    :param date: Date in format "YYYY-MM-DD"
    :type date: str
    :param create_new_entry: If **False** - When date isn't in database -> return None.     If **True** - When date isn't in database -> Create new date in database and return its date_id
    :type create_new_entry: bool
    """
    df = get_dataframe_from_sql(f"SELECT date_table.date_id FROM date_table WHERE date_table.date_value = '{date}';")
    if df.empty:
        if not create_new_entry: return None
        with engine.connect() as connection:
            max_index = pd.DataFrame(connection.execute(text("SELECT MAX(date_table.date_id) FROM date_table;")))
            max_index = max_index.at[0, 'max']
            if max_index is None: max_index = 0
            connection.execute(text(f"INSERT INTO date_table (date_id, date_value) VALUES ({max_index+1}, '{date}');"))
            connection.commit()
        return max_index+1
    else:
        return df.at[0, "date_id"]


def get_or_create_time_id(time: str, create_new_entry: bool = False) -> int | None:
    """
    Function that gets time_id from given time. If specified time doesnt exists, then creates new entry or returns None.

    :param time: time in format "HH-MM-SS"
    :type time: str
    :param create_new_entry: If **False** - When time isn't in database -> return None.     If **True** - When time isn't in database -> Create new time in database and return its time_id
    :type create_new_entry: bool
    """
    df = get_dataframe_from_sql(f"SELECT time_table.time_id FROM time_table WHERE time_table.time_value = '{time}';")
    if df.empty:
        if not create_new_entry: return None
        with engine.connect() as connection:
            max_index = pd.DataFrame(connection.execute(text("SELECT MAX(time_table.time_id) FROM time_table;")))
            max_index = max_index.at[0, 'max']
            if max_index is None: max_index = 0
            connection.execute(text(f"INSERT INTO time_table (time_id, time_value) VALUES ({max_index+1}, '{time}');"))
            connection.commit()
        return max_index+1
    else:
        return df.at[0, "time_id"]


def split_timestamp(timestamp: str) -> Tuple[str, str, str]:
    date, time = timestamp.split('T')
    if '+' in time:
        time, timezone_offset = time.split('+')
        return date, time, timezone_offset
    return date, time, ""


def check_if_measurement_already_exists(timestamp: str) -> int | None:
    """
    Function checks if measurement entry with given timestamp exists in database. Returns None if not found, returns measurement_id of measurement with specified timestamp.
    
    :params timestamp: Timestamp in ISO 8601 string ("YYYY-MM-DDTHH-MM-SS)
    :type timestamp: str

    :return: None if no measurement has the same timestamp / measurement_id if same one exists.
    :rtype: int | None
    """
    date, time = timestamp.split('T')
    time, timezone_offset = time.split('+')
    date_id = get_or_create_date_id(date, False)
    time_id = get_or_create_time_id(time, False)
    if (date_id is None) or (time_id is None): return None
    df = get_dataframe_from_sql(f"SELECT measurement_id FROM measurement WHERE date_id = {date_id} AND time_id = {time_id};")
    if df.empty: return None
    return df.at[0, "measurement_id"]


def insert_log_import() -> int:

    date, time, _ = split_timestamp(datetime.now().isoformat())
    date_id = get_or_create_date_id(date, True)
    time_id = get_or_create_time_id(time, True)
    with engine.connect() as connection:
        df = pd.DataFrame(connection.execute(text("SELECT MAX(import_id) FROM log_import;")))
        import_id = df.at[0, 'max']
        if import_id is None: import_id = 0
        import_id += 1
        connection.execute(text(f"INSERT INTO log_import (import_id, date_id, time_id) VALUES ({import_id}, {date_id}, {time_id});"))
        connection.commit()
        return import_id


def insert_measurement(import_id: int, location_id: int, api_response) -> bool:
    
    current_time = datetime.fromtimestamp(api_response.Time(), tz=timezone.utc).isoformat()
    
    measurement_id = check_if_measurement_already_exists(current_time)
    if measurement_id is not None: return None

    current_temperature_2m = api_response.Variables(0).Value()
    current_relative_humidity_2m = api_response.Variables(1).Value()
    current_apparent_temperature = api_response.Variables(2).Value()
    current_weather_code = api_response.Variables(3).Value()
    current_cloud_cover = api_response.Variables(4).Value()
    current_pressure_msl = api_response.Variables(5).Value()
    current_precipitation = api_response.Variables(6).Value()
    current_rain = api_response.Variables(7).Value()
    current_snowfall = api_response.Variables(8).Value()
    current_wind_speed_10m = api_response.Variables(9).Value()
    current_wind_direction_10m = api_response.Variables(10).Value()
    current_wind_gusts_10m = api_response.Variables(11).Value()

    date, time, _ = split_timestamp(current_time)
    date_id = get_or_create_date_id(date, True)
    time_id = get_or_create_time_id(time, True)
    
    
    
    with engine.connect() as connection:
        max_index = pd.DataFrame(connection.execute(text("SELECT MAX(measurement_id) FROM measurement;")))
        max_index = max_index.at[0, 'max']
        if max_index is None: max_index = 0
        measurement_id = max_index + 1
        connection.execute(text(f"INSERT INTO measurement (measurement_id, location_id, date_id, time_id, import_id) VALUES ({measurement_id}, {location_id}, {date_id}, {time_id}, {import_id});"))
        connection.execute(text(f"INSERT INTO temperature (measurement_id, temperature, apparent_temperature) VALUES ({measurement_id}, {current_temperature_2m}, {current_apparent_temperature});"))
        connection.execute(text(f"INSERT INTO precipitation (measurement_id, relative_humidity, precipitation, rain, snowfall) VALUES ({measurement_id}, {current_relative_humidity_2m}, {current_precipitation}, {current_rain}, {current_snowfall});"))
        connection.execute(text(f"INSERT INTO wind (measurement_id, wind_speed, wind_direction, wind_gusts) VALUES ({measurement_id}, {current_wind_speed_10m}, {current_wind_direction_10m}, {current_wind_gusts_10m});"))
        connection.execute(text(f"INSERT INTO weather (measurement_id, surface_pressure, cloud_cover, weather_code_id) VALUES ({measurement_id}, {current_pressure_msl}, {current_cloud_cover}, {current_weather_code});"))
        connection.commit()



def insert_api_response_current_time() -> bool:
    locations_position = get_locations_position()
    params = {
        "latitude": locations_position[1],
        "longitude": locations_position[2],
        "elevation": locations_position[3],
        "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "weather_code", "cloud_cover", "pressure_msl", "precipitation", "rain", "snowfall", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"],
    }
    responses = import_from_openmeteo.get_responses(params)

    import_id = insert_log_import()

    for response, location_id in zip(responses, locations_position[0]):
        
        insert_measurement(import_id, location_id, response.Current())
    


        