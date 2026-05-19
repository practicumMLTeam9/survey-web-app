import { useState } from "react"

export default function CreatePoll() {
    const [createMode, setCreateMode] = useState("ai")
    const [participants, setParticipants] = useState(280)

    const [unlimited, setUnlimited] = useState(false)

    const [showProgress, setShowProgress] = useState(true)

    const [questions, setQuestions] = useState([
        {
            id: 1,
            text: "Как вы оцениваете своё общее удовлетворение от работы?",
            type: "single",
            typeLabel: "Один вариант",
            options: [
                "Вариант 1",
                "Вариант 2"
            ]
        },
        {
            id: 2,
            text: "Что вам больше всего нравится в вашей работе?",
            type: "multiple",
            typeLabel: "Несколько",
        },
        {
            id: 3,
            text: "Что можно улучшить в компании?",
            type: "text",
            typeLabel: "Текст",
        },
    ])

    const [activeQuestionId, setActiveQuestionId] = useState(1)

    const addQuestion = () => {
        const newId = questions.length ? Math.max(...questions.map(q => q.id)) + 1 : 1

        setQuestions([
            ...questions,
            {
                id: newId,
                text: "Новый вопрос",
                type: "single",
                typeLabel: "Один вариант",
            },
        ])

        setActiveQuestionId(newId)
    }

    const deleteQuestion = (id) => {
        setQuestions(questions.filter(q => q.id !== id))

        if (activeQuestionId === id) {
            setActiveQuestionId(questions[0]?.id || null)
        }
    }

    const duplicateQuestion = (question) => {
        const newId = Math.max(...questions.map(q => q.id)) + 1

        setQuestions([
            ...questions,
            {
                ...question,
                id: newId,
                text: question.text + " копия",
            },
        ])

        setActiveQuestionId(newId)
    }

    const updateQuestionText = (id, value) => {
        setQuestions(
            questions.map(q =>
                q.id === id ? { ...q, text: value } : q
            )
        )
    }

    const updateQuestionType = (id, type, typeLabel) => {
        setQuestions(
            questions.map(q =>
                q.id === id
                    ? {
                        ...q,
                        type,
                        typeLabel,
                        options:
                            type === "single" || type === "multiple"
                                ? (q.options?.length ? q.options : ["Вариант 1"])
                                : [],
                        allowOwnAnswer: q.allowOwnAnswer || false,
                    }
                    : q
            )
        )
    }

    const updateOption = (questionId, index, value) => {
        setQuestions(
            questions.map(q =>
                q.id === questionId
                    ? {
                        ...q,
                        options: q.options.map((o, i) =>
                            i === index ? value : o
                        )
                    }
                    : q
            )
        )
    }

    const addOption = (questionId) => {
        setQuestions(
            questions.map(q =>
                q.id === questionId
                    ? {
                        ...q,
                        options: [
                            ...(q.options || []),
                            `Вариант ${(q.options || []).length + 1}`
                        ]
                    }
                    : q
            )
        )
    }

    const removeOption = (questionId, index) => {
        setQuestions(
            questions.map(q =>
                q.id === questionId
                    ? {
                        ...q,
                        options: q.options.filter((_, i) => i !== index)
                    }
                    : q
            )
        )
    }
    return (
        <div className="page active">
            <div className="topbar">
                <div className="topbar-title">Создать опрос</div>

                <div className="topbar-actions">
                    <button className="btn btn-secondary">Сохранить черновик</button>

                    <button className="btn btn-primary">
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" />
                        </svg>
                        Опубликовать
                    </button>
                </div>
            </div>

            <div style={{ padding: "28px" }}>
                <div className="create-mode-picker">
                    <div
                        className={`mode-card ${createMode === "manual" ? "selected-manual" : ""}`}
                        onClick={() => setCreateMode("manual")}
                    >
                        <div className="mode-card-icon manual-icon">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                            </svg>
                        </div>

                        <div className="mode-card-title">Создать вручную</div>

                        <div className="mode-card-desc">
                            Заполните форму самостоятельно — добавляйте вопросы, выбирайте типы ответов и настраивайте опрос под свои нужды.
                        </div>
                    </div>

                    <div
                        className={`mode-card ${createMode === "ai" ? "selected-ai" : ""}`}
                        onClick={() => setCreateMode("ai")}
                    >
                        <div className="mode-selected-dot">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                        </div>

                        <div className="mode-card-icon ai-icon">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" />
                            </svg>
                        </div>

                        <div className="mode-card-title">
                            Создать с помощью AI <span className="ai-badge-inline">NEW</span>
                        </div>

                        <div className="mode-card-desc">
                            Опишите цель опроса — AI сгенерирует структуру, вопросы и типы ответов за секунды. Вы можете отредактировать результат.
                        </div>
                    </div>
                </div>

                {createMode === "ai" && (
                    <div className="ai-create-panel">
                        <div className="ai-input-panel">
                            <div className="ai-input-inner">
                                <div className="ai-panel-label">
                                    <svg viewBox="0 0 20 20" fill="currentColor">
                                        <path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" />
                                    </svg>
                                    Powered by Claude · Опишите ваш опрос
                                </div>

                                <textarea
                                    className="ai-prompt-area"
                                    rows="3"
                                    placeholder="Например: Нам нужен квартальный пульс-опрос для 200 сотрудников. Хотим понять уровень вовлечённости, отношение к remote-формату и запросы по обучению. Тон — дружелюбный, анонимный."
                                />

                                <div className="ai-quick-prompts">
                                    <span style={{ fontSize: "11px", color: "rgba(255,255,255,.4)", alignSelf: "center" }}>
                                        Быстрый старт:
                                    </span>

                                    <button className="ai-quick-btn">Пульс-опрос сотрудников</button>
                                    <button className="ai-quick-btn">NPS после поддержки</button>
                                    <button className="ai-quick-btn">Оценка онбординга</button>
                                    <button className="ai-quick-btn">Опрос после события</button>
                                    <button className="ai-quick-btn">360° оценка руководителя</button>
                                    <button className="ai-quick-btn">Exit interview</button>
                                </div>

                                <div className="ai-settings-row">
                                    <select className="ai-select">
                                        <option>🎯 Аудитория: Сотрудники</option>
                                    </select>

                                    <select className="ai-select">
                                        <option>📝 Тон: Формальный</option>
                                    </select>

                                    <select className="ai-select">
                                        <option>5 вопросов</option>
                                    </select>

                                    <select className="ai-select">
                                        <option>🔒 Анонимно</option>
                                    </select>

                                    <button className="ai-generate-btn">
                                        <svg viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" />
                                        </svg>
                                        Сгенерировать опрос
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                <div className="create-layout">
                    <div>
                        <div className="card" style={{ marginBottom: "16px" }}>
                            <div className="card-header">
                                <div className="card-title">Основная информация</div>
                            </div>

                            <div className="card-body">
                                <div className="form-group">
                                    <label className="form-label">Название опроса</label>
                                    <input className="form-input" placeholder="Оценка удовлетворённости сотрудников Q2" />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Описание <span>(необязательно)</span></label>
                                    <textarea className="form-textarea" placeholder="Помогите нам стать лучше — пройдите короткий опрос о вашем опыте работы. Это займёт около 3 минут." />
                                </div>

                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                                    <div className="form-group" style={{ marginBottom: 0 }}>
                                        <label className="form-label">Тип опроса</label>
                                        <select className="form-select">
                                            <option>Корпоративный</option>
                                            <option>Клиентский</option>
                                            <option>Публичный</option>
                                        </select>
                                    </div>

                                    <div className="form-group" style={{ marginBottom: 0 }}>
                                        <label className="form-label">Язык</label>
                                        <select className="form-select">
                                            <option>Русский</option>
                                            <option>English</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="card">
                            <div className="card-header">
                                <div className="card-title">Вопросы</div>
                                <span className="chip">{questions.length} вопросов</span>
                            </div>

                            <div className="card-body">
                                <div className="question-list">
                                    {questions.map((question, index) => (
                                        <div className="question-card" key={question.id}>
                                            <div
                                                className="question-header"
                                                onClick={() => setActiveQuestionId(question.id)}
                                            >
                                                <span className="q-drag">⋮⋮</span>
                                                <span className="q-number">{index + 1}</span>
                                                <span className="q-title">{question.text}</span>
                                                <span className="q-type-tag">{question.typeLabel}</span>
                                            </div>

                                            {activeQuestionId === question.id && (
                                                <div className="question-body open">
                                                    <div className="form-group">
                                                        <label className="form-label">Формулировка вопроса</label>
                                                        <input
                                                            className="form-input"
                                                            value={question.text}
                                                            onChange={(e) => updateQuestionText(question.id, e.target.value)}
                                                        />
                                                    </div>

                                                    <div className="form-group" style={{ marginBottom: 0 }}>
                                                        <label className="form-label">Тип ответа</label>

                                                        <div className="type-picker">
                                                            <div
                                                                className={`type-option ${question.type === "single" ? "selected" : ""}`}
                                                                onClick={() => updateQuestionType(question.id, "single", "Один вариант")}
                                                            >
                                                                Один вариант
                                                            </div>

                                                            <div
                                                                className={`type-option ${question.type === "multiple" ? "selected" : ""}`}
                                                                onClick={() => updateQuestionType(question.id, "multiple", "Несколько")}
                                                            >
                                                                Несколько
                                                            </div>

                                                            <div
                                                                className={`type-option ${question.type === "scale" ? "selected" : ""}`}
                                                                onClick={() => updateQuestionType(question.id, "scale", "Шкала")}
                                                            >
                                                                Шкала 1–10
                                                            </div>

                                                            <div
                                                                className={`type-option ${question.type === "text" ? "selected" : ""}`}
                                                                onClick={() => updateQuestionType(question.id, "text", "Текст")}
                                                            >
                                                                Текст
                                                            </div>
                                                        </div>
                                                        {(question.type === "single" ||
                                                            question.type === "multiple") && (

                                                                <div className="options-block">

                                                                    <label className="form-label">
                                                                        Варианты ответа
                                                                    </label>

                                                                    {(question.options || []).map((option, index) => (

                                                                        <div
                                                                            className="option-row"
                                                                            key={index}
                                                                        >

                                                                            <input
                                                                                className="form-input"
                                                                                value={option}
                                                                                onChange={(e) =>
                                                                                    updateOption(
                                                                                        question.id,
                                                                                        index,
                                                                                        e.target.value
                                                                                    )
                                                                                }
                                                                            />

                                                                            <button
                                                                                type="button"
                                                                                className="option-delete"
                                                                                onClick={() =>
                                                                                    removeOption(
                                                                                        question.id,
                                                                                        index
                                                                                    )
                                                                                }
                                                                            >
                                                                                ×
                                                                            </button>

                                                                        </div>

                                                                    ))}

                                                                    <button
                                                                        type="button"
                                                                        className="add-option-btn"
                                                                        onClick={() =>
                                                                            addOption(question.id)
                                                                        }
                                                                    >
                                                                        ＋ Добавить вариант
                                                                    </button>
                                                                    <label className="own-answer-row">
                                                                        <input
                                                                            type="checkbox"
                                                                            checked={question.allowOwnAnswer || false}
                                                                            onChange={(e) =>
                                                                                setQuestions(
                                                                                    questions.map(q =>
                                                                                        q.id === question.id
                                                                                            ? { ...q, allowOwnAnswer: e.target.checked }
                                                                                            : q
                                                                                    )
                                                                                )
                                                                            }
                                                                        />
                                                                        Разрешить свой ответ
                                                                    </label>
                                                                </div>

                                                            )}
                                                    </div>

                                                    {question.type === "scale" && (
                                                        <>
                                                            <div className="scale-preview">
                                                                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                                                                    <div className="scale-btn" key={n}>{n}</div>
                                                                ))}
                                                            </div>

                                                            <div className="scale-labels">
                                                                <span>Совсем не доволен</span>
                                                                <span>Очень доволен</span>
                                                            </div>
                                                        </>
                                                    )}

                                                    <div className="divider"></div>

                                                    <div style={{ display: "flex", gap: "8px" }}>
                                                        <button
                                                            className="btn btn-ghost btn-sm"
                                                            onClick={() => duplicateQuestion(question)}
                                                        >
                                                            Дублировать
                                                        </button>

                                                        <button
                                                            className="btn btn-danger btn-sm"
                                                            onClick={() => deleteQuestion(question.id)}
                                                        >
                                                            Удалить
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>

                                <div className="add-question-bar" onClick={addQuestion}>
                                    <span className="aq-label">Добавить вопрос</span>
                                </div>

                                <div className="add-question-bar">
                                    <span className="aq-label">Добавить вопрос</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div>
                        <div className="settings-panel">
                            <div className="settings-panel-title">Настройки</div>

                            <div className="setting-block">
                                <div className="settings-label">Количество участников</div>
                                <div className="settings-hint">Максимум человек, которые могут пройти опрос</div>

                                <div className="participants-control">

                                    <input
                                        className={`form-input participants-input ${unlimited ? "disabled" : ""
                                            }`}
                                        type="number"
                                        value={participants}
                                        disabled={unlimited}
                                        onChange={(e) =>
                                            setParticipants(e.target.value)
                                        }
                                    />

                                    <span>человек</span>

                                </div>

                                <label className="unlimited-check">

                                    <input
                                        type="checkbox"
                                        checked={unlimited}
                                        onChange={() =>
                                            setUnlimited(!unlimited)
                                        }
                                    />

                                    Без ограничений

                                </label>
                            </div>

                            <div className="setting-toggle-row">
                                <div>
                                    <div className="settings-label">Показать прогресс</div>
                                    <div className="settings-hint">Шкала прогресса в опросе</div>
                                </div>
                                <div
                                    className={`toggle ${showProgress ? "on" : ""}`}
                                    onClick={() =>
                                        setShowProgress(!showProgress)
                                    }
                                />
                            </div>

                        </div>
                    </div>
                </div>

                <div className="section-header" style={{ marginTop: "28px", marginBottom: "16px" }}>
                    <div className="section-title">Предпросмотр опроса</div>
                    <span style={{ fontSize: "13px", color: "var(--gray-400)" }}>
                        Так видят опрос участники
                    </span>
                </div>

                <div style={{ background: "var(--gray-100)", borderRadius: "var(--radius)", padding: "28px" }}>
                    <div className="survey-shell">
                        <div className="survey-hero">
                            <div className="survey-company">TechCorp · Корпоративный опрос</div>
                            <div className="survey-title-big">Оценка удовлетворённости сотрудников Q2</div>
                            <div className="survey-desc">
                                Помогите нам стать лучше — пройдите короткий опрос о вашем опыте работы. Это займёт около 3 минут.
                            </div>
                        </div>

                        <div className="survey-progress-wrap">
                            <div className="survey-progress-label">
                                <span>Вопрос 2 из 5</span>
                                <span>40%</span>
                            </div>
                            <div className="progress-bar">
                                <div className="progress-fill" style={{ width: "40%" }}></div>
                            </div>
                        </div>

                        <div className="survey-body">
                            <div className="sq-block">
                                <div className="sq-label">
                                    Что вам больше всего нравится в вашей работе?<span className="sq-required">*</span>
                                </div>

                                <div className="sq-hint">Можно выбрать несколько вариантов</div>

                                <div className="check-option">Интересные задачи</div>
                                <div className="check-option selected">Команда и коллеги</div>
                                <div className="check-option">Гибкий график</div>
                                <div className="check-option selected">Возможности роста</div>
                            </div>

                            <div className="survey-footer">
                                <button className="btn btn-secondary">← Назад</button>
                                <div style={{ fontSize: "12px", color: "var(--gray-400)" }}>Вопрос 2 из 5</div>
                                <button className="btn btn-primary">Далее →</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}