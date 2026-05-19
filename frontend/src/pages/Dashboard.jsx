import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

import { getMe, logoutUser } from "../api/auth"
import { getMyPolls } from "../api/polls"
import CreatePoll from "./CreatePoll"
import Settings from "./Settings"
import Subscription from "./Subscription"

export default function Dashboard() {
    const [page, setPage] = useState("dashboard")
    const [surveyTab, setSurveyTab] = useState("all")

    const navigate = useNavigate()

    const [user, setUser] = useState(null)
    const [surveys, setSurveys] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState("")

    useEffect(() => {
        async function loadData() {
            try {
                const me = await getMe()
                const polls = await getMyPolls()

                setUser(me)
                setSurveys(polls)
            } catch (err) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }

        loadData()
    }, [])

    const filteredSurveys = surveys.filter((poll) => {
        if (surveyTab === "all") return true
        if (surveyTab === "active") return poll.status === "active"
        if (surveyTab === "draft") return poll.status === "draft"
        if (surveyTab === "closed") return poll.status === "closed"
        return true
    })

    const totalPolls = surveys.length
    const activePolls = surveys.filter(p => p.status === "active").length
    const draftPolls = surveys.filter(p => p.status === "draft").length
    const closedPolls = surveys.filter(p => p.status === "closed").length
    const totalVotes = surveys.reduce((sum, p) => sum + (p.total_votes || 0), 0)

    const getStatusText = (status) => {
        if (status === "active") return "Активен"
        if (status === "draft") return "Черновик"
        if (status === "closed") return "Завершён"
        return status
    }

    const formatDate = (date) => {
        if (!date) return "—"
        return new Date(date).toLocaleDateString("ru-RU")
    }

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

                        <div
                            onClick={() => setPage("dashboard")}
                            className={`nav-item ${page === "dashboard" ? "active" : ""}`}
                        >
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path d="M3 4a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 8a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H4a1 1 0 01-1-1v-4zm8-8a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V4zm0 8a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                            </svg>
                            Дашборд
                        </div>

                        <div
                            onClick={() => setPage("surveys")}
                            className={`nav-item ${page === "surveys" ? "active" : ""}`}
                        >
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M3 5a1 1 0 000 2h14a1 1 0 100-2H3zm0 4a1 1 0 000 2h14a1 1 0 100-2H3zm0 4a1 1 0 000 2h8a1 1 0 100-2H3z" clipRule="evenodd" />
                            </svg>
                            Опросы
                            <span className="nav-badge">{totalPolls}</span>
                        </div>

                        <div
                            onClick={() => setPage("create")}
                            className={`nav-item ${page === "create" ? "active" : ""}`}
                        >
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

                        <div
                            onClick={() => setPage("subscription")}
                            className={`nav-item ${page === "subscription" ? "active" : ""}`}
                        >
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                                <path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd" />
                            </svg>
                            Подписка
                        </div>

                        <div
                            onClick={() => setPage("settings")}
                            className={`nav-item ${page === "settings" ? "active" : ""}`}
                        >
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                            </svg>
                            Настройки
                        </div>
                    </div>
                </nav>

                <div className="sidebar-bottom">
                    <div className="user-card">
                        <div className="avatar">
                            {(user?.first_name?.[0] || user?.email?.[0] || "?").toUpperCase()}
                        </div>
                        <div className="user-info">
                            <div className="user-name">
                                {user?.first_name || user?.email || "Пользователь"}
                            </div>

                            <div className="user-role">
                                {user?.role || "Пользователь"}
                            </div>
                        </div>
                    </div>

                    <div
                        className="nav-item"
                        style={{ marginTop: "8px" }}
                        onClick={() => {
                            logoutUser()
                            navigate("/login")
                        }}
                    >
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
                {page === "dashboard" && (
                    <div className="page active">
                        <div className="topbar">
                            <div className="topbar-title">Дашборд</div>
                            <div className="topbar-actions">
                                <button
                                    className="btn btn-primary"
                                    onClick={() => setPage("create")}
                                >
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
                                    <div className="stat-value">{totalPolls}</div>
                                    <div className="stat-delta">из данных API</div>
                                </div>

                                <div className="stat-card">
                                    <div className="stat-icon green">
                                        <svg viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zm8 0a3 3 0 11-6 0 3 3 0 016 0zm-4.07 11c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                                        </svg>
                                    </div>
                                    <div className="stat-label">Ответов получено</div>
                                    <div className="stat-value">{totalVotes}</div>
                                    <div className="stat-delta">из данных API</div>
                                </div>

                                <div className="stat-card">
                                    <div className="stat-icon amber">
                                        <svg viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                                        </svg>
                                    </div>
                                    <div className="stat-label">Активных опросов</div>
                                    <div className="stat-value">{activePolls}</div>
                                    <div className="stat-delta">из данных API</div>
                                </div>

                                <div className="stat-card">
                                    <div className="stat-icon green">
                                        <svg viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                        </svg>
                                    </div>
                                    <div className="stat-label">Средний отклик</div>
                                    <div className="stat-value">—</div>
                                    <div className="stat-delta">нет в списке API</div>
                                </div>
                            </div>

                            <div className="section-header">
                                <div className="section-title">Последние опросы</div>
                                <button
                                    className="btn btn-ghost btn-sm"
                                    onClick={() => setPage("surveys")}
                                >
                                    Все опросы →
                                </button>
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
                                        {surveys.slice(0, 4).map((poll) => (
                                            <tr key={poll.id}>
                                                <td>
                                                    <div className="survey-name">{poll.title}</div>
                                                    <div className="survey-meta">Опрос</div>
                                                </td>

                                                <td>
                                                    <span className={`status-badge ${poll.status}`}>
                                                        {getStatusText(poll.status)}
                                                    </span>
                                                </td>

                                                <td>{poll.total_votes || 0}</td>

                                                <td>—</td>

                                                <td style={{ color: "var(--gray-500)" }}>
                                                    {formatDate(poll.expires_at)}
                                                </td>

                                                <td>
                                                    <div className="table-actions">
                                                        <button className="btn btn-secondary btn-sm">Результаты</button>
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
                )}

                {page === "surveys" && (
                    <div className="page active surveys-page">
                        <div className="topbar">
                            <div className="topbar-title">Все опросы</div>
                            <div className="topbar-actions">
                                <button
                                    className="btn btn-primary"
                                    onClick={() => setPage("create")}
                                >
                                    <svg viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                                    </svg>
                                    Новый опрос
                                </button>
                            </div>
                        </div>

                        <div style={{ padding: "28px" }}>
                            <div className="tabs">
                                <div onClick={() => setSurveyTab("all")} className={`tab ${surveyTab === "all" ? "active" : ""}`}>
                                    Все ({totalPolls})
                                </div>

                                <div onClick={() => setSurveyTab("active")} className={`tab ${surveyTab === "active" ? "active" : ""}`}>
                                    Активные ({activePolls})
                                </div>

                                <div onClick={() => setSurveyTab("draft")} className={`tab ${surveyTab === "draft" ? "active" : ""}`}>
                                    Черновики ({draftPolls})
                                </div>

                                <div onClick={() => setSurveyTab("closed")} className={`tab ${surveyTab === "closed" ? "active" : ""}`}>
                                    Завершённые ({closedPolls})
                                </div>
                            </div>

                            <div className="filter-bar">
                                <div className="search-wrap">
                                    <svg viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                                    </svg>
                                    <input type="text" placeholder="Поиск по названию..." />
                                </div>

                                <select className="filter-select">
                                    <option>Тип: Все</option>
                                    <option>Корпоративный</option>
                                    <option>Клиентский</option>
                                </select>

                                <select className="filter-select">
                                    <option>Период: Любой</option>
                                    <option>Апрель 2026</option>
                                    <option>Март 2026</option>
                                </select>
                            </div>

                            <div className="survey-table">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Название</th>
                                            <th>Тип</th>
                                            <th>Статус</th>
                                            <th>Ответов</th>
                                            <th>Отклик</th>
                                            <th>Дата создания</th>
                                            <th></th>
                                        </tr>
                                    </thead>

                                    <tbody>
                                        {filteredSurveys.map((poll) => (
                                            <tr key={poll.id}>
                                                <td>
                                                    <div className="survey-name">{poll.title}</div>
                                                    <div className="survey-meta">Опрос</div>
                                                </td>
                                                <td>
                                                    <span className={`status-badge ${poll.status}`}>
                                                        {getStatusText(poll.status)}
                                                    </span>
                                                </td>
                                                <td>{poll.total_votes || 0}</td>
                                                <td>—</td>
                                                <td style={{ color: "var(--gray-500)" }}>
                                                    {formatDate(poll.expires_at)}
                                                </td>
                                                <td>
                                                    <span className="chip">—</span>
                                                </td>
                                                <td>
                                                    <div className="table-actions">
                                                        <button className="btn btn-secondary btn-sm">Результаты</button>
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
                )}
                {page === "create" && <CreatePoll />}
                {page === "subscription" && <Subscription />}
                {page === "settings" && <Settings />}
            </main>
        </>
    )
}