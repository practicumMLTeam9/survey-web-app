-- DROP SCHEMA public;

CREATE SCHEMA public AUTHORIZATION pg_database_owner;

COMMENT ON SCHEMA public IS 'standard public schema';

-- DROP SEQUENCE public.ai_chat_messages_id_seq;

CREATE SEQUENCE public.ai_chat_messages_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.ai_requests_id_seq;

CREATE SEQUENCE public.ai_requests_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.ai_summaries_id_seq;

CREATE SEQUENCE public.ai_summaries_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.answers_id_seq;

CREATE SEQUENCE public.answers_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.answers_id_seq1;

CREATE SEQUENCE public.answers_id_seq1
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.polls_id_seq;

CREATE SEQUENCE public.polls_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.polls_id_seq1;

CREATE SEQUENCE public.polls_id_seq1
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.question_options_id_seq;

CREATE SEQUENCE public.question_options_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.question_options_id_seq1;

CREATE SEQUENCE public.question_options_id_seq1
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.questions_id_seq;

CREATE SEQUENCE public.questions_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.questions_id_seq1;

CREATE SEQUENCE public.questions_id_seq1
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.submissions_id_seq;

CREATE SEQUENCE public.submissions_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.submissions_id_seq1;

CREATE SEQUENCE public.submissions_id_seq1
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.subscriptions_id_seq;

CREATE SEQUENCE public.subscriptions_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.users_id_seq;

CREATE SEQUENCE public.users_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.users_id_seq1;

CREATE SEQUENCE public.users_id_seq1
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;-- public.users определение

-- Drop table

-- DROP TABLE public.users;

CREATE TABLE public.users ( id serial4 NOT NULL, email text NOT NULL, password_hash text NOT NULL, created_at timestamp DEFAULT now() NULL, reset_token_hash text NULL, reset_token_expires_at timestamp NULL, first_name text NULL, last_name text NULL, company_name text NULL, "position" text NULL, phone text NULL, interface_language text DEFAULT 'ru'::text NULL, "role" text DEFAULT 'user'::text NULL, avatar_url text NULL, CONSTRAINT users_email_key UNIQUE (email), CONSTRAINT users_pkey PRIMARY KEY (id));
COMMENT ON TABLE public.users IS 'Зарегистрированные пользователи системы';

-- Column comments

COMMENT ON COLUMN public.users.id IS 'Уникальный идентификатор пользователя';
COMMENT ON COLUMN public.users.email IS 'Email пользователя для регистрации и входа';
COMMENT ON COLUMN public.users.password_hash IS 'Хеш пароля пользователя';
COMMENT ON COLUMN public.users.created_at IS 'Дата создания аккаунта';
COMMENT ON COLUMN public.users.reset_token_hash IS 'Хеш токена для сброса пароля';
COMMENT ON COLUMN public.users.reset_token_expires_at IS 'Срок действия токена сброса пароля';
COMMENT ON COLUMN public.users.first_name IS 'Имя пользователя';
COMMENT ON COLUMN public.users.last_name IS 'Фамилия пользователя';
COMMENT ON COLUMN public.users.company_name IS 'Название компании пользователя';
COMMENT ON COLUMN public.users."position" IS 'Должность пользователя';
COMMENT ON COLUMN public.users.phone IS 'Телефон пользователя';
COMMENT ON COLUMN public.users.interface_language IS 'Язык интерфейса пользователя';
COMMENT ON COLUMN public.users."role" IS 'Роль пользователя в системе';
COMMENT ON COLUMN public.users.avatar_url IS 'Ссылка на аватар пользователя';


-- public.polls определение

-- Drop table

-- DROP TABLE public.polls;

CREATE TABLE public.polls ( id serial4 NOT NULL, title text NOT NULL, description text NULL, status text DEFAULT 'draft'::text NOT NULL, created_at timestamp DEFAULT now() NOT NULL, created_by_user_id int4 NULL, updated_at timestamp DEFAULT now() NULL, published_at timestamp NULL, expires_at timestamp NULL, is_anonymous bool DEFAULT true NULL, one_response_only bool DEFAULT true NULL, poll_type text DEFAULT 'corporate'::text NULL, "language" text DEFAULT 'ru'::text NULL, max_participants int4 NULL, show_progress bool DEFAULT true NULL, notify_on_response bool DEFAULT false NULL, generated_by_ai bool DEFAULT false NULL, ai_generation_prompt text NULL, target_participants int4 NULL, CONSTRAINT check_status CHECK ((status = ANY (ARRAY['draft'::text, 'active'::text, 'closed'::text]))), CONSTRAINT polls_pkey PRIMARY KEY (id), CONSTRAINT polls_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id));
CREATE INDEX idx_polls_created_by_user_id ON public.polls USING btree (created_by_user_id);
CREATE INDEX idx_polls_status ON public.polls USING btree (status);
COMMENT ON TABLE public.polls IS 'Опросы, создаваемые пользователями';

