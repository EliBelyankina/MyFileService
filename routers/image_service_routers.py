from enum import Enum

from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import Response
from bl.auth_bl_manager import AuthBLManager, RegistrationRequest,LoginRequest
from bl.file_bl_manager import FileBLManager, ImageOperation
from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
router = APIRouter()
auth_manager = AuthBLManager()
file_manager = FileBLManager()


@router.post("/login", response_model=dict)
async def login(login_request: LoginRequest):
    return await auth_manager.login(login_request)

@router.post("/registration", response_model=dict)
async def registration(registration_request: RegistrationRequest):
    return await auth_manager.register_user(registration_request)





# Пример использования с Depends
@router.post("/upload", response_model=dict)
async def upload(auth_token: str , operation: str, file: UploadFile = File(...),):
    try:
        data_current_user = await auth_manager.get_current_user_id(auth_token)

        # Удаление пробелов из каждого элемента списка
        operations = [op.strip() for op in operation.split(',')]
        return await file_manager.upload_image(file,operations,data_current_user)
    except HTTPException as e:
        raise e



@router.get("/status/", response_model=dict)
async def get_task_status(auth_token: str,id_task: str):
    try:
        data_current_user = await auth_manager.get_current_user_id(auth_token)
        return await file_manager.get_task_status(id_task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history_by_current_user/", response_model=dict)
async def get_history_by_token(auth_token: str):
    try:
        data_current_user = await auth_manager.get_current_user_id(auth_token)
        return await file_manager.get_history_by_id_user(data_current_user)
    except HTTPException as e:
        raise e

@router.get("/history/{user_id}", response_model=dict)
async def get_history_by_token(auth_token: str, user_id: str):
    try:
        data_current_user = await auth_manager.get_current_user_id(auth_token)
        return await file_manager.get_history_by_id_user(user_id)
    except HTTPException as e:
        raise e

@router.get("/task/", response_class=Response)
async def get_task(auth_token: str, id_task: str):
    try:
        data_current_user = await auth_manager.get_current_user_id(auth_token)
        zip_content = await file_manager.get_zip_by_id_task(id_task)
        return Response(content=zip_content, media_type="application/zip", headers={
            "Content-Disposition": f"attachment; filename={id_task}.zip"
        })
    except HTTPException as e:
        raise e

