
import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import openmeteo_requests
import requests_cache
from retry_requests import retry

from . import config
from . import import_from_openmeteo

from typing import Tuple, List, Dict
from datetime import datetime, timezone, timedelta
from enum import Enum

global engine


class InsertStatus(Enum):
    """
    ## ELEMENTS HAVE TO HAVE VALUES IDENTICAL WITH creating_tables.sql FILE.
    """
    SUCCESS = 0
    MASUREMENT_ALREADY_EXISTS = 1
    ALL_MEASUREMENTS_EXISTED = 2
    SOME_MEASUREMENTS_EXISTED = 3


class Location:
    def __init__(self, name: str, latitude: float, longitude: float, elevation: float, id: int | None = None):
        self.id = id
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation


def destroy_all_tables() -> None:
    """
    # This function deletes ALL TABLES IN DATABASE.

    Use wisely.
    """
    p = __file__.removesuffix("Python_code/import_module/database.py")+"SQL_scripts/deleting_tables.sql"
    harbinger_of_destruction = ""
    with open(p, 'r') as file:
        harbinger_of_destruction = file.read()
    with engine.connect() as connection:
            connection.execute(text(harbinger_of_destruction))
            connection.commit()


def create_all_tables() -> None:
    """
    Function that creates tables in **EMPTY** database.

    If database contains tables included in *SQL_scripts/creating_tables.sql* file, database will throw an exception.
    """
    p = __file__.removesuffix("Python_code/import_module/database.py")+"SQL_scripts/creating_tables.sql"
    the_joy_of_creation = ""
    with open(p, 'r') as file:
        the_joy_of_creation = file.read()
    with engine.connect() as connection:
            connection.execute(text(the_joy_of_creation))
            connection.commit()


def setup_engine(url: URL):
    """
    Contains *sqlalchemy.create_engine* function. 

    # Has to be run before any other function in module!
    
    :param url: URL of database;
    :type url: sqlalchemy.URL
    """
    global engine
    engine = create_engine(url)


def add_location(location: Location) -> bool:
    """
    Adds location to database. Geographical coordinates are rounded to nearest available in *OpenMeteo* simulation grid.
    
    :param location: Location to add. `Location.id` field is disregarded (can be None).
    :type location: database.Location
    :return: Returns **False** if location already exists and **True** if location is added successfully.
    :rtype: bool
    """
    params = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "elevation": location.elevation
    }
    responses = import_from_openmeteo.get_responses(params)
    response = responses[0]
    latitude = response.Latitude()
    longitude = response.Longitude()
    elevation = response.Elevation()

    with engine.connect() as connection:
        same_location = pd.DataFrame(connection.execute(text(f"SELECT 1 FROM location_table WHERE location_table.latitude = {latitude} AND location_table.longitude = {longitude} AND location_table.elevation = {elevation};")))
        if not same_location.empty: return False
        connection.execute(text(f"INSERT INTO location_table (latitude, longitude, elevation, name) VALUES ({latitude}, {longitude}, {elevation}, '{location.name}');"))
        connection.commit()
    return True


def get_dataframe_from_sql(sql_command: str) -> pd.DataFrame:
    """
    Sends given querry to database and converts response to pandas dataframe.
    
    :param sql_command: `SELECT` type SQL command
    :type sql_command: str
    :return: Database response
    :rtype: DataFrame
    """
    with engine.connect() as connection:
        result = connection.execute(text(sql_command))
        connection.commit()
        df = pd.DataFrame(result)
        return df


def get_locations(filter: str|None=None) -> List[Location]:
    """
    Function returns locations from database.

    Internally function calls:
    
    `
    SELECT location_id, latitude, longitude, elevation, name 
    FROM location_table
    `
    
    :param filter: Text added to the end of command above. Allows for `JOIN` and `WHERE`.
    :type filter: str | None
    :return: List of locations returned from database.
    :rtype: List[database.Location]
    """
    command = "SELECT location_id, latitude, longitude, elevation, name FROM location_table"
    if filter is None:
        command += ";"
    else:
        command += filter + " ;"
    df = get_dataframe_from_sql(command)
    locations = []
    for name, line in df.iterrows():
        locations.append(Location(line["name"], line["latitude"], line["longitude"], line["elevation"], line["location_id"]))
    return locations


