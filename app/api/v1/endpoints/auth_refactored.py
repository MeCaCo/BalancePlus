from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserCreate, User as UserOut
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService

router = APIRouter()

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    repository = UserRepository(db)
    return UserService(repository)

@router.post("/register", response_model=UserOut)
def register(user_data: UserCreate, service: UserService = Depends(get_user_service)):
    return service.register(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service)
):
    user = service.authenticate(form_data.username, form_data.password)
    return service.create_access_token_for_user(user)