# LinkShorteningServices

API-сервис сокращения ссылок, разработанный на FastAPI.

Сервис позволяет создавать короткие ссылки, выполнять редирект на оригинальный URL, получать статистику переходов и управлять ссылками зарегистрированным пользователям.  
Для хранения данных используется PostgreSQL, для кэширования — Redis.

---

## Tech Stack

- FastAPI
- PostgreSQL
- Redis
- SQLAlchemy
- Alembic
- Docker / Docker Compose

---

## Основные эндпоинты

### Аутентификация

**POST /auth/register**
Регистрация пользователя.

**POST /auth/jwt/login**
Вход пользователя. Устанавливает cookie с JWT.

**POST /auth/jwt/logout**
Выход пользователя.

---

### Работа со ссылками

**POST /links/shorten**
Создание короткой ссылки.  
Поддерживает:
- пользовательский alias
- срок жизни ссылки

**GET /links/search**
Поиск ссылки по оригинальному URL.

**GET /links/{short_code}/stats**
Получение статистики по ссылке:
- оригинальный URL
- дата создания
- количество переходов
- дата последнего использования.

**GET /links/my**
Получение списка ссылок текущего пользователя.
Требуется авторизация.

**GET /links/top**
Получение списка самых популярных ссылок по количеству переходов.

**GET /links/check-alias/{alias}**
Проверка доступности пользовательского alias.

**GET /links/expired**  
Получение истории истекших ссылок пользователя.
Требуется авторизация.

**PUT /links/{short_code}**
Обновление оригинального URL.
Доступно только создателю ссылки.

**DELETE /links/{short_code}**
Удаление ссылки.
Доступно только создателю ссылки.

### Редирект

**GET /{short_code}**

Переход по короткой ссылке.  
Сервис ищет оригинальный URL и выполняет redirect.

При переходе:

- увеличивается счетчик переходов
- обновляется время последнего использования
- используется Redis-кэш

Если срок жизни ссылки истек, она переносится в таблицу expired_links.

---

## База данных

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

## Кэширование

Используется Redis.

Кэшируются:
- редиректы коротких ссылок
- результат запроса /links/top

Кэш очищается при обновлении или удалении ссылки.

---

## Запуск проекта

Проект запускается через Docker Compose.

### 1. Перейти в корневую директорию проекта

cd LinkShorteningServices

### 2. Создать файл .env

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

### 3. Запустить контейнеры

docker compose up --build

Будут запущены:

- PostgreSQL
- Redis
- FastAPI приложение


# Testing

В проекте реализованы три типа тестирования:

- Unit tests
- Functional (API) tests
- Load testing

Общее покрытие кода тестами: 93%.

HTML-отчет покрытия находится в файле index.html.

---

## Unit Tests

Проверяют бизнес-логику сервиса:

- генерацию short code
- создание ссылок
- проверку alias
- обновление и удаление ссылок
- логику редиректа
- обработку ошибок

Расположение:

tests/unit

Запуск:

```shell
python -m pytest tests/unit -v
```

---

## Functional Tests

Функциональные тесты проверяют API через FastAPI TestClient.

Проверяемые сценарии:

Аутентификация
- регистрация
- логин
- logout

Работа со ссылками
- создание ссылки
- поиск по original_url
- получение статистики
- список ссылок пользователя
- популярные ссылки
- проверка alias
- обновление ссылки
- удаление ссылки
- получение expired ссылок

Редирект
- переход по short link
- увеличение click count
- обработка expired ссылок

Расположение:

tests/functional

Запуск:

```shell
python -m pytest tests/functional -v
```

---

## Coverage

Запуск всех тестов с coverage:

```shell
python -m coverage run -m pytest tests
```

Отчет в консоли:

```shell
python -m coverage report -m
```

HTML-отчет:

```shell
python -m coverage html
```

После генерации отчет доступен в файле:

```shell
index.html
```

Общее покрытие: 93%

---

## Load Testing

Для нагрузочного тестирования используется Locust.

Тестируются:

- POST /links/shorten
- GET /{short_code}
- GET /links/top

Файл сценария:

tests/load/locustfile.py

---

## Запуск нагрузочного теста

Сначала нужно запустить сервис:

```shell
docker compose up --build
```

После запуска API будет доступен по адресу:

```
http://localhost:8000
```

Далее запускается Locust:

```shell
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

Интерфейс Locust:

```
http://localhost:8089
```

---

## Параметры тестирования

**Тест 1**

Users: 20  
Spawn rate: 5 users/s  
Duration: ~1 minute  

Результат:
- ~2000 requests
- 0 failures
- ~11 ms average response time

**Тест 2**

Users: 50  
Spawn rate: 10 users/s  
Duration: ~1 minute  

Результат:
- ~2600 requests
- 0 failures
- ~12 ms average response time
- ~30 RPS

---

## Conclusion

Сервис стабильно работает под нагрузкой.

- ошибки отсутствуют
- среднее время ответа ~10–12 ms
- Redis-кэш ускоряет редиректы и endpoint /links/top

---

# Файловая структура проекта:

```
.
├── Dockerfile
├── alembic.ini
├── docker-compose.yml
├── htmlcov/
├── pytest.ini
├── readme.md
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
│   ├── config.py
│   ├── main.py
│   └── models
│       └── tables.py
└── tests
    ├── conftest.py
    ├── functional
    │   ├── conftest.py
    │   ├── test_auth.py
    │   ├── test_links.py
    │   └── test_redirect.py
    ├── load
    │   └── locustfile.py
    └── unit
        ├── test_link_service_create.py
        ├── test_link_service_read.py
        ├── test_link_service_redirect.py
        └── test_link_service_update_delete.py
```