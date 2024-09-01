import os

IMAGE_SERVICE_HOST = os.getenv('IMAGE_SERVICE_HOST', '0.0.0.0')
IMAGE_SERVICE_PORT = os.getenv('IMAGE_SERVICE_PORT', 11111)

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', '192.168.0.103:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'access_key')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'secret_key')
MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'imageservice')

CELERY_ADDRESS = os.getenv('CELERY_ADDRESS', 'redis://localhost:6379/0')