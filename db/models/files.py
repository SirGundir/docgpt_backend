import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import Relationship

from ..base_model import Model

class File_doc(Model):
    """
    Модель файла
    """
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
    user_id = Column(Integer, ForeignKey("users.id"))

    message = Relationship('Message', back_populates='file', cascade='all, delete-orphan')
    user = Relationship('User', back_populates='files')
