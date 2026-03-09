# LinkShorteningServices

API-сервис сокращения ссылок, разработанный на FastAPI.

Сервис позволяет создавать короткие ссылки, выполнять редирект на оригинальный URL, получать статистику переходов и управлять ссылками зарегистрированным пользователям.  
Для хранения данных используется PostgreSQL, для кэширования — Redis.

---

# Tech Stack

- FastAPI
- PostgreSQL
- Redis
- SQLAlchemy
- Alembic
- Docker / Docker Compose

---

# API Documentation

После запуска сервиса документация доступна по адресу:
**/docs**

---

# Основные эндпоинты

## Аутентификация

POST /auth/register  
Регистрация пользователя.

POST /auth/jwt/login  
Вход пользователя. Устанавливает cookie с JWT.

POST /auth/jwt/logout  
Выход пользователя.

## Работа со ссылками

POST /links/shorten  
Создание короткой ссылки.  
Поддерживает:
- пользовательский alias
- срок жизни ссылки

GET /links/search  
Поиск ссылки по оригинальному URL.

GET /links/{short_code}/stats  
Получение статистики по ссылке:
- оригинальный URL
- дата создания
- количество переходов
- дата последнего использования.

GET /links/my  
Получение списка ссылок текущего пользователя.
Требуется авторизация.

GET /links/top  
Получение списка самых популярных ссылок по количеству переходов.

GET /links/check-alias/{alias}  
Проверка доступности пользовательского alias.

GET /links/expired  
Получение истории истекших ссылок пользователя.
Требуется авторизация.

PUT /links/{short_code}  
Обновление оригинального URL.
Доступно только создателю ссылки.

DELETE /links/{short_code}  
Удаление ссылки.
Доступно только создателю ссылки.

## Редирект

GET /{short_code}

Переход по короткой ссылке.  
Сервис ищет оригинальный URL и выполняет redirect.

При переходе:

- увеличивается счетчик переходов
- обновляется время последнего использования
- используется Redis-кэш

Если срок жизни ссылки истек, она переносится в таблицу expired_links.

---

# База данных

В проекте используется PostgreSQL.  
Миграции базы данных реализованы с помощью Alembic.

### Таблица user
Хранит пользователей системы.

### Таблица links
Основная таблица коротких ссылок.

Поля:
- id
- original_url
- short_code
- created_at
- expires_at
- click_count
- last_used_at
- owner_id

### Таблица expired_links
Хранит историю ссылок, срок жизни которых истек.

Поля аналогичны таблице links + поле expired_at.

--- 

# Кэширование

Используется Redis.

Кэшируются:
- редиректы коротких ссылок
- результат запроса /links/top

Кэш очищается при обновлении или удалении ссылки.

---

# Запуск проекта

Проект запускается через Docker Compose.

## 1. Перейти в корневую директорию проекта

cd LinkShorteningServices

## 2. Создать файл .env

Пример:

DB_HOST=***  
DB_PORT=5432  
DB_NAME=***  
DB_USER=***  
DB_PASS=***  

REDIS_HOST=***  
REDIS_PORT=6379  
REDIS_DB=*** 

SECRET=***

## 3. Запустить контейнеры

docker compose up --build

Будут запущены:

- PostgreSQL
- Redis
- FastAPI приложение

---

Файловая структура проекта:

```
.
├── Dockerfile
├── alembic.ini
├── docker-compose.yml
├── migrations
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       ├── 328947599b73_add_links_table.py
│       ├── 6c96a0c67294_add_fastapi_users_fields.py
│       ├── 80f65996ebf0_add_expired_links_table.py
│       ├── a0d5ad288ff0_database_creation.py
│       └── b3cfd1062883_chabge_datetime_type.py
├── readme.md
├── requirements
│   └── base.txt
├── src
│   ├── auth
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── manager.py
│   │   ├── models.py
│   │   ├── router.py
│   │   └── schemas.py
│   ├── config.py
│   ├── core
│   │   ├── database.py
│   │   └── redis.py
│   ├── links
│   │   ├── cache_service.py
│   │   ├── dependencies.py
│   │   ├── exception.py
│   │   ├── redirect_router.py
│   │   ├── repository.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── main.py
│   └── models     
│       └── tables.py
└── tests
```