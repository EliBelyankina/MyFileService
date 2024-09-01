# Используем базовый образ Python
FROM python:3.9-slim

# Копируем файлы в контейнер
COPY . /app

# Установка зависимостей
WORKDIR /app
RUN pip install -r requirements.txt

# Установка переменных окружения
ENV SECRET_KEY=${SECRET_KEY}
ENV ALGORITHM=${ALGORITHM}
ENV DB_HOST=${DB_HOST}
ENV DB_NAME=${DB_NAME}
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}

# Запуск приложения
CMD ["python", "main.py"]