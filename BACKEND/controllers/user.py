"""
WHAT: Handle user registration and login.
WHY: Create accounts and start secure sessions.
HOW: Use FastAPI, SQLModel, bcrypt, and JWT.
IMPORTANT: Never store or return plaintext passwords.
"""

import os

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Response
from fastapi import Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select as sqlMongoose

from config.DBsetup import getDatabaseSession
from models.user import User


# Load BACKEND/.env regardless of the working directory.
load_dotenv(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".env"
    )
)


# Register Controller ---------------------------------------------------------


# Validate incoming registration data.
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=8, max_length=128)


# Define the registration response.
class RegisterResponse(BaseModel):
    message: str
    user: dict[str, str]


def register(
    userData: RegisterRequest,
    databaseSession: Session = Depends(getDatabaseSession)
) -> RegisterResponse:

    # Clean incoming data.
    username = userData.username.strip()
    email = userData.email.strip().lower()

    # Validate username.
    if len(username) < 3 or len(username) > 30:
        raise HTTPException(
            status_code=400,
            detail="Username must be between 3 and 30 characters."
        )

    # Validate email.
    if (
        len(email) < 2
        or len(email) > 50
        or "@" not in email
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid email address."
        )

    # Validate password length.
    if len(userData.password) < 8 or len(userData.password) > 128:
        raise HTTPException(
            status_code=400,
            detail="Password must be between 8 and 128 characters."
        )

    # Convert password into bytes.
    passwordBytes = userData.password.encode("utf-8")

    # bcrypt supports a maximum of 72 password bytes.
    if len(passwordBytes) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password must not exceed 72 bytes."
        )

    # Stop duplicate emails before saving.
    existingEmail = databaseSession.exec(
        sqlMongoose(User).where(User.email == email)
    ).first()

    if existingEmail:
        raise HTTPException(
            status_code=409,
            detail="Email already exists."
        )

    # Stop duplicate usernames before saving.
    existingUsername = databaseSession.exec(
        sqlMongoose(User).where(User.username == username)
    ).first()

    if existingUsername:
        raise HTTPException(
            status_code=409,
            detail="Username already exists."
        )

    # Hash the password using bcrypt.
    hashed_password = bcrypt.hashpw(
        passwordBytes,
        bcrypt.gensalt()
    ).decode("utf-8")

    # Create the new user.
    new_user = User(
        username=username,
        email=email,
        passwordHash=hashed_password
    )

    # Save the user to SQLite.
    try:
        databaseSession.add(new_user)
        databaseSession.commit()
        databaseSession.refresh(new_user)

    except IntegrityError:
        databaseSession.rollback()

        raise HTTPException(
            status_code=409,
            detail="Username or email already exists."
        )

    # Registration does not create a login session; the user must log in separately.
    return RegisterResponse(
        message="User registered successfully. Please log in from the login page.",
        user={
            "_id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
    )


# Login Controller ------------------------------------------------------------


# Validate incoming login data.
class LoginRequest(BaseModel):
    email: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=1, max_length=128)


# Define the successful login response.
class LoginResponse(BaseModel):
    message: str
    user: dict[str, str]