-- Column comments

COMMENT ON COLUMN public.polls.id IS 'Уникальный идентификатор опроса';
COMMENT ON COLUMN public.polls.title IS 'Название опроса';
COMMENT ON COLUMN public.polls.description IS 'Описание опроса';
COMMENT ON COLUMN public.polls.status IS 'Статус опроса: draft, active, closed';
COMMENT ON COLUMN public.polls.created_at IS 'Дата создания опроса';
COMMENT ON COLUMN public.polls.created_by_user_id IS 'ID пользователя, создавшего опрос';
COMMENT ON COLUMN public.polls.updated_at IS 'Дата последнего обновления опроса';
COMMENT ON COLUMN public.polls.published_at IS 'Дата публикации опроса';
COMMENT ON COLUMN public.polls.expires_at IS 'Дата окончания опроса';
COMMENT ON COLUMN public.polls.is_anonymous IS 'Признак анонимного опроса';
COMMENT ON COLUMN public.polls.one_response_only IS 'Ограничение на один ответ от одного участника';
COMMENT ON COLUMN public.polls.poll_type IS 'Тип опроса, например corporate или client';
COMMENT ON COLUMN public.polls."language" IS 'Язык опроса';
COMMENT ON COLUMN public.polls.max_participants IS 'Максимальное количество участников опроса';
COMMENT ON COLUMN public.polls.show_progress IS 'Показывать ли участнику прогресс прохождения опроса';
COMMENT ON COLUMN public.polls.notify_on_response IS 'Отправлять ли уведомление при новом ответе';
COMMENT ON COLUMN public.polls.generated_by_ai IS 'Признак того, что опрос был сгенерирован с помощью AI';
COMMENT ON COLUMN public.polls.ai_generation_prompt IS 'Промпт, по которому AI генерировал опрос';
COMMENT ON COLUMN public.polls.target_participants IS 'Планируемое или ожидаемое количество участников опроса';


-- public.questions определение

-- Drop table

-- DROP TABLE public.questions;

CREATE TABLE public.questions ( id serial4 NOT NULL, poll_id int4 NOT NULL, "text" text NOT NULL, "type" text NOT NULL, is_required bool DEFAULT false NOT NULL, "position" int4 NOT NULL, CONSTRAINT check_question_type CHECK ((type = ANY (ARRAY['single_choice'::text, 'multiple_choice'::text, 'text'::text, 'scale'::text]))), CONSTRAINT questions_pkey PRIMARY KEY (id), CONSTRAINT questions_poll_id_fkey FOREIGN KEY (poll_id) REFERENCES public.polls(id) ON DELETE CASCADE);
CREATE INDEX idx_questions_poll_id ON public.questions USING btree (poll_id);
COMMENT ON TABLE public.questions IS 'Вопросы внутри опросов';

-- Column comments

COMMENT ON COLUMN public.questions.id IS 'Уникальный идентификатор вопроса';
COMMENT ON COLUMN public.questions.poll_id IS 'ID опроса, к которому относится вопрос';
COMMENT ON COLUMN public.questions."text" IS 'Текст вопроса';
COMMENT ON COLUMN public.questions."type" IS 'Тип вопроса: single_choice, multiple_choice, text, scale';
COMMENT ON COLUMN public.questions.is_required IS 'Признак обязательного вопроса';
COMMENT ON COLUMN public.questions."position" IS 'Порядок отображения вопроса в опросе';


-- public.submissions определение

-- Drop table

-- DROP TABLE public.submissions;

CREATE TABLE public.submissions ( id serial4 NOT NULL, poll_id int4 NOT NULL, respondent_token text NULL, created_at timestamp DEFAULT now() NOT NULL, started_at timestamp NULL, completed_at timestamp NULL, CONSTRAINT submissions_pkey PRIMARY KEY (id), CONSTRAINT submissions_poll_id_fkey FOREIGN KEY (poll_id) REFERENCES public.polls(id) ON DELETE CASCADE);
CREATE INDEX idx_submissions_poll_id ON public.submissions USING btree (poll_id);
CREATE UNIQUE INDEX uniq_submission ON public.submissions USING btree (poll_id, respondent_token);
COMMENT ON TABLE public.submissions IS 'Факты прохождения опросов участниками';

