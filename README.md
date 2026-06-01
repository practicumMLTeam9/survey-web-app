![Python](https://img.shields.io/badge/Python-3670A0?style=flat&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat&logo=vite&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=github-actions&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)

## Кейс 9. Система опросов

Приложение для создания опросов, голосования и отображения результатов в реальном времени.
---

## Команда проекта

| ФИО       | никнеймы в GitHub | роли в команде       |
|-----------|-------------------------|----------------------|
| Елена     |  LinkiChmu               | тимлид, DE           |
| Влад      | PurpleZeroys              | PO, бизнес-аналитик  |
| Артём     | roux-afk              | фронтенд, ML-инженер |
| Владислав | framey1              | DevOps-инженер, DBA  |
| Максим    | Max-st21              | бэкенд, ML-инженер   |

## Куратор проекта


Контакты: [ mazurva ]

---

## План работы
| Спринт                         | Задачи                                                                                                                                                                                                                                                                                                                       |
|--------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **9-22 апреля 2026**           | • Исследование рынка, анализ нескольких конкурентов<br>• Создание GitHub-организации и репозитория<br>• Настройка веток `main` и `dev`<br>• Заполнение README (описание, цель, команда, roadmap)<br>• Контракт REST API<br>• Пользовательские сценарии<br>• Метрики успешности продукта<br>• Исследование дизайна интерфейсов |
| **23 апреля - 29 апреля 2026** | • Проектирование и создание модели данных<br>• Организация хранения данных в СУБД<br>• Доработка API (FastAPI)<br>• Разработка фронтенда<br>• Аналитика по ML<br>• Извлечение данных опросов и формирование датасетов<br>• Анализ результатов опросов с помощью AI<br>                                                       |
| **30 апреля - 19 мая 2026**    | • Подключение фронтенда к API бэкенда<br>• Создание тестовых кейсов<br>• Тестирование приложения<br>• Доработка бэкенда и фронтенда<br> • Расчет метрик по продукту<br>                                                                                                                                                          |
| **20 мая - 2 июня 2026**       | • Финальное тестирование приложения<br>• Исправление дефектов<br>• Итоговая презентация <br>• Итоговая защита<br>                                                                                                                                                                                                            |

###  Цель проекта

Разрабока системы для корпоративных опросов и анализа их результатов

### Запустить приложение в контейнере

#### в консоли

`docker compose up --build -d`

#### логи фронтенда (посмотреть url фронтенда)

`docker compose logs -f frontend`

#### логи бэкендa (для swagger - добавить в url `/docs` )
`docker compose logs -f backend`