def get_or_create_date_id(date: str, create_new_entry: bool = False) -> int | None:
    """
    Function that gets date_id from given date. If specified date doesnt exists, then creates new entry or returns None.

    :param date: Date in format "YYYY-MM-DD"
    :type date: str
    :param create_new_entry: If **False** - When date isn't in database -> return None.     If **True** - When date isn't in database -> Create new date in database and return its date_id
    :type create_new_entry: bool
    """
    sql_command = f"""
        WITH insert_result AS (
            INSERT INTO date_table(date_value)
                VALUES ('{date}')
                ON CONFLICT (date_value) DO NOTHING
                RETURNING date_id
        )
        SELECT date_id 
            FROM insert_result
            UNION ALL
            SELECT date_id
                FROM date_table
                WHERE date_value = '{date}'
        ;
        """ if create_new_entry else f"""
        SELECT date_id
            FROM date_table
            WHERE date_value = '{date}';
        """
    df = get_dataframe_from_sql(sql_command)
    if df.empty: return None
    return df.at[0, 'date_id']


def get_or_create_time_id(time: str, create_new_entry: bool = False) -> int | None:
    """
    Function that gets time_id from given time. If specified time doesnt exists, then creates new entry or returns None.

    :param time: time in format "HH-MM-SS"
    :type time: str
    :param create_new_entry: When time is not found in database **True** allows for creation of new entry in database, **False** will cause to return *None* 
    :type create_new_entry: bool
    :return: Found or created *time_id*; None unable to create and time not found in database.
    :rtype: int | None
    """
    sql_command = f"""
        WITH insert_result AS (
            INSERT INTO time_table(time_value)
                VALUES ('{time}')
                ON CONFLICT (time_value) DO NOTHING
                RETURNING time_id
        )
        SELECT time_id 
            FROM insert_result
            UNION ALL
            SELECT time_id
                FROM time_table
                WHERE time_value = '{time}'
        ;
        """ if create_new_entry else f"""
        SELECT time_id
            FROM time_table
            WHERE time_value = '{time}';
        """
    df = get_dataframe_from_sql(sql_command)
    if df.empty: return None
    return df.at[0, 'time_id']


def check_if_measurement_already_exists(date: str, time: str, location_id: int) -> int | None:
    """
    Function checks if measurement entry with given timestamp exists in database. Returns None if not found, returns measurement_id of measurement with specified timestamp.
    
    :params date: Date as string like "YYYY-MM-DD"
    :type timestamp: str

    :params time: Time as string like "HH-MM"
    :type timestamp: str

    :return: None if no measurement has the same timestamp / measurement_id if same one exists.
    :rtype: int | None
    """
    date_id = get_or_create_date_id(date, False)
    time_id = get_or_create_time_id(time, False)
    if (date_id is None) or (time_id is None): return None
    df = get_dataframe_from_sql(f"SELECT measurement_id FROM measurement WHERE date_id = {date_id} AND time_id = {time_id} AND location_id = {location_id};")
    if df.empty: return None
    return df.at[0, "measurement_id"]


def update_error_code(import_id: int, insert_status: InsertStatus) -> None:
    with engine.connect() as connection:
        connection.execute(text(f"UPDATE log_import SET error_id = {insert_status.value} WHERE log_import.import_id = {import_id};"))
        connection.commit()


def insert_log_import() -> int:
    """
    Function creates new entry in *log_import* table in database.

    New entry contains only current date and time.
    
    :return: *import_id* of freshly created entry.
    :rtype: int
    """
    now = datetime.now()
    date = str(now.date())
    time = now.strftime("%H:%M:%S")
    date_id = get_or_create_date_id(date, True)
    time_id = get_or_create_time_id(time, True)
    with engine.connect() as connection:
        connection.execute(text(f"INSERT INTO log_import (date_id, time_id) VALUES ({date_id}, {time_id});"))
        connection.commit()
    new_index = get_dataframe_from_sql("SELECT currval(pg_get_serial_sequence('log_import', 'import_id')) AS new_id;").at[0, 'new_id']
    return new_index


