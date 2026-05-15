from fastapi import APIRouter, Depends, status

from app.inventory.presentation.dto.auth_dto import RegisterRequest, LoginRequest, TokenResponse
from app.inventory.presentation.dependencies import get_register_handler, get_login_handler
from app.inventory.application.commands.auth_commands import (
    RegisterUserCommandHandler, LoginUserCommandHandler,
    RegisterUserCommand, LoginUserCommand,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    handler: RegisterUserCommandHandler = Depends(get_register_handler),
):
    user_id = await handler.handle(RegisterUserCommand(
        username=body.username, email=body.email, password=body.password,
    ))
    return {"id": user_id, "username": body.username}


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    handler: LoginUserCommandHandler = Depends(get_login_handler),
):
    token = await handler.handle(LoginUserCommand(
        username=body.username, password=body.password,
    ))
    return TokenResponse(access_token=token)
