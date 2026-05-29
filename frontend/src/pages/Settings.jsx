import { useState, useEffect, useCallback } from "react"
import { getMe } from "../api/auth"
import { apiRequest } from "../api/client"

// ─── Nav items ────────────────────────────────────────────────────────────────

const NAV_ITEMS = [
    {
        id: "profile",
        label: "Профиль",
        icon: (
            <svg viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
        ),
    },
    {
        id: "company",
        label: "Компания",
        icon: (
            <svg viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z" clipRule="evenodd" />
            </svg>
        ),
    },
    { sep: true },
    {
        id: "notifications",
        label: "Уведомления",
        icon: (
            <svg viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zm0 16a2 2 0 01-2-2h4a2 2 0 01-2 2z" />
            </svg>
        ),
    },
    {
        id: "security",
        label: "Безопасность",
        icon: (
            <svg viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
            </svg>
        ),
    },
    { sep: true },
    {
        id: "danger",
        label: "Опасная зона",
        danger: true,
        icon: (
            <svg viewBox="0 0 20 20" fill="currentColor" style={{ color: "var(--danger)" }}>
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
        ),
    },
]

// ─── Toggle ───────────────────────────────────────────────────────────────────

function Toggle({ value, onChange }) {
    return (
        <div
            className={`toggle ${value ? "on" : ""}`}
            onClick={() => onChange(!value)}
        />
    )
}

// ─── Toast ────────────────────────────────────────────────────────────────────

function Toast({ message, type }) {
    const isError = type === "error"
    return (
        <div style={{
            position: "fixed",
            bottom: "28px",
            right: "28px",
            zIndex: 1000,
            display: "flex",
            alignItems: "center",
            gap: "10px",
            background: isError ? "#FEF2F2" : "#F0FDF4",
            border: `1px solid ${isError ? "#FECACA" : "#BBF7D0"}`,
            color: isError ? "#B91C1C" : "#15803D",
            borderRadius: "10px",
            padding: "12px 18px",
            fontSize: "13px",
            fontWeight: 600,
            boxShadow: "0 4px 12px rgba(0,0,0,.12)",
            minWidth: "260px",
            animation: "fadeIn .2s ease",
        }}>
            <span style={{ fontSize: "16px" }}>{isError ? "✕" : "✓"}</span>
            {message}
        </div>
    )
}

// ─── Default notification prefs ───────────────────────────────────────────────

const DEFAULT_NOTIFS = {
    new_response: false,
    target_reached: true,
    poll_closed: true,
    weekly_digest: true,
    ai_ready: true,
    product_news: false,
}

const NOTIF_LABELS = [
    { key: "new_response",   label: "Новый ответ на опрос",          hint: "Письмо при каждом новом заполнении" },
    { key: "target_reached", label: "Достигнут целевой отклик",      hint: "Когда опрос достиг нужного числа ответов" },
    { key: "poll_closed",    label: "Опрос завершён",                 hint: "По истечении срока или достижении лимита" },
    { key: "weekly_digest",  label: "Еженедельный дайджест",          hint: "Сводка по всем активным опросам каждый понедельник" },
    { key: "ai_ready",       label: "AI-аналитика готова",            hint: "Когда AI завершил обработку результатов опроса" },
    { key: "product_news",   label: "Новости и обновления продукта",  hint: "Информация о новых функциях SurveyPulse" },
]

// ─── Main component ───────────────────────────────────────────────────────────

