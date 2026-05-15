from app.inventory.domain.models.user import User
from app.inventory.domain.models.value_objects import Email
from app.inventory.infrastructure.orm_models import UserEntity


class UserMapper:
    @staticmethod
    def to_domain(entity: UserEntity) -> User:
        return User(
            _id=entity.id,
            _username=entity.username,
            _email=Email(entity.email),
            _hashed_password=entity.hashed_password,
            _created_at=entity.created_at,
        )

    @staticmethod
    def to_entity(user: User) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email.value,
            "hashed_password": user.hashed_password,
        }
