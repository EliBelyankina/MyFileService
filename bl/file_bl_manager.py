import zipfile
import os
import uuid
import io

from fastapi import UploadFile
from minio import Minio
from urllib.parse import quote
from io import BytesIO
from celery.result import AsyncResult
from fastapi import HTTPException
from app_config.settings import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME, CELERY_ADDRESS
from bl.auth_bl_manager import AuthBLManager
from datetime import datetime
from celery import Celery
from PIL import Image

from bl.db_manager import DBManager
from models.base_models import ImageOperation


class FileBLManager:
    auth_manager = AuthBLManager()
    db_manager = DBManager()

    def __init__(self):
        self.supported_extensions = ['.png', '.jpg', '.jpeg']

        self.minio_endpoint = MINIO_ENDPOINT
        self.minio_access_key = MINIO_ACCESS_KEY
        self.minio_secret_key = MINIO_SECRET_KEY
        self.minio_bucket_name = MINIO_BUCKET_NAME
        self.minio_client = Minio(self.minio_endpoint, self.minio_access_key, self.minio_secret_key, secure=False)

        if not self.minio_client.bucket_exists(self.minio_bucket_name):
            self.minio_client.make_bucket(self.minio_bucket_name)

    async def create_database_record(self, image_id, task_id, img_link, id_current_user):
        conn = await self.db_manager.connect_to_db()
        cur = conn.cursor()
        cur.execute("""
                INSERT INTO ImageTask (task_id,id_user, img_link, created_at)
                VALUES (%s, %s, %s, %s)
            """, (task_id, id_current_user, img_link, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        await self._commit_and_close_connection(conn, cur)

    async def _commit_and_close_connection(self, conn, cur):
        conn.commit()
        await self._close_connection(conn, cur)

    async def _close_connection(self, conn, cur):
        cur.close()
        conn.close()

    async def _open_conn_and_get_cur(self):
        conn = await self.db_manager.connect_to_db()
        cur = conn.cursor()
        return conn, cur

    async def save_file(self, file: UploadFile):
        # Проверка типа файла
        if not file.filename.endswith(tuple(self.supported_extensions)):
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Чтение содержимого файла
        file_content = await file.read()
        # Проверка, что file_content является байтами
        if not isinstance(file_content, bytes):
            raise HTTPException(status_code=500, detail="File content is not bytes")
        return file_content

    def upload_image_to_minio(self, image_id, file_content, file_name):
        """
        Загрузка изображения в MinIO
        :param image_id: id изображения
        :param file_content: содержимое изображения
        :param file_name: имя изображения
        :return: имя загруженного изображения
        """
        try:
            base_name, extension = os.path.splitext(file_name)
            unique_image_name = f"{image_id}_{quote(base_name)}_original{extension}"
            self.minio_client.put_object(self.minio_bucket_name, unique_image_name, BytesIO(file_content),
                                         len(file_content))
            return unique_image_name
        except Exception as e:
            raise Exception(f"Failed to upload image to MinIO: {str(e)}")

    async def process_image(self, file_content, file_name, operation):
        """
        Обработка изображения
        :param file_content: содержимое изображения
        :param file_name: имя изображения
        :param operation: название преобразования
        :return: преобразованное изображение
        """
        try:
            image = Image.open(io.BytesIO(file_content))
            image = await self.process_image_by_operation(image, operation)
            output = io.BytesIO()
            image.save(output, format='JPEG' if file_name.endswith('.jpg') or file_name.endswith('.jpeg') else 'PNG')
            output.seek(0)
            return output.read()
        except Exception as e:
            raise Exception(f"Failed to process image: {str(e)}")

    async def process_image_by_operation(self, image, operation):
        """
        Преобразование изображения по названию операции.
        :param image: изображение
        :param operation: операция/преобразование
        :return: изображение
        """
        if ImageOperation.rotated in operation:
            image = image.rotate(90, expand=True)
        if ImageOperation.gray in operation:
            image = image.convert('L')
        if ImageOperation.scaled in operation:
            new_size = (image.width * 2, image.height * 2)
            image = image.resize(new_size)
        return image

    async def upload_image(self, file: UploadFile, operation: str, data_current_user: str):
        """
        Загрузка изображения в MinIO и создание записи в базе данных
        :param file: загруженное изображение
        :param operation: операция/преобразование
        :param data_current_user: данные о текущем юзере
        """
        file_content = await self.save_file(file)
        processed_image_content = await self.process_image(file_content, file.filename, operation)
        image_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        img_link = self.upload_image_to_minio(image_id, processed_image_content, file.filename)
        await self.create_database_record(image_id, task_id, img_link, data_current_user)
        return {"message": "Image upload task created", "image_id": image_id, "task_id": task_id}

    async def get_history_by_id_user(self, data_current_user: str) -> dict:
        """
        Возвращает историю загруженных и преобразованных пользователем изображений
        :param data_current_user: данные о текущем юзере
        :return: историю пользователя
        """
        try:
            conn, cur = await self._open_conn_and_get_cur()
            cur.execute("""
                SELECT task_id FROM ImageTask WHERE id_user = %s
            """, (data_current_user,))
            await self._close_connection(conn, cur)
            history = [user_id[0] for user_id in cur.fetchall()]
            return {f"history for user with id {data_current_user}": history}
        except Exception as e:
            # Обработка исключения
            print(f"An error occurred: {e}")
            raise

    async def get_zip_by_id_task(self, task_id):
        """
        Возвращает ZIP-файл с изображением, преобразованным пользователем
        :param task_id: id задачи
        :return: zip архив с изображением
        """
        try:
            conn = await self.db_manager.connect_to_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT img_link FROM ImageTask WHERE task_id = %s
            """, (task_id,))

            img_link = cur.fetchone()[0]
            await self._close_connection(conn, cur)
            image_content = await self.get_image_from_minio(img_link)
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                zip_file.writestr(img_link, image_content)
            zip_buffer.seek(0)
            return zip_buffer.read()
        except Exception as e:
            print(f"An error occurred: {e}")
            raise

    async def get_image_from_minio(self, image_name: str):
        """
        Получает изображение из MinIO
        :param image_name: имя изображения
        :return: данные изображения
        """
        try:
            response = self.minio_client.get_object(self.minio_bucket_name, image_name)
            image_content = response.read()
            return image_content
        except Exception as e:
            raise Exception(f"Failed to get image from MinIO: {str(e)}")

    async def get_task_status(self, task_id):
        """
        Возвращает статус задачи
        :param task_id: id задачи
        :return: статус по задаче
        """
        celery_app = Celery('tasks', broker=CELERY_ADDRESS, backend=CELERY_ADDRESS)
        try:
            task = AsyncResult(task_id, app=celery_app)
            status = task.status
            if status == 'FAILURE':
                raise HTTPException(status_code=500, detail=task.error)
            return {"status": status}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
