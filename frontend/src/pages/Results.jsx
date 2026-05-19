export default function Results({
    surveys,
    selectedPoll,
    selectedResults,
    openResults,
    getStatusText,
    formatDate,
}) {
    const totalVotes =
        selectedResults?.total_votes ??
        selectedResults?.total_responses ??
        selectedPoll?.total_votes ??
        0

    const maxParticipants =
        selectedPoll?.max_participants || null

    const responseRate =
        maxParticipants && totalVotes
            ? Math.round((totalVotes / maxParticipants) * 100)
            : null

    return (
        <div className="page active">
            <div className="topbar">
                <div className="topbar-title">
                    Результаты
                    {selectedPoll && ` — ${selectedPoll.title}`}
                </div>

                <div className="topbar-actions">
                    <button className="btn btn-secondary">
                        Скачать PDF
                    </button>

                    <button className="btn btn-primary">
                        Поделиться
                    </button>
                </div>
            </div>

            <div style={{ padding: "28px" }}>
                <div className="rsp-card">
                    <span className="rsp-label">
                        Опрос
                    </span>

                    <div className="rsp-select-wrap">
                        <select
                            className="rsp-select"
                            value={selectedPoll?.id || ""}
                            onChange={(e) => {
                                const poll = surveys.find(
                                    p => String(p.id) === e.target.value
                                )

                                if (poll) {
                                    openResults(poll)
                                }
                            }}
                        >
                            <option value="">
                                Выберите опрос
                            </option>

                            {surveys.map((poll) => (
                                <option key={poll.id} value={poll.id}>
                                    {poll.title}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="rsp-divider"></div>

                    <div className="rsp-meta">
                        <div className="rsp-meta-item">
                            <strong>
                                {totalVotes}
                                {maxParticipants ? ` / ${maxParticipants}` : ""}
                            </strong>
                            ответов
                        </div>

                        {selectedPoll && (
                            <div className="rsp-meta-item">
                                <span className={`status-badge ${selectedPoll.status}`}>
                                    {getStatusText(selectedPoll.status)}
                                </span>
                            </div>
                        )}

                        <div className="rsp-meta-item">
                            <span style={{ color: "var(--gray-400)", fontSize: "12px" }}>
                                {formatDate(selectedPoll?.expires_at || selectedPoll?.created_at)}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="stats-grid" style={{ marginBottom: "20px" }}>
                    <div className="stat-card">
                        <div className="stat-icon green"></div>
                        <div className="stat-label">Ответов</div>
                        <div className="stat-value">{totalVotes}</div>
                        <div className="stat-delta">
                            {maxParticipants ? `из ${maxParticipants} приглашённых` : "всего получено"}
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-icon indigo"></div>
                        <div className="stat-label">Отклик</div>
                        <div className="stat-value">
                            {responseRate !== null ? `${responseRate}%` : "—"}
                        </div>
                        <div className="stat-delta muted">
                            {responseRate !== null ? "рассчитано по лимиту участников" : "нет лимита участников"}
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-icon amber"></div>
                        <div className="stat-label">Ср. время заполнения</div>
                        <div className="stat-value">—</div>
                        <div className="stat-delta">нет в API</div>
                    </div>
                </div>

                {!selectedResults ? (
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
                ) : (
                    <div className="results-grid">
                        <div className="result-card">
                            <div className="rc-title">
                                Сводка по ответам
                            </div>

                            <div className="nps-gauge">
                                <div className="nps-score">
                                    {totalVotes}
                                </div>

                                <div className="nps-label">
                                    всего ответов
                                </div>
                            </div>
                        </div>

                        <div className="result-card">
                            <div className="rc-title">
                                Распределение
                            </div>

                            <div className="bar-chart">
                                <div className="bar-row">
                                    <div className="bar-label">Получено</div>
                                    <div className="bar-track">
                                        <div
                                            className="bar-fill"
                                            style={{
                                                width: `${responseRate || 0}%`,
                                            }}
                                        >
                                            {responseRate || 0}%
                                        </div>
                                    </div>
                                    <div className="bar-pct">{totalVotes}</div>
                                </div>
                            </div>
                        </div>

                        <div className="result-card full">
                            <div className="rc-title">
                                Данные API
                            </div>

                            <pre style={{ whiteSpace: "pre-wrap" }}>
                                {JSON.stringify(selectedResults, null, 2)}
                            </pre>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}