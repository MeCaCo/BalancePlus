from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "income" или "expense"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL = общая категория
    is_default = Column(Boolean, default=False)

    # Связи
    user = relationship("User", backref="categories")
    transactions = relationship("Transaction", back_populates="category")