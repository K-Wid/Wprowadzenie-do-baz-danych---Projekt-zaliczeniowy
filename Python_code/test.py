import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from import_module import config
from import_module import import_from_openmeteo
from import_module import database


db_url = config.read_config()
if db_url is None:
    raise NotImplementedError("Please fill in database URL parameters.")
    db_url = URL.create(
        drivername="postgresql+psycopg2",
        username="",
        password="",
        host="",
        port=5432,
        database="",
    )
    config.save_config(db_url, True)
    db_url = config.read_config()

database.setup_engine(db_url)

database.add_location(40, 10, 30, "a")

database.insert_api_response_current_time()
