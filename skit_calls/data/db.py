import os
from typing import Optional

import psycopg2 as pg

from skit_calls import constants as const


def postgres(
    host: Optional[str] = os.environ[const.DB_HOST],
    port: Optional[str] = os.environ[const.DB_PORT],
    user: Optional[str] = os.environ[const.DB_USER],
    password: Optional[str] = os.environ[const.DB_PASSWORD],
    db_name: Optional[str] = os.environ[const.DB_NAME],
):
    def query(fn):
        def on_connect():
            with pg.connect(
                host=host, port=port, user=user, password=password, dbname=db_name
            ) as conn:
                return fn(conn)

        return on_connect

    return query


def connect(
    host: Optional[str] = os.environ[const.DB_HOST],
    port: Optional[str] = os.environ[const.DB_PORT],
    user: Optional[str] = os.environ[const.DB_USER],
    password: Optional[str] = os.environ[const.DB_PASSWORD],
    db_name: Optional[str] = os.environ[const.DB_NAME],
):
    return pg.connect(
        host=host, port=port, user=user, password=password, dbname=db_name
    )
