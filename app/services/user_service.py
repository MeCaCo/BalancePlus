from app.repositories.user_repository import UserRepository
from app.services.base import BaseService
from app.models.user import User
from app.core.security import get_password_hash, verify_password
from fastapi import HTTPException, status
from datetime import timedelta
from app.core.config import settings
from app.core.security import create_access_token

class UserService(BaseService[User]):
    def __init__(self, repository: UserRepository):
        super().__init__(repository)
        self.repository = repository

    def get_by_username(self, username: str):
        return self.repository.get_by_username(username)

    def get_by_email(self, email: str):
        return self.repository.get_by_email(email)

    def register(self, username: str, email: str, password: str) -> User:
        # Проверяем, существует ли пользователь
        existing = self.repository.get_by_username_or_email(username, email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )

        # Хешируем пароль и создаём пользователя
        hashed_password = get_password_hash(password)
        return self.create(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True
        )

    def authenticate(self, username: str, password: str) -> User:
        user = self.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    def create_access_token_for_user(self, user: User) -> dict:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }