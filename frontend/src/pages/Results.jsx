import { useState } from "react"
import html2canvas from "html2canvas"
import jsPDF from "jspdf"
import { apiRequest } from "../api/client"

// ─── AI Analytics ─────────────────────────────────────────────────────────────

/**
 * Запрашивает AI-аналитику по результатам опроса.
 * @param {object} pollResults - объект результатов (selectedResults)
 */
function fetchAiAnalytics(pollResults) {
    return apiRequest("/api/v1/ai/ai_analytics?use_cookie=false&token_type=access", {
        method: "POST",
        body: JSON.stringify(pollResults),
    })
}

// ─── AI Analytics UI ──────────────────────────────────────────────────────────

function AiAnalyticsPanel({ results }) {
    const [analytics, setAnalytics] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState("")

    const handleGenerate = async () => {
        if (!results) return
        setLoading(true)
        setError("")
        setAnalytics(null)
        try {
            const data = await fetchAiAnalytics(results)
            setAnalytics(data)
        } catch (err) {
            setError(err.message || "Не удалось получить AI-аналитику")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="card no-print" style={{ marginTop: 20 }}>
            <div className="card-header">
                <div className="card-title">AI-аналитика</div>
                <span className="ai-badge-inline">AI</span>
            </div>

            <div className="card-body">

                {/* Кнопка запуска */}
                {!analytics && !loading && (
                    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                        <div className="chat-msg ai">
                            <div className="chat-avatar ai-av">✦</div>
                            <div className="chat-bubble">
                                Нажми кнопку — AI проанализирует текстовые ответы и выдаст резюме, тональность, темы и рекомендации.
                            </div>
                        </div>

                        {error && (
                            <div style={{
                                background: "#FEF2F2",
                                border: "1px solid #FECACA",
                                color: "#B91C1C",
                                borderRadius: "8px",
                                padding: "10px 14px",
                                fontSize: "13px",
                            }}>
                                {error}
                            </div>
                        )}

                        <button
                            className="btn btn-primary"
                            onClick={handleGenerate}
                            disabled={!results}
                            style={{ alignSelf: "flex-start" }}
                        >
                            ✦ Сгенерировать аналитику
                        </button>
                    </div>
                )}

                {/* Лоадер */}
                {loading && (
                    <div className="chat-msg ai">
                        <div className="chat-avatar ai-av">✦</div>
                        <div className="chat-bubble" style={{ color: "var(--gray-400)" }}>
                            Анализирую ответы…
                        </div>
                    </div>
                )}

                {/* Результат */}
                {analytics && (
                    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

                        {/* Резюме */}
                        {analytics.summary && (
                            <div className="chat-msg ai">
                                <div className="chat-avatar ai-av">✦</div>
                                <div className="chat-bubble">{analytics.summary}</div>
                            </div>
                        )}

                        {/* Тональность */}
                        {analytics.sentiment && (
                            <div>
                                <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--gray-400)", textTransform: "uppercase", letterSpacing: ".05em", marginBottom: "10px" }}>
                                    Тональность
                                </div>
                                <div style={{ display: "flex", gap: "10px", marginBottom: "8px" }}>
                                    <SentimentBadge label="Позитив" data={analytics.sentiment.positive} color="#10B981" />
                                    <SentimentBadge label="Нейтраль" data={analytics.sentiment.neutral} color="#6B7280" />
                                    <SentimentBadge label="Негатив" data={analytics.sentiment.negative} color="#EF4444" />
                                </div>
                                {analytics.sentiment.conclusion && (
                                    <div style={{ fontSize: "13px", color: "var(--gray-600)", fontStyle: "italic" }}>
                                        {analytics.sentiment.conclusion}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Темы */}
                        {analytics.themes?.length > 0 && (
                            <div>
                                <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--gray-400)", textTransform: "uppercase", letterSpacing: ".05em", marginBottom: "10px" }}>
                                    Темы
                                </div>
                                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                                    {analytics.themes.map((theme, i) => (
                                        <div key={i} style={{
                                            background: "var(--gray-50)",
                                            border: "1px solid var(--gray-200)",
                                            borderRadius: "8px",
                                            padding: "10px 14px",
                                        }}>
                                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: theme.quotes?.length ? "6px" : 0 }}>
                                                <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--gray-800)" }}>{theme.theme}</span>
                                                <span style={{ fontSize: "12px", color: "var(--gray-400)" }}>{theme.count} упом.</span>
                                            </div>
                                            {theme.quotes?.length > 0 && (
                                                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                                                    {theme.quotes.slice(0, 2).map((q, qi) => (
                                                        <div key={qi} style={{ fontSize: "12px", color: "var(--gray-500)", fontStyle: "italic" }}>
                                                            «{q}»
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Инсайты */}
                        {analytics.insights?.length > 0 && (
                            <div>
                                <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--gray-400)", textTransform: "uppercase", letterSpacing: ".05em", marginBottom: "10px" }}>
                                    Ключевые инсайты
                                </div>
                                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                                    {analytics.insights.map((insight, i) => (
                                        <div key={i} style={{
                                            display: "flex",
                                            alignItems: "flex-start",
                                            gap: "10px",
                                            background: "var(--gray-50)",
                                            border: "1px solid var(--gray-200)",
                                            borderRadius: "8px",
                                            padding: "10px 14px",
                                        }}>
                                            <span style={{ fontSize: "18px", lineHeight: 1 }}>{insight.emoji}</span>
                                            <span style={{ fontSize: "13px", color: "var(--gray-700)", lineHeight: "1.5" }}>{insight.text}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Рекомендации */}
                        {analytics.recommendations?.length > 0 && (
                            <div>
                                <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--gray-400)", textTransform: "uppercase", letterSpacing: ".05em", marginBottom: "10px" }}>
                                    Рекомендации
                                </div>
                                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                                    {analytics.recommendations.map((rec, i) => (
                                        <div key={i} style={{
                                            display: "flex",
                                            alignItems: "flex-start",
                                            gap: "10px",
                                            background: "var(--gray-50)",
                                            border: "1px solid var(--gray-200)",
                                            borderRadius: "8px",
                                            padding: "10px 14px",
                                        }}>
                                            <span style={{
                                                fontSize: "10px",
                                                fontWeight: 800,
                                                padding: "2px 8px",
                                                borderRadius: "20px",
                                                background: rec.priority_color || "#E5E7EB",
                                                color: "#fff",
                                                whiteSpace: "nowrap",
                                                marginTop: "2px",
                                                flexShrink: 0,
                                            }}>
                                                {rec.priority === "high" ? "Высокий" : rec.priority === "medium" ? "Средний" : "Низкий"}
                                            </span>
                                            <span style={{ fontSize: "13px", color: "var(--gray-700)", lineHeight: "1.5" }}>{rec.text}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Кнопка обновить */}
                        <button
                            className="btn btn-ghost btn-sm"
                            onClick={handleGenerate}
                            disabled={loading}
                            style={{ alignSelf: "flex-start" }}
                        >
                            Обновить анализ
                        </button>

                    </div>
                )}
            </div>
        </div>
    )
}

function SentimentBadge({ label, data, color }) {
    return (
        <div style={{
            flex: 1,
            background: "var(--gray-50)",
            border: "1px solid var(--gray-200)",
            borderRadius: "8px",
            padding: "10px 12px",
            textAlign: "center",
        }}>
            <div style={{ fontSize: "18px", fontWeight: 900, color }}>{data?.percentage ?? 0}%</div>
            <div style={{ fontSize: "12px", color: "var(--gray-500)" }}>{label}</div>
            <div style={{ fontSize: "11px", color: "var(--gray-400)" }}>{data?.count ?? 0} отв.</div>
        </div>
    )
}

// ─── Main Results component ───────────────────────────────────────────────────

export default function Results({
    surveys,
    selectedPoll,
    selectedResults,
    openResults,
    getStatusText,
    formatDate,
}) {
    const [copied, setCopied] = useState(false)

    const handleShare = () => {
        if (!selectedPoll) return
        const link = `${window.location.origin}/poll/${selectedPoll.id}`
        navigator.clipboard.writeText(link).then(() => {
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        })
    }
    const handleExportPdf = async () => {
        const element = document.querySelector(".results-print-area")

        if (!element) return

        const canvas = await html2canvas(element, {
            scale: 2,
            backgroundColor: "#ffffff",
            useCORS: true,
        })

        const imgData = canvas.toDataURL("image/png")

        const pdf = new jsPDF("p", "mm", "a4")

        const pageWidth = pdf.internal.pageSize.getWidth()
        const pageHeight = pdf.internal.pageSize.getHeight()

        const imgWidth = pageWidth
        const imgHeight = (canvas.height * imgWidth) / canvas.width

        let heightLeft = imgHeight
        let position = 0

        pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight)
        heightLeft -= pageHeight

        while (heightLeft > 0) {
            position = heightLeft - imgHeight
            pdf.addPage()
            pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight)
            heightLeft -= pageHeight
        }

        pdf.save(`results-${selectedPoll?.title || "poll"}.pdf`)
    }

    const totalAnswers =
        selectedResults?.total_responses ??
        selectedResults?.total_votes ??
        selectedResults?.responses_count ??
        selectedPoll?.total_votes ??
        0

    const maxParticipants =
        selectedPoll?.max_participants || null

    const responseRate =
        maxParticipants
            ? Math.round((totalAnswers / maxParticipants) * 100)
            : null

    const avgTime =
        selectedResults?.avg_completion_time ??
        selectedResults?.average_completion_time ??
        selectedResults?.avg_time ??
        null

    const questions =
        selectedResults?.questions ??
        selectedResults?.question_results ??
        selectedResults?.results ??
        []

    const getQuestionTitle = (question, index) =>
        question.text || question.title || question.question || `Вопрос ${index + 1}`

    const getOptions = (question) =>
        question.options ||
        question.answers_distribution ||
        question.choices ||
        []

    const getTextAnswers = (question) =>
        question.answers ||
        question.responses ||
        question.text_answers ||
        []

    const getOptionCount = (option) =>
        option.count ??
        option.votes ??
        option.total ??
        option.responses_count ??
        0

    const getOptionLabel = (option, index) =>
        option.text || option.label || option.title || `Вариант ${index + 1}`

    return (
        <div className="page active">
            <div className="topbar">
                <div className="topbar-title">
                    Результаты — {selectedPoll?.title || "Опрос"}
                </div>

                <div className="topbar-actions no-print">
                    <button
                        className="btn btn-secondary"
                        onClick={handleExportPdf}
                    >
                        Скачать PDF
                    </button>

                    <button className="btn btn-primary" onClick={handleShare} disabled={!selectedPoll}>
                        {copied ? "Ссылка скопирована ✓" : "Поделиться"}
                    </button>
                </div>
            </div>

            {!selectedPoll && (
                <div className="dashboard-content">
                    <div className="results-picker-card no-print">
                        <div className="results-picker-left">
                            <div className="results-picker-label">Опрос</div>

                            <select
                                className="results-picker-select"
                                value=""
                                onChange={(e) => {
                                    const poll = surveys.find(
                                        p => String(p.id) === e.target.value
                                    )

                                    if (poll) openResults(poll)
                                }}
                            >
                                <option value="">Выберите опрос</option>

                                {surveys.map((poll) => (
                                    <option key={poll.id} value={poll.id}>
                                        {poll.title} • {formatDate(poll.created_at)}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="results-empty-hero">
                        <div className="results-empty-orbit">
                            <span>📊</span>
                        </div>

                        <h2>Выберите опрос для анализа</h2>

                        <p>
                            Откройте выпадающий список выше и выберите нужный опрос, чтобы посмотреть ответы, метрики и аналитику.
                        </p>
                    </div>
                </div>
            )}

            <div className="dashboard-content results-print-area" style={{ display: selectedPoll ? undefined : "none" }}>
                <div className="results-picker-card no-print">
                    <div className="results-picker-left">
                        <div className="results-picker-label">Опрос</div>

                        <select
                            className="results-picker-select"
                            value={selectedPoll?.id || ""}
                            onChange={(e) => {
                                const poll = surveys.find(
                                    p => String(p.id) === e.target.value
                                )

                                if (poll) openResults(poll)
                            }}
                        >
                            {surveys.map((poll) => (
                                <option key={poll.id} value={poll.id}>
                                    {poll.title} • {formatDate(poll.created_at)}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="results-picker-divider" />

                    <div className="results-picker-meta">
                        <div className="results-picker-meta-item strong">
                            👥 {totalAnswers}
                            {maxParticipants ? ` / ${maxParticipants}` : ""}
                            <span>ответов</span>
                        </div>

                        <span className={`status-badge ${selectedPoll?.status}`}>
                            {getStatusText(selectedPoll?.status)}
                        </span>

                        <div className="results-picker-date">
                            {formatDate(selectedPoll?.expires_at || selectedPoll?.created_at)}
                        </div>
                    </div>
                </div>

                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-icon green"></div>
                        <div className="stat-label">Ответов</div>
                        <div className="stat-value">{totalAnswers}</div>
                        <div className="stat-delta">
                            {maxParticipants
                                ? `из ${maxParticipants} приглашённых`
                                : "получено всего"}
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-icon indigo"></div>
                        <div className="stat-label">Отклик</div>
                        <div className="stat-value">
                            {responseRate !== null ? `${responseRate}%` : "—"}
                        </div>
                        <div className="stat-delta">
                            {maxParticipants ? "по лимиту участников" : "лимит не задан"}
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-icon amber"></div>
                        <div className="stat-label">Ср. время заполнения</div>
                        <div className="stat-value">
                            {avgTime ? `${Math.round(avgTime)}с` : "—"}
                        </div>
                        <div className="stat-delta">
                            {avgTime ? "среднее по всем участникам" : "данных пока нет"}
                        </div>
                    </div>
                </div>

                <div className="results-grid">
                    {questions.length > 0 ? (
                        questions.map((question, questionIndex) => {
                            const options = getOptions(question)
                            const textAnswers = getTextAnswers(question)

                            return (
                                <div
                                    className={`result-card ${question.type === "text" || !options.length
                                        ? "full"
                                        : ""
                                        }`}
                                    key={question.id || questionIndex}
                                >
                                    <div className="rc-title">
                                        Вопрос {questionIndex + 1} — {getQuestionTitle(question, questionIndex)}
                                    </div>

                                    {options.length > 0 ? (
                                        <div className="bar-chart">
                                            {options.map((option, optionIndex) => {
                                                const count = getOptionCount(option)

                                                const percent =
                                                    totalAnswers > 0
                                                        ? Math.round((count / totalAnswers) * 100)
                                                        : 0

                                                return (
                                                    <div
                                                        className="bar-row"
                                                        key={option.id || optionIndex}
                                                    >
                                                        <div className="bar-label">
                                                            {getOptionLabel(option, optionIndex)}
                                                        </div>

                                                        <div className="bar-track">
                                                            <div
                                                                className="bar-fill"
                                                                style={{ width: `${percent}%` }}
                                                            >
                                                                {percent > 0 ? `${percent}%` : ""}
                                                            </div>
                                                        </div>

                                                        <div className="bar-pct">
                                                            {count}
                                                        </div>
                                                    </div>
                                                )
                                            })}
                                        </div>
                                    ) : (
                                        <div className="response-feed">
                                            {textAnswers.length > 0 ? (
                                                textAnswers.slice(0, 5).map((answer, answerIndex) => (
                                                    <div
                                                        className="response-item"
                                                        key={answerIndex}
                                                    >
                                                        {typeof answer === "string"
                                                            ? answer
                                                            : answer.text || answer.value || "Ответ без текста"}

                                                        {typeof answer !== "string" && answer.created_at && (
                                                            <div className="response-meta">
                                                                {formatDate(answer.created_at)}
                                                            </div>
                                                        )}
                                                    </div>
                                                ))
                                            ) : (
                                                <div className="empty-state compact">
                                                    <div className="empty-title">
                                                        Пока нет ответов по этому вопросу
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )
                        })
                    ) : (
                        <div className="result-card full">
                            <div className="empty-state">
                                <div className="empty-icon">📊</div>

                                <div className="empty-title">
                                    Пока нет результатов
                                </div>

                                <div className="empty-text">
                                    Когда пользователи начнут отвечать — здесь появится аналитика
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* AI-аналитика */}
                <AiAnalyticsPanel results={selectedResults} />

            </div>
        </div>
    )
}
