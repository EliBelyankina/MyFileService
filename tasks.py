import logging

from models.base_models import ImageModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from datetime import datetime

from celery import Celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from bl.file_bl_manager import FileBLManager

app = Celery('tasks', broker='redis://localhost:6379/0')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=create_engine('postgresql://postgres:postgres@localhost:5432/postgres'))


@app.task
def upload_image_to_minio(image_id, file_content, file_name):
    logger.info(f"Starting task upload_image_to_minio with image_id {image_id}")
    try:
        manager = FileBLManager()
        result = manager.upload_image_to_minio(image_id, file_content, file_name)
        logger.info(f"Finished task upload_image_to_minio with result {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to upload image to MinIO: {str(e)}")
        raise

@app.task
def create_database_record(image_id, task_id, img_link):
    logger.info(f"Starting task create_database_record with image_id {image_id}")
    try:
        db_session = SessionLocal()
        record = ImageModel(id=image_id, task_id=task_id, img_link=img_link, created_at=datetime.now())
        db_session.add(record)
        db_session.commit()
        logger.info(f"Finished task create_database_record")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to create database record: {e}")
        raise
    finally:
        db_session.close()