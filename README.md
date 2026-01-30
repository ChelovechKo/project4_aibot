# Project M4: AI-генератор постов для Telegram #

Это учебный проект, где требуется автоматизировать новостной Telegram-канал на новом уровне.
Необходимо сделать сервис, который не просто парсит новости, но использует ИИ для генерации ярких, лаконичных и интересных постов на основе собранных материалов.
Публикация должна идти в Telegram-канал по расписанию, с возможностью ручного управления и мониторинга через API.

В проекте интегрированы несколько сервисов: парсинг новостей (сайты и Telegram-каналы), очередь задач, генерация постов с OpenAI GPT, публикация через Telethon.

#       Как начать       #

1. Склонируйте репозиторий в рабочую директорию:
git clone https://github.com/ChelovechKo/project4_aibot.git
2. Создайте файл .env (можно скопировать из .env.example)
3. Поднимите контейнеры
docker compose up --build -d
4. Swagger: http://localhost:8000/docs

#  Функциональные блоки  #

1. Сбор и парсинг новостей (сайты и Telegram-каналы)
Сбор новосте с сайтов и из публичных Telegram-каналов (с помощью Telethon).
Для каждого источника реализуется отдельный парсер.
По расписанию запускается сбор новостей (каждые 30 минут, Celery Beat).
Каждая новость должна содержать: title, url (если есть), summary, source, published_at.
2. Очередь задач и асинхронная обработка
Использование Celery и брокера (RabbitMQ или Redis) для обработки задач (парсинг, генерация, публикация).
Фоновая цепочка: парсинг → фильтрация → генерация поста через AI → публикация.
3. AI-генерация постов
Использование OpenAI GPT-4 через публичный API.
На вход: текст новости/сводка/пост из Telegram, на выход: сгенерированный пост по заданному промпту.
Обработка ошибок API (rate limit, недоступность).
Возможность вручную протестировать генерацию через API.
4. Фильтрация и отбор релевантных новостей
Перед генерацией AI добавить возможность фильтровать новости по ключевым словам, источнику (настройка в API).
Исключение дублей (по url и\или title).
5. Публикация в Telegram через Telethon
После генерации AI-поста отправлять его в указанный Telegram-канал (через Telethon).
Проверять, что пост не был уже опубликован.
Логировать успешные публикации и ошибки.
6. Управление источниками и ключевыми словами (панель администратора через API)
REST API для добавления, редактирования, удаления источников новостей (сайты, Telegram-каналы).
API для управления списком ключевых слов и фильтров.
Эндпоинты для просмотра истории постов, логов ошибок.
7. Документация API (Swagger)
Автоматическая генерация через FastAPI (/docs).
Документировать основные эндпоинты: новости, генерация, публикация, источники, фильтры.

#    Структура данных    #

Модель NewsItem:
 - id (uuid или hash)
 - title (str)
 - url (str, optional)
 - summary (str)
 - source (str)
 - published_at (datetime)
 -  (str, если из Telegram)

Модель Post:
 - id
 - news_id
 - generated_text (str)
 - published_at (datetime)
 - status (new/generated/published/failed)

Модель Source:
 - id
 - type (site/tg)
 - name
 - url (или username для TG)
 - enabled (bool)

Модель Keyword:
 - id
 - word

#   Проектная структура  #

/aibot/  
├── app/  
│   ├── ai/  
│   │   ├── generator.py  
│   │   └── openai_client.py  
│   ├── api/  
│   │   ├── endpoints.py  
│   │   └── schemas.py  
│   ├── database/  
│   │   ├── db.py  
│   │   ├── models.py  
│   │   └── types.py  
│   ├── news_parser/  
│   │   ├── sites.py  
│   │   └── telegram.py  
│   ├── telegram/  
│   │   ├── bot.py  
│   │   └── publisher.py  
|   ├── celery_worker.py  
│   ├── config.py  
|   ├── main.py  
│   ├── tasks.py  
│   └── utils.py  
├── .env  
├── docker-compose.yml  
├── Dockerfile  
├── fixtures.py  
├── pyproject.toml  
└── README.md  

# Чеклист по функциональности #

№	Функция	URL/Команда	Методы	Технологии  
1 [X] Сбор новостей (сайты)	Celery Beat	-	Celery, requests  
2 [ ] Сбор новостей (Telegram)	Celery Beat	-	Telethon  
3 [X] Фильтрация новостей	-	-	Python, Redis  
4 [X] AI-генерация постов	Celery Task	-	OpenAI API, asyncio  
5 [X] Публикация в Telegram	Celery Task	-	Telethon, Redis  
6 [X] API-управление	/api/sources/	CRUD	FastAPI  
7 [X] API-фильтры	/api/keywords/	CRUD	FastAPI  
8 [X] История постов	/api/posts/	GET	FastAPI  
9 [X] Генерация вручную	/api/generate/	POST	FastAPI, OpenAI  
10 [X] Документация API	/docs/	GET	FastAPI (Swagger)  
11 [X] Логирование	-	-	logging  
