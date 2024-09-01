from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette.status import HTTP_401_UNAUTHORIZED

from datetime import datetime, timedelta
from typing import Optional
import uvicorn

from routers.image_service_routers import router

app = FastAPI()
app.include_router(router)



if __name__ == "__main__":

    uvicorn.run("main:app", host="127.0.0.1", port=8000)