import pytest
from fastapi import HTTPException

from jose import jwt, JWTError

from bl.auth_bl_manager import SECRET_KEY, ALGORITHM, AuthBLManager


@pytest.mark.asyncio
async def test_get_current_user_id_valid_token():
    print("Starting test_get_current_user_id_valid_token")
    # Создание валидного токена
    payload = {"id_user": "12345"}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Создание экземпляра класса
    instance = AuthBLManager()

    # Вызов метода и проверка результата
    user_id = await instance.get_current_user_id(token)
    assert user_id == "12345"

@pytest.mark.asyncio
async def test_get_current_user_id_invalid_token():
    print("Starting test_get_current_user_id_invalid_token")
    # Создание невалидного токена
    token = "invalid_token"

    # Создание экземпляра класса
    instance = AuthBLManager()

    # Вызов метода и проверка исключения
    with pytest.raises(HTTPException) as http_exc:
        await instance.get_current_user_id(token)
    assert http_exc.value.status_code == 401
    assert http_exc.value.detail == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_current_user_id_missing_id_user():
    print("Starting test_get_current_user_id_missing_id_user")
    # Создание токена без id_user
    payload = {}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Создание экземпляра класса
    instance = AuthBLManager()

    # Вызов метода и проверка исключения
    with pytest.raises(HTTPException) as http_exc:
        await instance.get_current_user_id(token)
    assert http_exc.value.status_code == 401
    assert http_exc.value.detail == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_current_user_id_jwt_error():
    print("Starting test_get_current_user_id_jwt_error")
    # Создание токена с неверным ключом или алгоритмом
    payload = {"id_user": "12345"}
    token = jwt.encode(payload, "wrong_secret_key", algorithm=ALGORITHM)

    # Создание экземпляра класса
    instance = AuthBLManager()

    # Вызов метода и проверка исключения
    with pytest.raises(HTTPException) as http_exc:
        await instance.get_current_user_id(token)
    assert http_exc.value.status_code == 401
    assert http_exc.value.detail == "Could not validate credentials"