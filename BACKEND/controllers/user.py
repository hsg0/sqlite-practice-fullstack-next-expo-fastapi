"""
WHAT: Handle registration, login, and password recovery.
WHY: Create accounts, recover access, and start secure sessions.
HOW: Use FastAPI, SQLModel, bcrypt, and JWT.
IMPORTANT: Never store or return plaintext passwords.
"""

import os
import hashlib
import hmac
import secrets

from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
import jwt

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Response
from fastapi import Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select as sqlMongoose

from config.DBsetup import getDatabaseSession
from models.user import PasswordResetCode, User


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


# Password Reset Controller ---------------------------------------------------


# Validate the email that receives a reset code.
class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=2, max_length=50)


# Return the same message for every valid email format.
class PasswordResetRequestResponse(BaseModel):
    message: str


# Validate the email and six-digit code.
class PasswordResetVerifyRequest(BaseModel):
    email: str = Field(min_length=2, max_length=50)
    otp: str = Field(min_length=6, max_length=6)


# Return a limited token after OTP verification.
class PasswordResetVerifyResponse(BaseModel):
    message: str
    resetToken: str


# Validate the final password reset request.
class PasswordResetConfirmRequest(BaseModel):
    email: str = Field(min_length=2, max_length=50)
    resetToken: str = Field(min_length=32, max_length=200)
    password: str = Field(min_length=8, max_length=128)


# Confirm that the password was changed.
class PasswordResetConfirmResponse(BaseModel):
    message: str


# Create a protected digest for a reset value.
def createPasswordResetDigest(email: str, value: str) -> str:
    jwtSecret = os.getenv("JWT_SECRET")

    if not jwtSecret or len(jwtSecret) < 32:
        raise HTTPException(
            status_code=500,
            detail="JWT secret is not configured."
        )

    resetValue = f"{email}:{value}".encode("utf-8")

    return hmac.new(
        jwtSecret.encode("utf-8"),
        resetValue,
        hashlib.sha256
    ).hexdigest()


# Remove older reset attempts for one email.
def deletePasswordResetCodes(
    email: str,
    databaseSession: Session
) -> None:
    resetCodes = databaseSession.exec(
        sqlMongoose(PasswordResetCode).where(
            PasswordResetCode.email == email
        )
    ).all()

    for resetCode in resetCodes:
        databaseSession.delete(resetCode)


# Create a six-digit reset code.
def requestPasswordReset(
    userData: PasswordResetRequest,
    databaseSession: Session = Depends(getDatabaseSession)
) -> PasswordResetRequestResponse:
    email = userData.email.strip().lower()

    if len(email) < 2 or len(email) > 50 or "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="Invalid email address."
        )

    existing_user = databaseSession.exec(
        sqlMongoose(User).where(User.email == email)
    ).first()

    # Generate securely even when no account matches.
    resetCode = f"{secrets.randbelow(1_000_000):06d}"
    codeDigest = createPasswordResetDigest(email, resetCode)

    if existing_user:
        currentTimestamp = int(datetime.now(timezone.utc).timestamp())
        recentReset = databaseSession.exec(
            sqlMongoose(PasswordResetCode).where(
                PasswordResetCode.email == email
            )
        ).first()

        # Limit each account to one new code per minute.
        if (
            recentReset
            and recentReset.createdAt > currentTimestamp - 60
        ):
            return PasswordResetRequestResponse(
                message="If an account matches that email, a reset code has been sent."
            )

        deletePasswordResetCodes(email, databaseSession)

        databaseSession.add(
            PasswordResetCode(
                email=email,
                codeDigest=codeDigest,
                createdAt=currentTimestamp,
                expiresAt=currentTimestamp + 600
            )
        )
        databaseSession.commit()

        # Development only: replace this with email delivery.
        print(f"Password reset code for {email}: {resetCode}")

    return PasswordResetRequestResponse(
        message="If an account matches that email, a reset code has been sent."
    )


# Verify the OTP and create a limited reset token.
def verifyPasswordResetCode(
    userData: PasswordResetVerifyRequest,
    databaseSession: Session = Depends(getDatabaseSession)
) -> PasswordResetVerifyResponse:
    email = userData.email.strip().lower()
    resetCode = userData.otp.strip()

    if not resetCode.isdigit() or len(resetCode) != 6:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset code."
        )

    resetRecord = databaseSession.exec(
        sqlMongoose(PasswordResetCode).where(
            PasswordResetCode.email == email
        )
    ).first()

    currentTimestamp = int(datetime.now(timezone.utc).timestamp())

    if (
        not resetRecord
        or resetRecord.expiresAt < currentTimestamp
        or resetRecord.failedAttempts >= 5
        or resetRecord.resetTokenDigest is not None
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset code."
        )

    submittedDigest = createPasswordResetDigest(email, resetCode)

    if not hmac.compare_digest(
        submittedDigest,
        resetRecord.codeDigest
    ):
        resetRecord.failedAttempts += 1
        databaseSession.add(resetRecord)
        databaseSession.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset code."
        )

    resetToken = secrets.token_urlsafe(32)
    resetRecord.resetTokenDigest = createPasswordResetDigest(
        email,
        resetToken
    )
    resetRecord.expiresAt = currentTimestamp + 600
    databaseSession.add(resetRecord)
    databaseSession.commit()

    return PasswordResetVerifyResponse(
        message="Reset code verified.",
        resetToken=resetToken
    )


