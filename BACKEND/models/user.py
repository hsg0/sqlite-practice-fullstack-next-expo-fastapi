"""
WHAT: Define the users table and account request data.
WHY: Store accounts and validate registration and login input.
HOW: Use SQLModel for SQLite and Pydantic validation.
IMPORTANT: The stored password value must always be a hash.
"""

import uuid as nanoID

from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "webUsers"

    id: str = Field(
        default_factory=lambda: str(nanoID.uuid4()),
        sa_column=Column("_id", String, primary_key=True),
    )
    username: str = Field(
        sa_column=Column("username", String, unique=True, nullable=False),
    )
    email: str = Field(
        sa_column=Column("email", String, unique=True, nullable=False),
    )
    passwordHash: str = Field(
        sa_column=Column("password", String, nullable=False),
    )


class UserCredentials(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=8, max_length=128)
