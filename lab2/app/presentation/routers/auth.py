from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.presentation.dependencies import get_register_use_case, get_login_use_case
from app.presentation.dto.auth_dto import (
    UserCreateRequest,
    LoginRequest,
    UserResponse,
    TokenResponse,
)
from app.application.use_cases.auth_use_cases import RegisterUserUseCase, LoginUserUseCase
from app.infrastructure.repositories.postgres_user_repo import PostgresUserRepository
from app.infrastructure.mappers.user_mapper import UserMapper
from app.infrastructure.orm_models import UserEntity

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreateRequest,
    use_case: RegisterUserUseCase = Depends(get_register_use_case),
    db: AsyncSession = Depends(get_db),
):
    user_id = await use_case.execute(
        username=data.username,
        email=data.email,
        password=data.password,
    )
    await db.commit()

    entity = await db.get(UserEntity, user_id)
    return UserResponse(
        id=entity.id,
        username=entity.username,
        email=entity.email,
        created_at=entity.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    use_case: LoginUserUseCase = Depends(get_login_use_case),
):
    token = await use_case.execute(
        username=data.username,
        password=data.password,
    )
    return TokenResponse(access_token=token)
