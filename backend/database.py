import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sleep_user:sleep_pass@postgres:5432/sleep_db"
)

engine = create_engine(DATABASE_URL)