-- Column comments

COMMENT ON COLUMN public.submissions.id IS 'Уникальный идентификатор прохождения опроса';
COMMENT ON COLUMN public.submissions.poll_id IS 'ID опроса, который прошёл участник';
COMMENT ON COLUMN public.submissions.respondent_token IS 'Анонимный идентификатор участника';
COMMENT ON COLUMN public.submissions.created_at IS 'Дата создания прохождения';
COMMENT ON COLUMN public.submissions.started_at IS 'Дата и время начала прохождения опроса';
COMMENT ON COLUMN public.submissions.completed_at IS 'Дата и время завершения прохождения опроса';


-- public.subscriptions определение

-- Drop table

-- DROP TABLE public.subscriptions;

CREATE TABLE public.subscriptions ( id serial4 NOT NULL, user_id int4 NOT NULL, plan text DEFAULT 'free'::text NOT NULL, status text DEFAULT 'active'::text NOT NULL, started_at timestamp DEFAULT now() NULL, expires_at timestamp NULL, CONSTRAINT check_subscription_plan CHECK ((plan = ANY (ARRAY['free'::text, 'pro'::text, 'enterprise'::text]))), CONSTRAINT check_subscription_status CHECK ((status = ANY (ARRAY['active'::text, 'expired'::text, 'cancelled'::text]))), CONSTRAINT subscriptions_pkey PRIMARY KEY (id), CONSTRAINT subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE);
CREATE INDEX idx_subscriptions_user_id ON public.subscriptions USING btree (user_id);
COMMENT ON TABLE public.subscriptions IS 'Подписки пользователей и тарифные планы';

-- Column comments

COMMENT ON COLUMN public.subscriptions.id IS 'Уникальный идентификатор подписки';
COMMENT ON COLUMN public.subscriptions.user_id IS 'ID пользователя, которому принадлежит подписка';
COMMENT ON COLUMN public.subscriptions.plan IS 'Тарифный план: free, pro, enterprise';
COMMENT ON COLUMN public.subscriptions.status IS 'Статус подписки: active, expired, cancelled';
COMMENT ON COLUMN public.subscriptions.started_at IS 'Дата начала действия подписки';
COMMENT ON COLUMN public.subscriptions.expires_at IS 'Дата окончания действия подписки';


-- public.ai_chat_messages определение

-- Drop table

-- DROP TABLE public.ai_chat_messages;

CREATE TABLE public.ai_chat_messages ( id serial4 NOT NULL, poll_id int4 NOT NULL, "role" text NOT NULL, message_text text NOT NULL, created_at timestamp DEFAULT now() NULL, CONSTRAINT ai_chat_messages_pkey PRIMARY KEY (id), CONSTRAINT ai_chat_messages_poll_id_fkey FOREIGN KEY (poll_id) REFERENCES public.polls(id) ON DELETE CASCADE);
CREATE INDEX idx_ai_chat_poll_id ON public.ai_chat_messages USING btree (poll_id);
COMMENT ON TABLE public.ai_chat_messages IS 'История общения пользователя с AI по конкретному опросу';

-- Column comments

COMMENT ON COLUMN public.ai_chat_messages.id IS 'Уникальный идентификатор сообщения';
COMMENT ON COLUMN public.ai_chat_messages.poll_id IS 'ID опроса, по которому ведётся AI-диалог';
COMMENT ON COLUMN public.ai_chat_messages."role" IS 'Роль автора сообщения: user или assistant';
COMMENT ON COLUMN public.ai_chat_messages.message_text IS 'Текст сообщения в AI-чате';
COMMENT ON COLUMN public.ai_chat_messages.created_at IS 'Дата создания сообщения';


-- public.ai_requests определение

-- Drop table

-- DROP TABLE public.ai_requests;

CREATE TABLE public.ai_requests ( id serial4 NOT NULL, user_id int4 NULL, poll_id int4 NULL, request_type text NOT NULL, created_at timestamp DEFAULT now() NULL, CONSTRAINT ai_requests_pkey PRIMARY KEY (id), CONSTRAINT check_ai_request_type CHECK ((request_type = ANY (ARRAY['generate_poll'::text, 'summary'::text, 'chat'::text]))), CONSTRAINT ai_requests_poll_id_fkey FOREIGN KEY (poll_id) REFERENCES public.polls(id) ON DELETE CASCADE, CONSTRAINT ai_requests_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL);
CREATE INDEX idx_ai_requests_created_at ON public.ai_requests USING btree (created_at);
CREATE INDEX idx_ai_requests_poll_id ON public.ai_requests USING btree (poll_id);
CREATE INDEX idx_ai_requests_user_id ON public.ai_requests USING btree (user_id);
COMMENT ON TABLE public.ai_requests IS 'Логи AI-запросов для учёта использования AI-функций';

