import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_connection() -> psycopg.Connection:
    return psycopg.connect(os.environ["DATABASE_URL"])
