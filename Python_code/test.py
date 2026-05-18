import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from import_module import config
from import_module import import_from_openmeteo
from import_module import database


db_url = config.read_config()
if not isinstance(db_url, URL):
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


# database.destroy_all_tables()
# database.create_all_tables()
# quit()


database.add_location(database.Location("Bermuda triangle", 25, 70, 20))
database.add_location(database.Location("Sth", 75, 20, 20))

e = database.insert_api_response_current_time(database.get_all_locations())

for id, (location, status) in e.items():
    print(id, location.name, status)