# Change the password after OTP verification.
def confirmPasswordReset(
    userData: PasswordResetConfirmRequest,
    databaseSession: Session = Depends(getDatabaseSession)
) -> PasswordResetConfirmResponse:
    email = userData.email.strip().lower()
    passwordBytes = userData.password.encode("utf-8")

    if len(passwordBytes) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password must not exceed 72 bytes."
        )

    resetRecord = databaseSession.exec(
        sqlMongoose(PasswordResetCode).where(
            PasswordResetCode.email == email
        )
    ).first()

    currentTimestamp = int(datetime.now(timezone.utc).timestamp())

    if (
        not resetRecord
        or not resetRecord.resetTokenDigest
        or resetRecord.expiresAt < currentTimestamp
    ):
        raise HTTPException(
            status_code=400,
            detail="Password reset authorization is invalid or expired."
        )

    submittedDigest = createPasswordResetDigest(
        email,
        userData.resetToken
    )

    if not hmac.compare_digest(
        submittedDigest,
        resetRecord.resetTokenDigest
    ):
        raise HTTPException(
            status_code=400,
            detail="Password reset authorization is invalid or expired."
        )

    existing_user = databaseSession.exec(
        sqlMongoose(User).where(User.email == email)
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=400,
            detail="Password reset authorization is invalid or expired."
        )

    existing_user.passwordHash = bcrypt.hashpw(
        passwordBytes,
        bcrypt.gensalt()
    ).decode("utf-8")

    databaseSession.add(existing_user)
    databaseSession.delete(resetRecord)
    databaseSession.commit()

    return PasswordResetConfirmResponse(
        message="Password reset successful. Please log in."
    )


# Login Controller ------------------------------------------------------------


# Validate incoming login data.
class LoginRequest(BaseModel):
    email: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=1, max_length=128)

    # Select token transport; this does not prove client identity.
    clientType: Literal["web", "mobile"]


# Define the successful login response.
class LoginResponse(BaseModel):
    message: str
    user: dict[str, str]

    # Only mobile receives the JWT in JSON.
    accessToken: str | None = None


# Log in an existing user.
def login(
    userData: LoginRequest,
    response: Response,
    databaseSession: Session = Depends(getDatabaseSession)
) -> LoginResponse:

    # Clean incoming email.
    email = userData.email.strip().lower()

    # Validate email.
    if len(email) < 2 or len(email) > 50 or "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="Invalid email address."
        )

    # Convert password to bytes.
    passwordBytes = userData.password.encode("utf-8")

    if len(passwordBytes) > 72:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    # Read environment configuration.
    jwtSecret = os.getenv("JWT_SECRET")
    jwtAlgorithm = os.getenv("JWT_ALGORITHM", "HS256")
    cookieSecure = os.getenv("COOKIE_SECURE", "false").lower() == "true"

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
        # Find user in SQLite using SQLModel.
        existing_user = databaseSession.exec(
            sqlMongoose(User).where(User.email == email)
        ).first()

        if existing_user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        # Verify password using bcrypt.
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

        # Web: store JWT in an HttpOnly cookie.
        if userData.clientType == "web":
            response.set_cookie(
                key="accessToken",
                value=accessToken,
                httponly=True,
                secure=cookieSecure,
                samesite="lax",
                max_age=jwtExpireMinutes * 60,
                path="/"
            )

        # Mobile: return the JWT for Expo SecureStore.
        return LoginResponse(
            message="Login successful.",
            user={
                "_id": existing_user.id,
                "username": existing_user.username,
                "email": existing_user.email
            },
            accessToken=(
                accessToken
                if userData.clientType == "mobile"
                else None
            )
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


# Log out a web user by deleting the JWT cookie.
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


# Read the JWT from web cookies or mobile headers.
def getAccessToken(request: Request) -> str:

    # Read JWT from the browser cookie.
    accessToken = request.cookies.get("accessToken")

    # Mobile: Read JWT from Authorization header.
    if not accessToken:
        authorizationHeader = request.headers.get(
            "Authorization", ""
        )

        if authorizationHeader.startswith("Bearer "):
            accessToken = authorizationHeader[7:].strip()

    if accessToken:
        return accessToken

    raise HTTPException(
        status_code=401,
        detail="Authentication required."
    )


# Retrieve the currently logged-in user.
def me(
    request: Request,
    databaseSession: Session = Depends(getDatabaseSession)
) -> MeResponse:

    try:
        # Accept web cookie or mobile Bearer authentication.
        accessToken = getAccessToken(request)

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
