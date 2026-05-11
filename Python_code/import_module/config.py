
import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

def save_config(database_url: URL, overwrite: bool = False) -> bool:
    """
    Function that saves given URL to file.

    :param database_url: URL to save.
    :type database_url: sqlalchemy.URL

    :param overwrite: True allows for overwriting existing config file. False (with file existing) will return False instead of overwriting.
    :type overwrite: bool


    :return Bool: True if saving was successful. False if file exists and cannot override.
    """
    if os.path.exists("./config.bin"):
        if not overwrite: return False
        with open("./config.bin", 'w') as file:
            file.write(database_url.render_as_string(False))
    else:
        with open("./config.bin", 'x') as file:
            file.write(database_url.render_as_string(False))
    return True


def read_config() -> str | None:
    """
    Function for reading URL from saved config file.
    Returns *None* if file doesn't exist.

    :return: Returns url from config file or None if file doesn't exist.
    :rtype: str | None
    """
    if not os.path.exists("./config.bin"): return None
    with open("./config.bin", 'r') as file:
        database_url = file.readline()
    return database_url