-- Column comments

COMMENT ON COLUMN public.ai_requests.id IS 'Уникальный идентификатор AI-запроса';
COMMENT ON COLUMN public.ai_requests.user_id IS 'ID пользователя, который инициировал AI-запрос';
COMMENT ON COLUMN public.ai_requests.poll_id IS 'ID опроса, связанного с AI-запросом';
COMMENT ON COLUMN public.ai_requests.request_type IS 'Тип AI-запроса: generate_poll, summary, chat';
COMMENT ON COLUMN public.ai_requests.created_at IS 'Дата создания AI-запроса';


-- public.ai_summaries определение

-- Drop table

-- DROP TABLE public.ai_summaries;

CREATE TABLE public.ai_summaries ( id serial4 NOT NULL, poll_id int4 NOT NULL, summary_text text NOT NULL, created_at timestamp DEFAULT now() NULL, CONSTRAINT ai_summaries_pkey PRIMARY KEY (id), CONSTRAINT ai_summaries_poll_id_fkey FOREIGN KEY (poll_id) REFERENCES public.polls(id) ON DELETE CASCADE);
CREATE INDEX idx_ai_summary_poll_id ON public.ai_summaries USING btree (poll_id);
COMMENT ON TABLE public.ai_summaries IS 'AI-резюме по результатам опросов';

-- Column comments

COMMENT ON COLUMN public.ai_summaries.id IS 'Уникальный идентификатор AI-резюме';
COMMENT ON COLUMN public.ai_summaries.poll_id IS 'ID опроса, к которому относится AI-резюме';
COMMENT ON COLUMN public.ai_summaries.summary_text IS 'Текст AI-резюме по результатам опроса';
COMMENT ON COLUMN public.ai_summaries.created_at IS 'Дата генерации AI-резюме';


-- public.question_options определение

-- Drop table

-- DROP TABLE public.question_options;

CREATE TABLE public.question_options ( id serial4 NOT NULL, question_id int4 NOT NULL, "text" text NOT NULL, "position" int4 NOT NULL, CONSTRAINT question_options_pkey PRIMARY KEY (id), CONSTRAINT question_options_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE);
CREATE INDEX idx_options_question_id ON public.question_options USING btree (question_id);
COMMENT ON TABLE public.question_options IS 'Варианты ответов для вопросов с выбором';

-- Column comments

COMMENT ON COLUMN public.question_options.id IS 'Уникальный идентификатор варианта ответа';
COMMENT ON COLUMN public.question_options.question_id IS 'ID вопроса, к которому относится вариант';
COMMENT ON COLUMN public.question_options."text" IS 'Текст варианта ответа';
COMMENT ON COLUMN public.question_options."position" IS 'Порядок отображения варианта ответа';


-- public.answers определение

-- Drop table

-- DROP TABLE public.answers;

CREATE TABLE public.answers ( id serial4 NOT NULL, submission_id int4 NOT NULL, question_id int4 NOT NULL, option_id int4 NULL, text_value text NULL, CONSTRAINT answers_pkey PRIMARY KEY (id), CONSTRAINT answers_option_id_fkey FOREIGN KEY (option_id) REFERENCES public.question_options(id) ON DELETE CASCADE, CONSTRAINT answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE, CONSTRAINT answers_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) ON DELETE CASCADE);
CREATE INDEX idx_answers_option_id ON public.answers USING btree (option_id);
CREATE INDEX idx_answers_question_id ON public.answers USING btree (question_id);
CREATE INDEX idx_answers_submission_id ON public.answers USING btree (submission_id);
COMMENT ON TABLE public.answers IS 'Ответы участников на вопросы опроса';

-- Column comments

COMMENT ON COLUMN public.answers.id IS 'Уникальный идентификатор ответа';
COMMENT ON COLUMN public.answers.submission_id IS 'ID прохождения опроса';
COMMENT ON COLUMN public.answers.question_id IS 'ID вопроса, на который дан ответ';
COMMENT ON COLUMN public.answers.option_id IS 'ID выбранного варианта ответа';
COMMENT ON COLUMN public.answers.text_value IS 'Текстовый ответ участника';
