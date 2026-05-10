from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.presentation.dependencies import get_register_handler, get_login_handler
from app.presentation.dto.auth_dto import RegisterRequest, LoginRequest, TokenResponse
from app.application.commands.auth_commands import (
    RegisterUserCommand,
    LoginUserCommand,
    RegisterUserCommandHandler,
    LoginUserCommandHandler,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    handler: RegisterUserCommandHandler = Depends(get_register_handler),
    db: AsyncSession = Depends(get_db),
):
    command = RegisterUserCommand(
        username=data.username, email=data.email, password=data.password
    )
    user_id = await handler.handle(command)
    await db.commit()
    return {"id": user_id}


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    handler: LoginUserCommandHandler = Depends(get_login_handler),
):
    command = LoginUserCommand(username=data.username, password=data.password)
    token = await handler.handle(command)
    return TokenResponse(access_token=token)