# Log in an existing user.
def login(
    userData: LoginRequest,
    response: Response,
    databaseSession: Session = Depends(getDatabaseSession)
) -> LoginResponse:

    # Clean incoming email.
    email = userData.email.strip().lower()

    # Reject an invalid email before searching.
    if len(email) < 2 or len(email) > 50 or "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="Invalid email address."
        )

    # Convert the password once for bcrypt.
    passwordBytes = userData.password.encode("utf-8")

    # bcrypt cannot compare more than 72 bytes.
    if len(passwordBytes) > 72:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    # Read configuration from .env.
    jwtSecret = os.getenv("JWT_SECRET")
    jwtAlgorithm = os.getenv("JWT_ALGORITHM", "HS256")
    cookieSecure = os.getenv("COOKIE_SECURE", "false").lower() == "true"

    # Require a strong secret before signing.
    if not jwtSecret or len(jwtSecret) < 32:
        raise HTTPException(
            status_code=500,
            detail="JWT secret is not configured."
        )

    # Allow only secret-key JWT algorithms.
    if jwtAlgorithm not in {"HS256", "HS384", "HS512"}:
        raise HTTPException(
            status_code=500,
            detail="JWT algorithm is not configured correctly."
        )

    # Convert and validate the token lifetime.
    try:
        jwtExpireMinutes = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail="JWT expiry is not configured correctly."
        ) from error

    if jwtExpireMinutes <= 0:
        raise HTTPException(
            status_code=500,
            detail="JWT expiry is not configured correctly."
        )

    try:

        # Keep the database session on this thread.
        existing_user = databaseSession.exec(
            sqlMongoose(User).where(User.email == email)
        ).first()

        # Reject unknown email addresses.
        if not existing_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        # Compare the password with its saved hash.
        passwordMatches = bcrypt.checkpw(
            passwordBytes,
            existing_user.passwordHash.encode("utf-8")
        )

        if not passwordMatches:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        # Prepare JWT payload.
        currentTime = datetime.now(timezone.utc)

        tokenPayload = {
            "sub": existing_user.id,
            "iat": currentTime,
            "exp": currentTime + timedelta(
                minutes=jwtExpireMinutes
            )
        }

        # Generate signed JWT.
        accessToken = jwt.encode(
            tokenPayload,
            jwtSecret,
            algorithm=jwtAlgorithm
        )

        # Save JWT inside an HttpOnly browser cookie.
        response.set_cookie(
            key="accessToken",
            value=accessToken,
            httponly=True,
            secure=cookieSecure,
            samesite="lax",
            max_age=jwtExpireMinutes * 60,
            path="/"
        )

        # Return public user information.
        return LoginResponse(
            message="Login successful.",
            user={
                "_id": existing_user.id,
                "username": existing_user.username,
                "email": existing_user.email
            }
        )

    except HTTPException:
        raise

    except Exception as error:
        print(f"Login error: {type(error).__name__}")

        raise HTTPException(
            status_code=500,
            detail="Login failed."
        ) from error


# Logout Controller -----------------------------------------------------------


# Define the logout response.
class LogoutResponse(BaseModel):
    message: str


# Log out the user by deleting the JWT cookie.
async def logout(
    response: Response
) -> LogoutResponse:

    try:
        # Match the cookie settings used during login.
        cookieSecure = os.getenv("COOKIE_SECURE", "false").lower() == "true"

        # Remove the JWT cookie from the browser.
        response.delete_cookie(
            key="accessToken",
            path="/",
            httponly=True,
            secure=cookieSecure,
            samesite="lax"
        )

        return LogoutResponse(
            message="Logout successful."
        )

    except Exception as error:
        print(f"Logout error: {type(error).__name__}")

        raise HTTPException(
            status_code=500,
            detail="Logout failed."
        ) from error


# Me Controller ---------------------------------------------------------------


# Define the authenticated user response.
class MeResponse(BaseModel):
    message: str
    user: dict[str, str]


# Retrieve the currently logged-in user.
def me(
    request: Request,
    databaseSession: Session = Depends(getDatabaseSession)
) -> MeResponse:

    try:
        # Read the JWT from the browser cookie.
        accessToken = request.cookies.get("accessToken")

        if not accessToken:
            raise HTTPException(
                status_code=401,
                detail="Authentication required."
            )

        # Read JWT configuration from .env.
        jwtSecret = os.getenv("JWT_SECRET")
        jwtAlgorithm = os.getenv("JWT_ALGORITHM", "HS256")

        if not jwtSecret or len(jwtSecret) < 32:
            raise HTTPException(
                status_code=500,
                detail="JWT secret is not configured."
            )

        if jwtAlgorithm not in {"HS256", "HS384", "HS512"}:
            raise HTTPException(
                status_code=500,
                detail="JWT algorithm is not configured correctly."
            )

        # Verify the JWT signature and expiration.
        tokenPayload = jwt.decode(
            accessToken,
            jwtSecret,
            algorithms=[jwtAlgorithm],
            options={"require": ["sub", "iat", "exp"]}
        )

        # Retrieve the user identifier from the JWT.
        userId = tokenPayload["sub"]

        if not isinstance(userId, str) or not userId:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token."
            )

        # Find the user by primary key using SQLModel.
        existing_user = databaseSession.get(User, userId)

        if not existing_user:
            raise HTTPException(
                status_code=401,
                detail="User not found."
            )

        # Return public user information only.
        return MeResponse(
            message="User authenticated successfully.",
            user={
                "_id": existing_user.id,
                "username": existing_user.username,
                "email": existing_user.email
            }
        )

    except HTTPException:
        raise

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token."
        )

    except Exception as error:
        print(f"Me controller error: {type(error).__name__}")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve user."
        ) from error
