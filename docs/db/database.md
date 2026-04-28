# Database Overview

База данных реализована на PostgreSQL и хранит пользователей, опросы, ответы, подписки и AI-аналитику.

---

## 1. users

Хранит зарегистрированных пользователей системы.

| Поле | Описание |
|---|---|
| id | Уникальный идентификатор пользователя |
| email | Email для регистрации и входа |
| password_hash | Хеш пароля |
| created_at | Дата создания аккаунта |
| reset_token_hash | Хеш токена для сброса пароля |
| reset_token_expires_at | Срок действия токена сброса пароля |
| first_name | Имя пользователя |
| last_name | Фамилия пользователя |
| company_name | Название компании |
| position | Должность |
| phone | Телефон |
| interface_language | Язык интерфейса |
| role | Роль пользователя |
| avatar_url | Ссылка на аватар |

Связи:
- один пользователь может создать много опросов
- один пользователь может иметь подписку
- один пользователь может инициировать AI-запросы

---

## 2. subscriptions

Хранит тариф пользователя.

| Поле | Описание |
|---|---|
| id | Уникальный идентификатор подписки |
| user_id | ID пользователя |
| plan | Тариф: free, pro, enterprise |
| status | Статус: active, expired, cancelled |
| started_at | Дата начала |
| expires_at | Дата окончания |

---

## 3. polls

Хранит основные данные опроса.

| Поле | Описание |
|---|---|
| id | Уникальный идентификатор опроса |
| title | Название |
| description | Описание |
| status | draft, active, closed |
| created_at | Дата создания |
| created_by_user_id | Автор |
| updated_at | Обновление |
| published_at | Публикация |
| expires_at | Завершение |
| is_anonymous | Анонимность |
| one_response_only | Один ответ |
| poll_type | Тип опроса |
| language | Язык |
| max_participants | Лимит участников |
| show_progress | Показывать прогресс |
| notify_on_response | Уведомления |
| generated_by_ai | Создан AI |
| ai_generation_prompt | Промпт генерации |
| target_participants | План участников |

Связи:
- один `poll` содержит много `questions`
- один `poll` имеет много `submissions`
- один `poll` может иметь AI-резюме и AI-чат
- один `poll` связан с AI-запросами

---

## 4. questions

Хранит вопросы внутри опроса.

| Поле | Описание |
|---|---|
| id | ID вопроса |
| poll_id | ID опроса |
| text | Текст |
| type | single_choice, multiple_choice, text, scale |
| is_required | Обязательность |
| position | Порядок |

---

## 5. question_options

Хранит варианты ответов.

| Поле | Описание |
|---|---|
| id | ID варианта |
| question_id | ID вопроса |
| text | Текст |
| position | Порядок |

---

## 6. submissions

Факт прохождения опроса.

| Поле | Описание |
|---|---|
| id | ID прохождения |
| poll_id | ID опроса |
| respondent_token | Анонимный токен |
| created_at | Дата |
| started_at | Время начала |
| completed_at | Время завершения |

---

## 7. answers

Ответы пользователей.

| Поле | Описание |
|---|---|
| id | ID ответа |
| submission_id | ID прохождения |
| question_id | ID вопроса |
| option_id | ID варианта |
| text_value | Текст |

Логика:
- выбор → option_id  
- текст → text_value  
- multiple_choice → несколько строк  

---

## 8. ai_summaries

AI-резюме.

| Поле | Описание |
|---|---|
| id | ID |
| poll_id | Опрос |
| summary_text | Текст |
| created_at | Дата |

---

## 9. ai_chat_messages

Чат с AI.

| Поле | Описание |
|---|---|
| id | ID |
| poll_id | Опрос |
| role | user / assistant |
| message_text | Текст |
| created_at | Дата |

---

## 10. ai_requests

Логи AI-запросов.

| Поле | Описание |
|---|---|
| id | ID |
| user_id | Пользователь |
| poll_id | Опрос |
| request_type | generate_poll / summary / chat |
| created_at | Дата |

Используется для лимитов и аналитики.

---

# Relationships

Основная логика связей:
users → polls
users → subscriptions
users → ai_requests

polls → questions → question_options
polls → submissions → answers
polls → ai_summaries
polls → ai_chat_messages
polls → ai_requests

## Подробно

- Один пользователь может создать несколько опросов  
- Один пользователь может иметь подписку  
- Один пользователь может делать AI-запросы  

- Один опрос содержит вопросы  
- Один вопрос содержит варианты  

- Один опрос проходит много пользователей  
- Один submission содержит ответы  

- Один опрос может иметь:
  - AI-резюме  
  - AI-чат  
  - AI-запросы  

---

# Constraints

- FOREIGN KEY  
- ON DELETE CASCADE  
- UNIQUE (poll_id, respondent_token)  

CHECK:
- questions.type  
- polls.status  
- subscriptions.plan  
- subscriptions.status  
- ai_requests.request_type  

---

# Indexes

- questions.poll_id  
- question_options.question_id  
- submissions.poll_id  
- answers.submission_id  
- answers.question_id  
- answers.option_id  
- ai_summaries.poll_id  
- ai_chat_messages.poll_id  
- polls.created_by_user_id  
- polls.status  
- subscriptions.user_id  
- ai_requests.user_id  
- ai_requests.poll_id  

---

# Anonymous Mode

Используется respondent_token.

Позволяет:
- не хранить личные данные  
- ограничить повторные ответы  

---

# Data Flow

1. Создание опроса → polls, questions, options  
2. Прохождение → submissions  
3. Ответы → answers  
4. Аналитика → aggregation  
5. AI → summaries / chat  
6. Логи AI → ai_requests  

---

# AI Integration

- ai_summaries — кэш анализа  
- ai_chat_messages — диалог  
- ai_requests — лимиты  

---

# Subscription Logic

Тарифы:
- free  
- pro  
- enterprise  

Ограничения:
- опросы  
- ответы  
- участники  
- AI-запросы  
