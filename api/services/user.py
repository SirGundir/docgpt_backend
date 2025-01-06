from datetime import datetime, timedelta
import string
import random
from passlib.hash import pbkdf2_sha512
from fastapi import HTTPException
from pydantic import BaseModel, EmailStr

from api.services.base import BaseService
from api.db.models import User
from api.utils import generate_token
from config import settings



class UserService:
    """
    Пользовательский CRUD+ менеджер
    """
    def __init__(self):
        self.model = User

    @staticmethod
    async def generate_user_dict(user: User) -> dict:
        """
        Генерация информации о пользователе в виде словаря 
        """
        if not user:
            return {}
        return {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'password_hash': user.password_hash,
            'is_blocked': user.is_blocked,
            'created': user.created_at.strftime(format=settings.date_time_format)
        }

    async def create(self, name: str, email: str, password) -> dict:
        if await BaseService().get(self.model, email=email):
            return HTTPException(
                status_code=400,
                detail='User already exists'
            )
        await BaseService().create(
            self.model,
            email=email,
            name=name,
            password_hash=pbkdf2_sha512.hash(password),
        )
        return {
            'status': 'ok'
        }


    async def get(self, user: User, id: int):
        """
        Получение информации о пользователе для бэкенда
        """
        user_db = await BaseService().get(self.model, id=id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail='User not found',
            )
        if user_db.id != user.id:
            raise HTTPException(
                status_code=401,
                detail='Cannot access to this user with your session',
            )
        return {
            'status': 'ok',
            'user': await UserService().generate_user_dict(user=user_db)
        }

    async def login(self, email: str, password: str):
        """
        Авторизация (проверка пароля)
        """
        user = await BaseService().get(self.model, email=email)
        if not user:
            raise HTTPException(
                status_code=404,
                detail='User was not found'
            )
        # Проверка на блок
        if user.is_blocked:
            raise HTTPException(
                status_code=401,
                detail='You are banned'
            )
        if not pbkdf2_sha512.verify(password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail='Wrong password'
            )
        # Генерация одноразового кода
        code = "".join(random.choices(string.digits, k=6)) 
        expiration = datetime.now() + timedelta(minutes=15)
        # TODO: отправлять отсюда код на почту
        await BaseService().update(user, last_code=code, code_expiration=expiration)
        return {
            'status': 'ok',
            'detail': 'Code is sent'
        }

    async def verify_code(self, email: str, code: str):
        """
        Верификация пользователя (проверка кода + генерация токена)
        """
        user = await BaseService().get(self.model, email=email)
        if not user:
            raise HTTPException(
                status_code=404,
                detail='User was not found'
            )
        # Проверка на наличие кода
        if not user.last_code:
            raise HTTPException(
                status_code=404,
                detail='You did not try to log in'
            )
        current_code = user.last_code
        expiration_time = user.code_expiration
        # Обнуление текущего кода
        await BaseService().update(user, last_code=None, code_expiration=None)
        # Проверка времени действия кода 
        if datetime.now() > expiration_time:
            raise HTTPException(
                status_code=401,
                detail='Code has been expired, request new please'
            )
        # Проверка соответствия кода
        if current_code != code:
            raise HTTPException(
                status_code=401,
                detail='Wrong code'
            )
        return {
            'status': 'ok',
            'token': generate_token(email=email),
            'user_id': user.id,
            'name': user.name
        }
