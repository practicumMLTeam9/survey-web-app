import html2canvas from "html2canvas"
import jsPDF from "jspdf"

export default function Results({
    surveys,
    selectedPoll,
    selectedResults,
    openResults,
    getStatusText,
    formatDate,
}) {
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

                    <button className="btn btn-primary">
                        Поделиться
                    </button>
                </div>
            </div>

            <div className="dashboard-content results-print-area">
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
                                    {poll.title}
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
                            {avgTime ? "из API" : "нет в API"}
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

                <div className="card no-print" style={{ marginTop: 20 }}>
                    <div className="card-header">
                        <div className="card-title">
                            Спросить AI про этот опрос
                        </div>

                        <span className="ai-badge-inline">
                            AI
                        </span>
                    </div>

                    <div className="card-body">
                        <div className="chat-msg ai">
                            <div className="chat-avatar ai-av">
                                ✦
                            </div>

                            <div className="chat-bubble">
                                AI-анализ будет доступен после подключения backend endpoint.
                            </div>
                        </div>

                        <div className="chat-input-row">
                            <input
                                className="chat-input"
                                placeholder="AI-анализ пока недоступен"
                                disabled
                            />

                            <button className="btn btn-primary" disabled>
                                ↑
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}