export default function Settings() {
    const [section, setSection] = useState("profile")
    const [toast, setToast] = useState(null)

    // Profile
    const [profile, setProfile] = useState({
        first_name: "",
        last_name: "",
        email: "",
        position: "",
        phone: "",
        interface_language: "ru",
        company_name: "",
        role: "",
    })
    const [profileLoading, setProfileLoading] = useState(true)
    const [profileSaving, setProfileSaving] = useState(false)

    // Password
    const [passwords, setPasswords] = useState({
        current_password: "",
        new_password: "",
        confirm_password: "",
    })
    const [passwordSaving, setPasswordSaving] = useState(false)

    // Notifications
    const [notifs, setNotifs] = useState(() => {
        try {
            const saved = localStorage.getItem("notif_prefs")
            return saved ? JSON.parse(saved) : DEFAULT_NOTIFS
        } catch {
            return DEFAULT_NOTIFS
        }
    })

    // Load user data
    useEffect(() => {
        getMe()
            .then((data) => {
                setProfile({
                    first_name: data.first_name || "",
                    last_name: data.last_name || "",
                    email: data.email || "",
                    position: data.position || "",
                    phone: data.phone || "",
                    interface_language: data.interface_language || "ru",
                    company_name: data.company_name || "",
                    role: data.role || "user",
                })
            })
            .catch(() => {})
            .finally(() => setProfileLoading(false))
    }, [])

    const showToast = useCallback((message, type = "success") => {
        setToast({ message, type })
        setTimeout(() => setToast(null), 3500)
    }, [])

    // Save profile
    const handleSaveProfile = async (e) => {
        e.preventDefault()
        setProfileSaving(true)
        try {
            await apiRequest("/api/v1/auth/me?use_cookie=false&token_type=access", {
                method: "PATCH",
                body: JSON.stringify({
                    first_name: profile.first_name,
                    last_name: profile.last_name,
                    position: profile.position,
                    phone: profile.phone,
                    interface_language: profile.interface_language,
                    company_name: profile.company_name,
                }),
            })
            showToast("Профиль успешно обновлён")
        } catch (err) {
            showToast(err.message || "Не удалось сохранить", "error")
        } finally {
            setProfileSaving(false)
        }
    }

    // Change password
    const handleChangePassword = async (e) => {
        e.preventDefault()
        if (!passwords.current_password) {
            showToast("Введите текущий пароль", "error")
            return
        }
        if (passwords.new_password.length < 8) {
            showToast("Новый пароль должен быть минимум 8 символов", "error")
            return
        }
        if (passwords.new_password !== passwords.confirm_password) {
            showToast("Пароли не совпадают", "error")
            return
        }
        setPasswordSaving(true)
        try {
            await apiRequest("/api/v1/auth/change-password?use_cookie=false&token_type=access", {
                method: "POST",
                body: JSON.stringify({
                    current_password: passwords.current_password,
                    new_password: passwords.new_password,
                }),
            })
            showToast("Пароль успешно изменён")
            setPasswords({ current_password: "", new_password: "", confirm_password: "" })
        } catch (err) {
            showToast(err.message || "Не удалось изменить пароль", "error")
        } finally {
            setPasswordSaving(false)
        }
    }

    // Save notifications
    const handleSaveNotifs = () => {
        localStorage.setItem("notif_prefs", JSON.stringify(notifs))
        showToast("Настройки уведомлений сохранены")
    }

    const avatarLetter = (
        (profile.first_name?.[0] || profile.email?.[0] || "?")
    ).toUpperCase()

    const roleLabel = (role) => {
        if (role === "admin") return "Администратор"
        if (role === "moderator") return "Модератор"
        return "Пользователь"
    }

    const roleDescription = (role) => {
        if (role === "admin") return "Полный доступ: создание опросов, просмотр всех результатов, управление участниками и настройками."
        if (role === "moderator") return "Может просматривать результаты и управлять опросами, но не может менять настройки аккаунта."
        return "Может проходить опросы и просматривать свои результаты."
    }

    return (
        <div className="page active">
            {toast && <Toast message={toast.message} type={toast.type} />}

            <div className="topbar">
                <div className="topbar-title">Настройки</div>
            </div>

            <div style={{ padding: "28px" }}>
                <div className="settings-layout">

                    {/* ── Left nav ── */}
                    <div className="settings-nav-panel">
                        {NAV_ITEMS.map((item, i) =>
                            item.sep ? (
                                <div key={i} className="settings-nav-sep" />
                            ) : (
                                <div
                                    key={item.id}
                                    className={`settings-nav-item ${section === item.id ? "active" : ""}`}
                                    onClick={() => setSection(item.id)}
                                >
                                    {item.icon}
                                    {item.danger
                                        ? <span style={{ color: "var(--danger)" }}>{item.label}</span>
                                        : item.label
                                    }
                                </div>
                            )
                        )}
                    </div>

                    {/* ── Right content ── */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

                        {/* ── Profile ── */}
                        {section === "profile" && (
                            <>
                                <form className="settings-card" onSubmit={handleSaveProfile}>
                                    <div className="settings-card-header">
                                        <div className="settings-card-title">Личные данные</div>
                                        <div className="settings-card-sub">Информация о вашем аккаунте</div>
                                    </div>

                                    <div className="settings-card-body">
                                        {profileLoading ? (
                                            <div style={{ color: "var(--gray-400)", fontSize: "13px", padding: "8px 0" }}>
                                                Загрузка…
                                            </div>
                                        ) : (
                                            <>
                                                <div className="settings-avatar-row">
                                                    <div className="settings-avatar">{avatarLetter}</div>
                                                    <div className="settings-avatar-actions">
                                                        <button type="button" className="btn btn-secondary btn-sm">Загрузить фото</button>
                                                        <button type="button" className="btn btn-ghost btn-sm">Удалить</button>
                                                        <div className="settings-avatar-hint">JPG, PNG до 2 МБ</div>
                                                    </div>
                                                </div>

                                                <div className="settings-row2">
                                                    <div className="form-group">
                                                        <label className="form-label">Имя</label>
                                                        <input
                                                            className="form-input"
                                                            type="text"
                                                            value={profile.first_name}
                                                            onChange={(e) => setProfile(p => ({ ...p, first_name: e.target.value }))}
                                                            placeholder="Введите имя"
                                                        />
                                                    </div>
                                                    <div className="form-group">
                                                        <label className="form-label">Фамилия</label>
                                                        <input
                                                            className="form-input"
                                                            type="text"
                                                            value={profile.last_name}
                                                            onChange={(e) => setProfile(p => ({ ...p, last_name: e.target.value }))}
                                                            placeholder="Введите фамилию"
                                                        />
                                                    </div>
                                                </div>

                                                <div className="form-group">
                                                    <label className="form-label">Email</label>
                                                    <input
                                                        className="form-input"
                                                        type="email"
                                                        value={profile.email}
                                                        readOnly
                                                        style={{ background: "var(--gray-50)", color: "var(--gray-400)", cursor: "not-allowed" }}
                                                        title="Email изменить нельзя"
                                                    />
                                                </div>

                                                <div className="settings-row2">
                                                    <div className="form-group">
                                                        <label className="form-label">Должность</label>
                                                        <input
                                                            className="form-input"
                                                            type="text"
                                                            value={profile.position}
                                                            onChange={(e) => setProfile(p => ({ ...p, position: e.target.value }))}
                                                            placeholder="Например: HR-директор"
                                                        />
                                                    </div>
                                                    <div className="form-group">
                                                        <label className="form-label">
                                                            Телефон <span>(необязательно)</span>
                                                        </label>
                                                        <input
                                                            className="form-input"
                                                            type="tel"
                                                            value={profile.phone}
                                                            onChange={(e) => setProfile(p => ({ ...p, phone: e.target.value }))}
                                                            placeholder="+7 (___) ___-__-__"
                                                        />
                                                    </div>
                                                </div>

                                                <div className="form-group" style={{ marginBottom: 0 }}>
                                                    <label className="form-label">Язык интерфейса</label>
                                                    <select
                                                        className="form-select"
                                                        style={{ maxWidth: "220px" }}
                                                        value={profile.interface_language}
                                                        onChange={(e) => setProfile(p => ({ ...p, interface_language: e.target.value }))}
                                                    >
                                                        <option value="ru">Русский</option>
                                                        <option value="en">English</option>
                                                        <option value="kk">Қазақша</option>
                                                    </select>
                                                </div>
                                            </>
                                        )}
                                    </div>

                                    <div className="settings-card-footer">
                                        <button
                                            type="button"
                                            className="btn btn-secondary"
                                            onClick={() => {
                                                setProfileLoading(true)
                                                getMe()
                                                    .then((data) => setProfile({
                                                        first_name: data.first_name || "",
                                                        last_name: data.last_name || "",
                                                        email: data.email || "",
                                                        position: data.position || "",
                                                        phone: data.phone || "",
                                                        interface_language: data.interface_language || "ru",
                                                        company_name: data.company_name || "",
                                                    }))
                                                    .catch(() => {})
                                                    .finally(() => setProfileLoading(false))
                                            }}
                                        >
                                            Отмена
                                        </button>
                                        <button
                                            type="submit"
                                            className="btn btn-primary"
                                            disabled={profileSaving || profileLoading}
                                        >
                                            {profileSaving ? "Сохраняем…" : "Сохранить"}
                                        </button>
                                    </div>
                                </form>

                                <div className="settings-card">
                                    <div className="settings-card-header">
                                        <div className="settings-card-title">Роль в системе</div>
                                        <div className="settings-card-sub">Ваши права доступа в SurveyPulse</div>
                                    </div>
                                    <div className="settings-card-body" style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                                        <div style={{
                                            width: "44px", height: "44px", borderRadius: "12px",
                                            background: "var(--brand-light)", display: "flex",
                                            alignItems: "center", justifyContent: "center", flexShrink: 0,
                                        }}>
                                            <svg viewBox="0 0 20 20" fill="currentColor" style={{ width: "22px", height: "22px", color: "var(--brand)" }}>
                                                <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                            </svg>
                                        </div>
                                        <div>
                                            <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--gray-900)" }}>
                                                {profileLoading ? "—" : roleLabel(profile.role)}
                                            </div>
                                            <div style={{ fontSize: "12px", color: "var(--gray-400)", marginTop: "2px" }}>
                                                {profileLoading ? "" : roleDescription(profile.role)}
                                            </div>
                                        </div>
                                        <button
                                            className="btn btn-ghost btn-sm"
                                            style={{ marginLeft: "auto", flexShrink: 0 }}
                                            onClick={() => showToast("Смена роли доступна только через администратора", "error")}
                                        >
                                            Сменить роль
                                        </button>
                                    </div>
                                </div>
                            </>
                        )}

                        {/* ── Company ── */}
                        {section === "company" && (
                            <>
                                <form
                                    className="settings-card"
                                    onSubmit={(e) => {
                                        e.preventDefault()
                                        showToast("Данные компании сохранены")
                                    }}
                                >
                                    <div className="settings-card-header">
                                        <div className="settings-card-title">Данные компании</div>
                                        <div className="settings-card-sub">Отображаются в опросах и отчётах</div>
                                    </div>
                                    <div className="settings-card-body">
                                        <div className="form-group">
                                            <label className="form-label">Название компании</label>
                                            <input
                                                className="form-input"
                                                type="text"
                                                value={profile.company_name}
                                                onChange={(e) => setProfile(p => ({ ...p, company_name: e.target.value }))}
                                                placeholder="Название вашей компании"
                                            />
                                        </div>
                                        <div className="settings-row2">
                                            <div className="form-group">
                                                <label className="form-label">Отрасль</label>
                                                <select className="form-select">
                                                    <option>Информационные технологии</option>
                                                    <option>Финансы и банки</option>
                                                    <option>Производство</option>
                                                    <option>Ретейл</option>
                                                    <option>Здравоохранение</option>
                                                    <option>Образование</option>
                                                    <option>Другое</option>
                                                </select>
                                            </div>
                                            <div className="form-group">
                                                <label className="form-label">Размер компании</label>
                                                <select className="form-select">
                                                    <option>1–50 сотрудников</option>
                                                    <option>51–200 сотрудников</option>
                                                    <option>201–500 сотрудников</option>
                                                    <option>501–1000 сотрудников</option>
                                                    <option>Более 1000</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Сайт <span>(необязательно)</span></label>
                                            <input className="form-input" type="url" placeholder="https://company.ru" />
                                        </div>
                                        <div className="form-group" style={{ marginBottom: 0 }}>
                                            <label className="form-label">Часовой пояс</label>
                                            <select className="form-select" style={{ maxWidth: "300px" }}>
                                                <option>UTC+3 — Москва, Санкт-Петербург</option>
                                                <option>UTC+5 — Екатеринбург</option>
                                                <option>UTC+7 — Красноярск</option>
                                                <option>UTC+8 — Иркутск</option>
                                                <option>UTC+0 — Лондон</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div className="settings-card-footer">
                                        <button
                                            type="button"
                                            className="btn btn-secondary"
                                            onClick={() => {
                                                setProfileLoading(true)
                                                getMe()
                                                    .then((data) => setProfile(p => ({ ...p, company_name: data.company_name || "" })))
                                                    .catch(() => {})
                                                    .finally(() => setProfileLoading(false))
                                            }}
                                        >
                                            Отмена
                                        </button>
                                        <button type="submit" className="btn btn-primary">Сохранить</button>
                                    </div>
                                </form>

                                <form
                                    className="settings-card"
                                    onSubmit={(e) => {
                                        e.preventDefault()
                                        showToast("Брендирование сохранено")
                                    }}
                                >
                                    <div className="settings-card-header">
                                        <div className="settings-card-title">Брендирование</div>
                                        <div className="settings-card-sub">Логотип и цвет отображаются в шапке опросов</div>
                                    </div>
                                    <div className="settings-card-body">
                                        <div style={{
                                            display: "flex", alignItems: "center", gap: "20px",
                                            marginBottom: "20px", paddingBottom: "20px",
                                            borderBottom: "1px solid var(--gray-100)",
                                        }}>
                                            <div style={{
                                                width: "72px", height: "72px", borderRadius: "12px",
                                                border: "2px dashed var(--gray-200)", background: "var(--gray-50)",
                                                display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer",
                                            }}>
                                                <svg viewBox="0 0 20 20" fill="currentColor" style={{ width: "24px", height: "24px", color: "var(--gray-300)" }}>
                                                    <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                                                </svg>
                                            </div>
                                            <div>
                                                <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--gray-800)", marginBottom: "4px" }}>
                                                    Логотип компании
                                                </div>
                                                <div style={{ fontSize: "12px", color: "var(--gray-400)", marginBottom: "8px" }}>
                                                    PNG или SVG, минимум 200×200 пикселей
                                                </div>
                                                <button type="button" className="btn btn-secondary btn-sm">Загрузить</button>
                                            </div>
                                        </div>
                                        <div className="form-group" style={{ marginBottom: 0 }}>
                                            <label className="form-label">Основной цвет бренда</label>
                                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                                <input type="color" defaultValue="#4F46E5" style={{
                                                    width: "42px", height: "38px",
                                                    border: "1px solid var(--gray-200)", borderRadius: "8px",
                                                    cursor: "pointer", padding: "2px",
                                                }} />
                                                <input className="form-input" type="text" defaultValue="#4F46E5" style={{ maxWidth: "140px", fontFamily: "monospace" }} />
                                                <span style={{ fontSize: "12px", color: "var(--gray-400)" }}>
                                                    Используется в кнопках и акцентах опроса
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="settings-card-footer">
                                        <button type="button" className="btn btn-secondary">Отмена</button>
                                        <button type="submit" className="btn btn-primary">Сохранить</button>
                                    </div>
                                </form>
                            </>
                        )}

                        {/* ── Notifications ── */}
                        {section === "notifications" && (
                            <div className="settings-card">
                                <div className="settings-card-header">
                                    <div className="settings-card-title">Email-уведомления</div>
                                    <div className="settings-card-sub">Выберите, о чём получать письма</div>
                                </div>
                                <div className="settings-card-body">
                                    {NOTIF_LABELS.map(({ key, label, hint }) => (
                                        <div key={key} className="notif-row">
                                            <div>
                                                <div className="notif-label">{label}</div>
                                                <div className="notif-hint">{hint}</div>
                                            </div>
                                            <Toggle
                                                value={notifs[key]}
                                                onChange={(val) => setNotifs(n => ({ ...n, [key]: val }))}
                                            />
                                        </div>
                                    ))}
                                </div>
                                <div className="settings-card-footer">
                                    <button className="btn btn-primary" onClick={handleSaveNotifs}>
                                        Сохранить
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* ── Security ── */}
                        {section === "security" && (
                            <>
                                <form className="settings-card" onSubmit={handleChangePassword}>
                                    <div className="settings-card-header">
                                        <div className="settings-card-title">Пароль</div>
                                        <div className="settings-card-sub">Изменение пароля для входа в аккаунт</div>
                                    </div>
                                    <div className="settings-card-body">
                                        <div className="form-group">
                                            <label className="form-label">Текущий пароль</label>
                                            <input
                                                className="form-input"
                                                type="password"
                                                placeholder="Введите текущий пароль"
                                                style={{ maxWidth: "340px" }}
                                                value={passwords.current_password}
                                                onChange={(e) => setPasswords(p => ({ ...p, current_password: e.target.value }))}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Новый пароль</label>
                                            <input
                                                className="form-input"
                                                type="password"
                                                placeholder="Минимум 8 символов"
                                                style={{ maxWidth: "340px" }}
                                                value={passwords.new_password}
                                                onChange={(e) => setPasswords(p => ({ ...p, new_password: e.target.value }))}
                                            />
                                        </div>
                                        <div className="form-group" style={{ marginBottom: 0 }}>
                                            <label className="form-label">Повторите новый пароль</label>
                                            <input
                                                className="form-input"
                                                type="password"
                                                placeholder="Повторите пароль"
                                                style={{ maxWidth: "340px" }}
                                                value={passwords.confirm_password}
                                                onChange={(e) => setPasswords(p => ({ ...p, confirm_password: e.target.value }))}
                                            />
                                        </div>
                                    </div>
                                    <div className="settings-card-footer">
                                        <button type="submit" className="btn btn-primary" disabled={passwordSaving}>
                                            {passwordSaving ? "Сохраняем…" : "Изменить пароль"}
                                        </button>
                                    </div>
                                </form>

                                <div className="settings-card">
                                    <div className="settings-card-header">
                                        <div className="settings-card-title">Двухфакторная аутентификация</div>
                                        <div className="settings-card-sub">Дополнительная защита аккаунта</div>
                                    </div>
                                    <div className="settings-card-body">
                                        <TwoFAItem
                                            icon={
                                                <svg viewBox="0 0 20 20" fill="currentColor">
                                                    <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
                                                </svg>
                                            }
                                            label="SMS-подтверждение"
                                            hint="Код на номер +7 (___) ___-__-__"
                                            defaultOn={false}
                                            onToggle={() => showToast("SMS 2FA — скоро")}
                                        />
                                        <TwoFAItem
                                            icon={
                                                <svg viewBox="0 0 20 20" fill="currentColor">
                                                    <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                                                </svg>
                                            }
                                            label="Приложение-аутентификатор"
                                            hint="Google Authenticator, Yandex Key и др."
                                            defaultOn={false}
                                            onToggle={() => showToast("TOTP 2FA — скоро")}
                                        />
                                    </div>
                                </div>

                                <div className="settings-card">
                                    <div className="settings-card-header">
                                        <div className="settings-card-title">Активные сессии</div>
                                        <div className="settings-card-sub">Устройства, с которых выполнен вход</div>
                                    </div>
                                    <div className="settings-card-body">
                                        <SessionItem
                                            label="Chrome · macOS — Текущая сессия"
                                            meta="Текущее устройство"
                                            current
                                        />
                                        <SessionItem
                                            label="Safari · iPhone"
                                            meta="Последняя активность неизвестна"
                                            onTerminate={() => showToast("Сессия завершена")}
                                        />
                                        <SessionItem
                                            label="Chrome · Windows"
                                            meta="Последняя активность неизвестна"
                                            onTerminate={() => showToast("Сессия завершена")}
                                        />
                                    </div>
                                    <div className="settings-card-footer">
                                        <button
                                            className="btn btn-danger btn-sm"
                                            onClick={() => showToast("Все другие сессии завершены")}
                                        >
                                            Завершить все другие сессии
                                        </button>
                                    </div>
                                </div>
                            </>
                        )}

                        {/* ── Danger zone ── */}
                        {section === "danger" && (
                            <div className="settings-card">
                                <div className="settings-card-header">
                                    <div className="settings-card-title" style={{ color: "var(--danger)" }}>Опасная зона</div>
                                    <div className="settings-card-sub">Необратимые действия. Действуйте осторожно.</div>
                                </div>
                                <div className="settings-card-body">
                                    <div className="danger-item">
                                        <div>
                                            <div className="danger-item-label">Экспорт всех данных</div>
                                            <div className="danger-item-hint">Скачать архив со всеми опросами, ответами и настройками</div>
                                        </div>
                                        <button
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => showToast("Экспорт данных — скоро")}
                                        >
                                            Экспортировать
                                        </button>
                                    </div>
                                    <div className="danger-item">
                                        <div>
                                            <div className="danger-item-label">Удалить все завершённые опросы</div>
                                            <div className="danger-item-hint">Удалятся все опросы со статусом «Завершён» и их результаты</div>
                                        </div>
                                        <button
                                            className="btn btn-danger btn-sm"
                                            onClick={() => {
                                                if (window.confirm("Удалить все завершённые опросы? Это действие необратимо.")) {
                                                    showToast("Завершённые опросы удалены")
                                                }
                                            }}
                                        >
                                            Удалить
                                        </button>
                                    </div>
                                    <div className="danger-item">
                                        <div>
                                            <div className="danger-item-label">Удалить аккаунт</div>
                                            <div className="danger-item-hint">Аккаунт, все опросы и результаты будут удалены без возможности восстановления</div>
                                        </div>
                                        <button
                                            className="btn btn-danger btn-sm"
                                            onClick={() => {
                                                if (window.confirm("Вы уверены? Это действие необратимо. Все данные будут удалены.")) {
                                                    showToast("Запрос на удаление отправлен")
                                                }
                                            }}
                                        >
                                            Удалить аккаунт
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}

                    </div>
                </div>
            </div>
        </div>
    )
}

// ─── Вспомогательные компоненты ───────────────────────────────────────────────

function TwoFAItem({ icon, label, hint, defaultOn, onToggle }) {
    const [on, setOn] = useState(defaultOn)
    return (
        <div className="security-item">
            <div className="security-item-icon">{icon}</div>
            <div className="security-item-body">
                <div className="security-item-label">{label}</div>
                <div className="security-item-hint">{hint}</div>
            </div>
            <Toggle
                value={on}
                onChange={(val) => { setOn(val); onToggle(val) }}
            />
        </div>
    )
}

function SessionItem({ label, meta, current, onTerminate }) {
    return (
        <div className="session-item">
            <div className={`session-dot ${current ? "current" : "other"}`} />
            <div style={{ flex: 1 }}>
                <div className="session-label">{label}</div>
                <div className="session-meta">{meta}</div>
            </div>
            {current ? (
                <span style={{
                    fontSize: "11px", fontWeight: 700, color: "var(--success)",
                    background: "#D1FAE5", padding: "2px 8px", borderRadius: "20px",
                }}>
                    Активна
                </span>
            ) : (
                <button className="btn btn-ghost btn-sm" onClick={onTerminate}>
                    Завершить
                </button>
            )}
        </div>
    )
}
