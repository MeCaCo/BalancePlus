from typing import TypeVar, Generic, List, Optional
from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType")

class BaseService(Generic[ModelType]):
    def __init__(self, repository: BaseRepository[ModelType]):
        self.repository = repository

    def get_by_id(self, id: int) -> Optional[ModelType]:
        return self.repository.get_by_id(id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return self.repository.get_all(skip, limit)

    def create(self, **kwargs) -> ModelType:
        return self.repository.create(**kwargs)

    def delete(self, obj: ModelType) -> None:
        self.repository.delete(obj)