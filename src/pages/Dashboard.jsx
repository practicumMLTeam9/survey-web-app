export default function Dashboard() {
    return (
        <>
            <aside className="sidebar">
                <div className="sidebar-logo">
                    <div className="logo-icon">
                        <svg viewBox="0 0 20 20">
                            <path d="M2 4h16v2H2V4zm0 5h10v2H2V9zm0 5h13v2H2v-2z" />
                        </svg>
                    </div>
                    <span className="logo-text">SurveyPulse</span>
                    <span className="logo-badge">BETA</span>
                </div>

                <nav className="sidebar-nav">
                    <div className="nav-section">
                        <div className="nav-label">Меню</div>

                        <div className="nav-item active">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path d="M3 4a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 8a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H4a1 1 0 01-1-1v-4zm8-8a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V4zm0 8a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                            </svg>
                            Дашборд
                        </div>

                        <div className="nav-item">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M3 5a1 1 0 000 2h14a1 1 0 100-2H3zm0 4a1 1 0 000 2h14a1 1 0 100-2H3zm0 4a1 1 0 000 2h8a1 1 0 100-2H3z" clipRule="evenodd" />
                            </svg>
                            Опросы
                            <span className="nav-badge">4</span>
                        </div>

                        <div className="nav-item">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                            </svg>
                            Создать опрос
                        </div>

                        <div className="nav-item">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zm6-4a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zm6-3a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                            </svg>
                            Результаты
                        </div>
                    </div>

                    <div className="nav-section">
                        <div className="nav-label">Управление</div>

                        <div className="nav-item">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                                <path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd" />
                            </svg>
                            Подписка
                        </div>

                        <div className="nav-item">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                            </svg>
                            Настройки
                        </div>
                    </div>
                </nav>

                <div className="sidebar-bottom">
                    <div className="user-card">
                        <div className="avatar">АК</div>
                        <div className="user-info">
                            <div className="user-name">Алексей Козлов</div>
                            <div className="user-role">Администратор</div>
                        </div>
                    </div>

                    <div className="nav-item" style={{ marginTop: "8px" }}>
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path
                                fillRule="evenodd"
                                d="M3 4a1 1 0 011-1h6a1 1 0 110 2H5v10h5a1 1 0 110 2H4a1 1 0 01-1-1V4zm10.293 2.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L14.586 11H9a1 1 0 110-2h5.586l-1.293-1.293a1 1 0 010-1.414z"
                                clipRule="evenodd"
                            />
                        </svg>
                        Выйти из аккаунта
                    </div>
                </div>
            </aside>

            <main className="main">
                <div className="page active">
                    <div className="topbar">
                        <div className="topbar-title">Дашборд</div>
                        <div className="topbar-actions">
                            <button className="btn btn-primary">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                                </svg>
                                Новый опрос
                            </button>
                        </div>
                    </div>

                    <div style={{ padding: "28px" }}>
                        <div className="stats-grid">
                            <div className="stat-card">
                                <div className="stat-icon indigo">
                                    <svg viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M3 5a1 1 0 000 2h14a1 1 0 100-2H3zm0 4a1 1 0 000 2h14a1 1 0 100-2H3zm0 4a1 1 0 000 2h8a1 1 0 100-2H3z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <div className="stat-label">Всего опросов</div>
                                <div className="stat-value">12</div>
                                <div className="stat-delta up">↑ 3 за месяц</div>
                            </div>

                            <div className="stat-card">
                                <div className="stat-icon green">
                                    <svg viewBox="0 0 20 20" fill="currentColor">
                                        <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zm8 0a3 3 0 11-6 0 3 3 0 016 0zm-4.07 11c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                                    </svg>
                                </div>
                                <div className="stat-label">Ответов получено</div>
                                <div className="stat-value">1 842</div>
                                <div className="stat-delta up">↑ 12% к прошлому мес.</div>
                            </div>

                            <div className="stat-card">
                                <div className="stat-icon amber">
                                    <svg viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <div className="stat-label">Активных опросов</div>
                                <div className="stat-value">3</div>
                                <div className="stat-delta">из 12 всего</div>
                            </div>

                            <div className="stat-card">
                                <div className="stat-icon green">
                                    <svg viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <div className="stat-label">Средний отклик</div>
                                <div className="stat-value">68%</div>
                                <div className="stat-delta up">↑ 5% к прошлому мес.</div>
                            </div>
                        </div>

                        <div className="section-header">
                            <div className="section-title">Последние опросы</div>
                            <button className="btn btn-ghost btn-sm">Все опросы →</button>
                        </div>

                        <div className="survey-table">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Название опроса</th>
                                        <th>Статус</th>
                                        <th>Ответов</th>
                                        <th>Отклик</th>
                                        <th>Закрывается</th>
                                        <th></th>
                                    </tr>
                                </thead>

                                <tbody>
                                    {[
                                        ["Оценка удовлетворённости сотрудников Q2", "Корпоративный · 8 вопросов", "Активен", "active", "214 / 280", "76%", "30 апр 2026"],
                                        ["NPS — Апрель 2026", "Клиентский · 3 вопроса", "Активен", "active", "891 / —", "100%", "1 мая 2026"],
                                        ["Пульс-опрос: Удалённая работа", "Корпоративный · 5 вопросов", "Запланирован", "scheduled", "0 / 150", "0%", "15 мая 2026"],
                                        ["Оценка онбординга — Q1 2026", "Корпоративный · 12 вопросов", "Завершён", "closed", "47 / 47", "100%", "31 мар 2026"],
                                    ].map((poll) => (
                                        <tr key={poll[0]}>
                                            <td>
                                                <div className="survey-name">{poll[0]}</div>
                                                <div className="survey-meta">{poll[1]}</div>
                                            </td>
                                            <td>
                                                <span className={`status-badge ${poll[3]}`}>{poll[2]}</span>
                                            </td>
                                            <td>{poll[4]}</td>
                                            <td>
                                                <div className="progress-bar" style={{ width: "120px" }}>
                                                    <div
                                                        className="progress-fill"
                                                        style={{
                                                            width: poll[5],
                                                            background: poll[0].includes("NPS") ? "var(--success)" : "var(--brand)",
                                                        }}
                                                    ></div>
                                                </div>
                                            </td>
                                            <td style={{ color: "var(--gray-500)" }}>{poll[6]}</td>
                                            <td>
                                                <div className="table-actions">
                                                    <button className="btn btn-secondary btn-sm">
                                                        {poll[3] === "scheduled" ? "Редактировать" : "Результаты"}
                                                    </button>
                                                    <button className="btn btn-ghost btn-sm">⋯</button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </main>
        </>
    )
}