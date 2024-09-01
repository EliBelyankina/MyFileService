from enum import Enum

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2
from jose import jwt, JWTError
from pydantic import BaseModel
from datetime import datetime
import uuid
import hashlib
import psycopg2

from app_config.settings import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, SECRET_KEY, ALGORITHM
import zipfile

import os

from sqlalchemy import  Column, String, DateTime

from sqlalchemy.orm import declarative_base
from enum import Enum
from pydantic import BaseModel

Base = declarative_base()
class RegistrationRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ImageOperation(str, Enum):
    original = "original"
    rotated = "rotated"
    gray = "gray"
    scaled = "scaled"


class ImageModel(Base):
    __tablename__ = "ImageTask"
    id = Column(String, primary_key=True)
    task_id = Column(String)
    img_link = Column(String)
    created_at = Column(DateTime)

