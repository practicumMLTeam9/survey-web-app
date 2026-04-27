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

CREATE TABLE public.users ( id serial4 NOT NULL, email text NOT NULL, password_hash text NOT NULL, created_at timestamp DEFAULT now() NULL, reset_token_hash text NULL, reset_token_expires_at timestamp NULL, CONSTRAINT users_email_key UNIQUE (email), CONSTRAINT users_pkey PRIMARY KEY (id));
COMMENT ON TABLE public.users IS 'Зарегистрированные пользователи системы';

-- Column comments

COMMENT ON COLUMN public.users.id IS 'Уникальный идентификатор пользователя';
COMMENT ON COLUMN public.users.email IS 'Email пользователя для входа';
COMMENT ON COLUMN public.users.password_hash IS 'Хеш пароля';
COMMENT ON COLUMN public.users.created_at IS 'Дата регистрации';
COMMENT ON COLUMN public.users.reset_token_hash IS 'Хеш токена сброса пароля';
COMMENT ON COLUMN public.users.reset_token_expires_at IS 'Срок действия токена сброса пароля';


-- public.polls определение

-- Drop table

-- DROP TABLE public.polls;

CREATE TABLE public.polls ( id serial4 NOT NULL, title text NOT NULL, description text NULL, status text DEFAULT 'draft'::text NOT NULL, created_at timestamp DEFAULT now() NOT NULL, created_by_user_id int4 NULL, updated_at timestamp DEFAULT now() NULL, published_at timestamp NULL, expires_at timestamp NULL, is_anonymous bool DEFAULT true NULL, one_response_only bool DEFAULT true NULL, CONSTRAINT check_status CHECK ((status = ANY (ARRAY['draft'::text, 'active'::text, 'closed'::text]))), CONSTRAINT polls_pkey PRIMARY KEY (id), CONSTRAINT polls_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id));
COMMENT ON TABLE public.polls IS 'Опросы, создаваемые пользователями';

-- Column comments

COMMENT ON COLUMN public.polls.id IS 'Уникальный идентификатор опроса';
COMMENT ON COLUMN public.polls.title IS 'Название опроса';
COMMENT ON COLUMN public.polls.description IS 'Описание опроса';
COMMENT ON COLUMN public.polls.status IS 'Статус опроса (draft, active, closed)';
COMMENT ON COLUMN public.polls.created_at IS 'Дата создания';
COMMENT ON COLUMN public.polls.created_by_user_id IS 'ID пользователя, создавшего опрос';
COMMENT ON COLUMN public.polls.updated_at IS 'Дата последнего обновления';
COMMENT ON COLUMN public.polls.published_at IS 'Дата публикации';
COMMENT ON COLUMN public.polls.expires_at IS 'Дата окончания опроса';
COMMENT ON COLUMN public.polls.is_anonymous IS 'Признак анонимного опроса';
COMMENT ON COLUMN public.polls.one_response_only IS 'Разрешен только один ответ от пользователя';


-- public.questions определение

-- Drop table

-- DROP TABLE public.questions;

CREATE TABLE public.questions ( id serial4 NOT NULL, poll_id int4 NOT NULL, "text" text NOT NULL, "type" text NOT NULL, is_required bool DEFAULT false NOT NULL, "position" int4 NOT NULL, CONSTRAINT check_question_type CHECK ((type = ANY (ARRAY['single_choice'::text, 'multiple_choice'::text, 'text'::text, 'scale'::text]))), CONSTRAINT questions_pkey PRIMARY KEY (id), CONSTRAINT questions_poll_id_fkey FOREIGN KEY (poll_id) REFERENCES public.polls(id) ON DELETE CASCADE);
CREATE INDEX idx_questions_poll_id ON public.questions USING btree (poll_id);
COMMENT ON TABLE public.questions IS 'Вопросы внутри опроса';

-- Column comments

COMMENT ON COLUMN public.questions.id IS 'Уникальный идентификатор вопроса';
COMMENT ON COLUMN public.questions.poll_id IS 'ID опроса';
COMMENT ON COLUMN public.questions."text" IS 'Текст вопроса';
COMMENT ON COLUMN public.questions."type" IS 'Тип вопроса (single_choice, multiple_choice, text, scale)';
COMMENT ON COLUMN public.questions.is_required IS 'Обязательный ли вопрос';
COMMENT ON COLUMN public.questions."position" IS 'Порядок отображения вопроса';


-- public.submissions определение

-- Drop table

-- DROP TABLE public.submissions;

CREATE TABLE public.submissions ( id serial4 NOT NULL, poll_id int4 NOT NULL, respondent_token text NULL, created_at timestamp DEFAULT now() NOT NULL, CONSTRAINT submissions_pkey PRIMARY KEY (id), CONSTRAINT submissions_poll_id_fkey FOREIGN KEY (poll_id) REFERENCES public.polls(id) ON DELETE CASCADE);
CREATE INDEX idx_submissions_poll_id ON public.submissions USING btree (poll_id);
CREATE UNIQUE INDEX uniq_submission ON public.submissions USING btree (poll_id, respondent_token);
COMMENT ON TABLE public.submissions IS 'Факт прохождения опроса пользователем';

