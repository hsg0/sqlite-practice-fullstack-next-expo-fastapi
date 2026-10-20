"""
WHAT: Define the user API routes.
WHY: Connect HTTP requests to user controllers.
HOW: Use FastAPI's APIRouter, similar to Express.
IMPORTANT: Database logic belongs in controllers.
"""

from fastapi import APIRouter

from controllers.user import (
    register,
    RegisterResponse,
    login,
    LoginResponse,
    logout,
    LogoutResponse,
    me,
    MeResponse,
)


userRouter = APIRouter(prefix="/api/users", tags=["Users"])

userRouter.post("/register", status_code=201, response_model=RegisterResponse)(register)
userRouter.post("/login", response_model=LoginResponse)(login)
userRouter.post("/logout", response_model=LogoutResponse)(logout)
userRouter.get("/me", response_model=MeResponse)(me)
