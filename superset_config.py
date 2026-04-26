import os

SECRET_KEY = "super_secure_random_key_123456"

SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:airflow@cloudsql-proxy:5432/airflow"

WTF_CSRF_ENABLED = True

