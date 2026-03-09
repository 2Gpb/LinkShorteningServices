from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST=os.environ.get('DB_HOST')
DB_PORT=os.environ.get('DB_PORT')
DB_NAME=os.environ.get('DB_NAME')
DB_USER=os.environ.get('DB_USER')
DB_PASS=os.environ.get('DB_PASS')

DATABASE_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_DB = int(os.getenv("REDIS_DB"))

REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

SECRET=os.environ.get('SECRET')

INACTIVE_LINK_DAYS = 30