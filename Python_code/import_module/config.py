
import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import os
from enum import Enum


class ConfigStatus(Enum):
    SUCCESS = 0
    NO_CONFIG_FILE = 1
    CONFIG_FILE_EXISTS = 2
    INCORRECT_URL_SYNTAX = 3
    

def save_config(database_url: URL, overwrite: bool = False) -> ConfigStatus:
    """
    Function that saves given URL to file.

    :param database_url: URL to save.
    :type database_url: sqlalchemy.URL

    :param overwrite: Value **True** allows for overwriting existing config file. **False** will prevent overwriting existing file.
    :type overwrite: bool

    :return config.ConfigStatus: Returns SUCCESS if everything went right, CONFIG_FILE_EXISTS if config file exists and *overwrite* = False.
    """
    if os.path.exists("./config.bin"):
        if not overwrite: return ConfigStatus.CONFIG_FILE_EXISTS
        with open("./config.bin", 'wb') as file:
            file.write(database_url.render_as_string(False).encode())
    else:
        with open("./config.bin", 'xb') as file:
            file.write(database_url.render_as_string(False).encode())
    return ConfigStatus.SUCCESS

def read_config() -> URL | ConfigStatus:
    """
    Function for reading URL from saved config file.
    Returns config.ConfigStatus if an error is encountered.

    **NO_CONFIG_FILE** is returned if config file doesn't exist.

    **INCORRECT_URL_SYNTAX** if data read from file cannot be converted to sqlalchemy.URL.


    :return: Returns url from config file or ConfigStatus if an error is encountered.
    :rtype: sqlalchely.URL | config.ConfigStatus
    """
    if not os.path.exists("./config.bin"): return None
    database_url = ""
    with open("./config.bin", 'rb') as file:
        database_url = file.readline().decode()
    drivername, s = database_url.split("://", 1)
    username, s = s.split(":", 1)
    password, s = s.split("@", 1)
    host, s = s.split(":", 1)
    port, database = s.split("/")
    port = int(port)
    db_url = URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    return db_url
    