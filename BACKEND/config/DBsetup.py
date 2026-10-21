
"""
WHAT: Configure the SQLite database.
WHY: Share one database engine across the backend.
HOW: Connect SQLModel to DATABASE/practice.db.
IMPORTANT: Keep database access in the backend.
"""

import os
from sqlalchemy import inspect
from sqlmodel import SQLModel, Session, create_engine


# Find the project's root directory.
projectRoot = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

# Locate the SQLite database file.
databaseFile = os.path.join(
    projectRoot,
    "DATABASE",
    "practice.db"
)

# Create the database engine.
databaseEngine = create_engine(
    f"sqlite:///{databaseFile}"
)


# Create missing database tables.
def createDatabaseTables():
    from models.user import PasswordResetCode, User

    # Create tables that do not already exist.
    databaseInspector = inspect(databaseEngine)
    if databaseInspector.has_table(User.__tablename__):
        userColumns = {
            column["name"]
            for column in databaseInspector.get_columns(User.__tablename__)
        }
        if "email" not in userColumns:
            with databaseEngine.begin() as databaseConnection:
                databaseConnection.exec_driver_sql(
                    'ALTER TABLE "webUsers" ADD COLUMN "email" VARCHAR'
                )

    SQLModel.metadata.create_all(databaseEngine)


# Open a database session for API requests.
def getDatabaseSession():

    # Automatically close the session after use.
    with Session(databaseEngine) as databaseSession:
        yield databaseSession