-- Column comments

COMMENT ON COLUMN public.submissions.id IS 'ID прохождения';
COMMENT ON COLUMN public.submissions.poll_id IS 'ID опроса';
COMMENT ON COLUMN public.submissions.respondent_token IS 'Анонимный идентификатор пользователя';
COMMENT ON COLUMN public.submissions.created_at IS 'Дата отправки ответов';


-- public.ai_chat_messages определение

-- Drop table

-- DROP TABLE public.ai_chat_messages;

CREATE TABLE public.ai_chat_messages ( id serial4 NOT NULL, poll_id int4 NOT NULL, "role" text NOT NULL, message_text text NOT NULL, created_at timestamp DEFAULT now() NULL, CONSTRAINT ai_chat_messages_pkey PRIMARY KEY (id), CONSTRAINT ai_chat_messages_poll_id_fkey FOREIGN KEY (poll_id) REFERENCES public.polls(id) ON DELETE CASCADE);
CREATE INDEX idx_ai_chat_poll_id ON public.ai_chat_messages USING btree (poll_id);
COMMENT ON TABLE public.ai_chat_messages IS 'История общения пользователя с AI по опросу';

-- Column comments

COMMENT ON COLUMN public.ai_chat_messages.id IS 'ID сообщения';
COMMENT ON COLUMN public.ai_chat_messages.poll_id IS 'ID опроса';
COMMENT ON COLUMN public.ai_chat_messages."role" IS 'Роль (user или assistant)';
COMMENT ON COLUMN public.ai_chat_messages.message_text IS 'Текст сообщения';
COMMENT ON COLUMN public.ai_chat_messages.created_at IS 'Дата сообщения';


-- public.ai_summaries определение

-- Drop table

-- DROP TABLE public.ai_summaries;

CREATE TABLE public.ai_summaries ( id serial4 NOT NULL, poll_id int4 NOT NULL, summary_text text NOT NULL, created_at timestamp DEFAULT now() NULL, CONSTRAINT ai_summaries_pkey PRIMARY KEY (id), CONSTRAINT ai_summaries_poll_id_fkey FOREIGN KEY (poll_id) REFERENCES public.polls(id) ON DELETE CASCADE);
CREATE INDEX idx_ai_summary_poll_id ON public.ai_summaries USING btree (poll_id);
COMMENT ON TABLE public.ai_summaries IS 'AI-резюме по результатам опроса';

-- Column comments

COMMENT ON COLUMN public.ai_summaries.id IS 'ID резюме';
COMMENT ON COLUMN public.ai_summaries.poll_id IS 'ID опроса';
COMMENT ON COLUMN public.ai_summaries.summary_text IS 'Сгенерированный текст резюме';
COMMENT ON COLUMN public.ai_summaries.created_at IS 'Дата генерации';


-- public.question_options определение

-- Drop table

-- DROP TABLE public.question_options;

CREATE TABLE public.question_options ( id serial4 NOT NULL, question_id int4 NOT NULL, "text" text NOT NULL, "position" int4 NOT NULL, CONSTRAINT question_options_pkey PRIMARY KEY (id), CONSTRAINT question_options_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE);
CREATE INDEX idx_options_question_id ON public.question_options USING btree (question_id);
COMMENT ON TABLE public.question_options IS 'Варианты ответов для вопросов';

-- Column comments

COMMENT ON COLUMN public.question_options.id IS 'ID варианта ответа';
COMMENT ON COLUMN public.question_options.question_id IS 'ID вопроса';
COMMENT ON COLUMN public.question_options."text" IS 'Текст варианта';
COMMENT ON COLUMN public.question_options."position" IS 'Порядок отображения варианта';


-- public.answers определение

-- Drop table

-- DROP TABLE public.answers;

CREATE TABLE public.answers ( id serial4 NOT NULL, submission_id int4 NOT NULL, question_id int4 NOT NULL, option_id int4 NULL, text_value text NULL, CONSTRAINT answers_pkey PRIMARY KEY (id), CONSTRAINT answers_option_id_fkey FOREIGN KEY (option_id) REFERENCES public.question_options(id) ON DELETE CASCADE, CONSTRAINT answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE, CONSTRAINT answers_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) ON DELETE CASCADE);
CREATE INDEX idx_answers_option_id ON public.answers USING btree (option_id);
CREATE INDEX idx_answers_question_id ON public.answers USING btree (question_id);
CREATE INDEX idx_answers_submission_id ON public.answers USING btree (submission_id);
COMMENT ON TABLE public.answers IS 'Ответы пользователей на вопросы';

-- Column comments

COMMENT ON COLUMN public.answers.id IS 'ID ответа';
COMMENT ON COLUMN public.answers.submission_id IS 'ID прохождения опроса';
COMMENT ON COLUMN public.answers.question_id IS 'ID вопроса';
COMMENT ON COLUMN public.answers.option_id IS 'ID выбранного варианта';
COMMENT ON COLUMN public.answers.text_value IS 'Текстовый ответ';