def insert_measurement_single(import_id: int, location_id: int, api_response: import_from_openmeteo.MeteoResponse) -> InsertStatus:
    measurement_id = check_if_measurement_already_exists(api_response.date, api_response.time, location_id)
    if measurement_id is not None: return InsertStatus.MASUREMENT_ALREADY_EXISTS

    date_id = get_or_create_date_id(api_response.date, True)
    time_id = get_or_create_time_id(api_response.time, True)
 
    measurement_id = get_dataframe_from_sql(f"""
        INSERT INTO measurement (location_id, date_id, time_id, import_id) 
            VALUES ({location_id}, {date_id}, {time_id}, {import_id})
            RETURNING measurement_id;
        """).at[0, 'measurement_id']

    with engine.connect() as connection:
        connection.execute(text(f"INSERT INTO temperature (measurement_id, temperature, apparent_temperature) VALUES ({measurement_id}, {api_response.temperature_2m}, {api_response.apparent_temperature});"))
        connection.execute(text(f"INSERT INTO precipitation (measurement_id, relative_humidity, precipitation, rain, snowfall) VALUES ({measurement_id}, {api_response.relative_humidity_2m}, {api_response.precipitation}, {api_response.rain}, {api_response.snowfall});"))
        connection.execute(text(f"INSERT INTO wind (measurement_id, wind_speed, wind_direction, wind_gusts) VALUES ({measurement_id}, {api_response.wind_speed_10m}, {api_response.wind_direction_10m}, {api_response.wind_gusts_10m});"))
        connection.execute(text(f"INSERT INTO weather (measurement_id, surface_pressure, cloud_cover, weather_code_id) VALUES ({measurement_id}, {api_response.pressure_msl}, {api_response.cloud_cover}, {api_response.weather_code});"))
        connection.commit()
    return InsertStatus.SUCCESS


def insert_measurement_multiple(import_id: int, location_id: int, api_response: import_from_openmeteo.MultipleMeteoResponses) -> Dict[Tuple[str, str], InsertStatus]:
    status_dict = {}
    for response in api_response.iterator():
        status = insert_measurement_single(import_id, location_id, response)
        status_dict[(response.date, response.time)] = status
    return status_dict


def insert_api_response_current_time(locations: List[Location]) -> Dict[int, Tuple[str, InsertStatus]]:
    params = {
        "latitude": [l.latitude for l in locations],
        "longitude": [l.longitude for l in locations],
        "elevation": [l.elevation for l in locations],
        "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "weather_code", "cloud_cover", "pressure_msl", "precipitation", "rain", "snowfall", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"],
    }
    responses = import_from_openmeteo.get_responses(params)

    result_dict = {}
    import_id = insert_log_import()
    for response, location in zip(responses, locations):
        status = insert_measurement_single(import_id, location.id, import_from_openmeteo.MeteoResponse(response.Current()))
        update_error_code(import_id, status)
        result_dict[location.id] = (location, status)
    return result_dict


def insert_api_response_hourly(locations: List[Location], start_date: str, end_date: str):
    params = {
        "latitude": [l.latitude for l in locations],
        "longitude": [l.longitude for l in locations],
        "elevation": [l.elevation for l in locations],
        "hourly": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "weather_code", "cloud_cover", "pressure_msl", "precipitation", "rain", "snowfall", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"],
        "start_date": start_date,
	    "end_date": end_date,
    }
    responses = import_from_openmeteo.get_responses(params)

    result_dict = {}
    import_id = insert_log_import()
    for response, location in zip(responses, locations):
        status_dict = insert_measurement_multiple(import_id, location.id, import_from_openmeteo.MultipleMeteoResponses(response.Hourly()))
        final_status = InsertStatus.SUCCESS
        if InsertStatus.MASUREMENT_ALREADY_EXISTS in status_dict.values():
            if InsertStatus.SUCCESS not in status_dict.values():
                final_status = InsertStatus.ALL_MEASUREMENTS_EXISTED
            else:
                final_status = InsertStatus.SOME_MEASUREMENTS_EXISTED
        update_error_code(import_id, final_status)
        result_dict[location.id] = (location, final_status)
    return result_dict

