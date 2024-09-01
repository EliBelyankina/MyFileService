from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from datetime import datetime
import uuid
import hashlib

from app_config.settings import  SECRET_KEY, ALGORITHM
from bl.db_manager import DBManager
from models.base_models import LoginRequest, RegistrationRequest


class AuthBLManager:
    def __init__(self):
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
        self.db_manager = DBManager()

    async def _connect_to_db(self):
        """Подключение к базе данных."""
        return await self.db_manager.connect_to_db()

    async def _execute_query(self, conn, query, params):
        """Выполнение SQL-запроса."""
        cur = conn.cursor()
        cur.execute(query, params)
        if query.upper().startswith("SELECT"):
            return cur.fetchone()
        else:
            return None

    async def _commit_and_close(self, conn):
        """Сохранение изменений и закрытие соединения."""
        conn.commit()
        cur = conn.cursor()
        cur.close()
        conn.close()

    async def authenticate_user(self, username: str, password: str) -> str:
        """Аутентификация пользователя."""
        conn = await self._connect_to_db()
        user_data = await self._execute_query(conn, "SELECT id, password FROM users WHERE email = %s", (username,))
        if user_data is None:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        user_id, stored_password = user_data
        if hashlib.sha256(password.encode()).hexdigest() != stored_password:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        await self._commit_and_close(conn)
        return user_id

    async def generate_jwt_token(self, id_user: str) -> str:
        """Генерация JWT-токена."""
        payload = {"id_user": id_user}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    async def login(self, login_request: LoginRequest) -> dict:
        """Авторизация пользователя."""
        user_id = await self.authenticate_user(login_request.username, login_request.password)
        token = await self.generate_jwt_token(user_id)
        return {"access_token": token, "token_type": "bearer"}

    async def register_user(self, registration_request: RegistrationRequest) -> dict:
        """Регистрация нового пользователя."""
        conn = await self._connect_to_db()
        cur = conn.cursor()

        if await self._execute_query(conn, "SELECT * FROM users WHERE email = %s", (registration_request.email,)) is not None:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        user_id = str(uuid.uuid4())
        hashed_password = hashlib.sha256(registration_request.password.encode()).hexdigest()
        await self._execute_query(conn, """
            INSERT INTO users (id, email, password, created_at, first_name, last_name)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, registration_request.email, hashed_password, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              registration_request.first_name, registration_request.last_name))

        await self._commit_and_close(conn)

        token = await self.generate_jwt_token(registration_request.email)

        return {"message": "User created successfully", "access_token": token, "token_type": "bearer"}

    async def get_current_user_id(self, token: str) -> str:
        """Получение ID текущего пользователя по токену."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            id_user: str = payload.get("id_user")
            if id_user is None:
                raise HTTPException(status_code=401, detail="Could not validate credentials")
            return id_user
        except JWTError:
            raise HTTPException(status_code=401, detail="Could not validate credentials")