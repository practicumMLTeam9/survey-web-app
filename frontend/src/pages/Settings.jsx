import { useState } from "react"

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

function Toggle({ defaultOn = false }) {
    const [on, setOn] = useState(defaultOn)
    return <div className={`toggle ${on ? "on" : ""}`} onClick={() => setOn(v => !v)} />
}

export default function Settings() {
    const [section, setSection] = useState("profile")

    return (
        <div className="page active">
            <div className="topbar">
                <div className="topbar-title">Настройки</div>
            </div>

            <div style={{ padding: "28px" }}>
                <div className="settings-layout">

                    {/* Left nav */}
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

                    {/* Right content */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

                        {/* ── Profile ── */}
                        {section === "profile" && (
                            <>
                                <div className="settings-card">
                                    <div className="settings-card-header">
                                        <div className="settings-card-title">Личные данные</div>
                                        <div className="settings-card-sub">Информация о вашем аккаунте</div>
                                    </div>
                                    <div className="settings-card-body">
                                        <div className="settings-avatar-row">
                                            <div className="settings-avatar">АК</div>
                                            <div className="settings-avatar-actions">
                                                <button className="btn btn-secondary btn-sm">Загрузить фото</button>
                                                <button className="btn btn-ghost btn-sm">Удалить</button>
                                                <div className="settings-avatar-hint">JPG, PNG до 2 МБ</div>
                                            </div>
                                        </div>
                                        <div className="settings-row2">
                                            <div className="form-group">
                                                <label className="form-label">Имя</label>
                                                <input className="form-input" type="text" defaultValue="Алексей" />
                                            </div>
                                            <div className="form-group">
                                                <label className="form-label">Фамилия</label>
                                                <input className="form-input" type="text" defaultValue="Козлов" />
                                            </div>
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Email</label>
                                            <input className="form-input" type="email" defaultValue="alexey@techcorp.ru" />
                                        </div>
                                        <div className="settings-row2">
                                            <div className="form-group">
                                                <label className="form-label">Должность</label>
                                                <input className="form-input" type="text" defaultValue="HR-директор" />
                                            </div>
                                            <div className="form-group">
                                                <label className="form-label">
                                                    Телефон <span>(необязательно)</span>
                                                </label>
                                                <input className="form-input" type="tel" defaultValue="+7 (495) 000-00-00" />
                                            </div>
                                        </div>
                                        <div className="form-group" style={{ marginBottom: 0 }}>
                                            <label className="form-label">Язык интерфейса</label>
                                            <select className="form-select" style={{ maxWidth: "220px" }}>
                                                <option>Русский</option>
                                                <option>English</option>
                                                <option>Қазақша</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div className="settings-card-footer">
                                        <button className="btn btn-secondary">Отмена</button>
                                        <button className="btn btn-primary">Сохранить</button>
                                    </div>
                                </div>

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
                                            <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--gray-900)" }}>Администратор</div>
                                            <div style={{ fontSize: "12px", color: "var(--gray-400)", marginTop: "2px" }}>
                                                Полный доступ: создание опросов, просмотр всех результатов, управление участниками и настройками.
                                            </div>
                                        </div>
                                        <button className="btn btn-ghost btn-sm" style={{ marginLeft: "auto", flexShrink: 0 }}>
                                            Сменить роль
                                        </button>
                                    </div>
                                </div>
                            </>
                        )}

                        {/* ── Company ── */}
                        {section === "company" && (
                            <>
                                <div className="settings-card">
                                    <div className="settings-card-header">
                                        <div className="settings-card-title">Данные компании</div>
                                        <div className="settings-card-sub">Отображаются в опросах и отчётах</div>
                                    </div>
                                    <div className="settings-card-body">
                                        <div className="form-group">
                                            <label className="form-label">Название компании</label>
                                            <input className="form-input" type="text" defaultValue="TechCorp" />
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
                                            <input className="form-input" type="url" defaultValue="https://techcorp.ru" />
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
                                        <button className="btn btn-secondary">Отмена</button>
                                        <button className="btn btn-primary">Сохранить</button>
                                    </div>
                                </div>

                                <div className="settings-card">
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
                                                <button className="btn btn-secondary btn-sm">Загрузить</button>
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
                                        <button className="btn btn-secondary">Отмена</button>
                                        <button className="btn btn-primary">Сохранить</button>
                                    </div>
                                </div>
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
                                    {[
                                        ["Новый ответ на опрос", "Письмо при каждом новом заполнении", false],
                                        ["Достигнут целевой отклик", "Когда опрос достиг нужного числа ответов", true],
                                        ["Опрос завершён", "По истечении срока или достижении лимита", true],
                                        ["Еженедельный дайджест", "Сводка по всем активным опросам каждый понедельник", true],
                                        ["AI-аналитика готова", "Когда AI завершил обработку результатов опроса", true],
                                        ["Новости и обновления продукта", "Информация о новых функциях SurveyPulse", false],
                                    ].map(([label, hint, defaultOn]) => (
                                        <div key={label} className="notif-row">
                                            <div>
                                                <div className="notif-label">{label}</div>
                                                <div className="notif-hint">{hint}</div>
                                            </div>
                                            <Toggle defaultOn={defaultOn} />
                                        </div>
                                    ))}
                                </div>
                                <div className="settings-card-footer">
                                    <button className="btn btn-primary">Сохранить</button>
                                </div>
                            </div>
                        )}

                        {/* ── Security ── */}
                        {section === "security" && (
                            <>
                                <div className="settings-card">
                                    <div className="settings-card-header">
                                        <div className="settings-card-title">Пароль</div>
                                        <div className="settings-card-sub">Изменение пароля для входа в аккаунт</div>
                                    </div>
                                    <div className="settings-card-body">
                                        <div className="form-group">
                                            <label className="form-label">Текущий пароль</label>
                                            <input className="form-input" type="password" placeholder="Введите текущий пароль" style={{ maxWidth: "340px" }} />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Новый пароль</label>
                                            <input className="form-input" type="password" placeholder="Минимум 8 символов" style={{ maxWidth: "340px" }} />
                                        </div>
                                        <div className="form-group" style={{ marginBottom: 0 }}>
                                            <label className="form-label">Повторите новый пароль</label>
                                            <input className="form-input" type="password" placeholder="Повторите пароль" style={{ maxWidth: "340px" }} />
                                        </div>
                                    </div>
                                    <div className="settings-card-footer">
                                        <button className="btn btn-primary">Изменить пароль</button>
                                    </div>
                                </div>

                                <div className="settings-card">
                                    <div className="settings-card-header">
                                        <div className="settings-card-title">Двухфакторная аутентификация</div>
                                        <div className="settings-card-sub">Дополнительная защита аккаунта</div>
                                    </div>
                                    <div className="settings-card-body">
                                        <div className="security-item">
                                            <div className="security-item-icon">
                                                <svg viewBox="0 0 20 20" fill="currentColor">
                                                    <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
                                                </svg>
                                            </div>
                                            <div className="security-item-body">
                                                <div className="security-item-label">SMS-подтверждение</div>
                                                <div className="security-item-hint">Код на номер +7 (495) •••• 00-00</div>
                                            </div>
                                            <Toggle defaultOn={true} />
                                        </div>
                                        <div className="security-item">
                                            <div className="security-item-icon">
                                                <svg viewBox="0 0 20 20" fill="currentColor">
                                                    <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                                                </svg>
                                            </div>
                                            <div className="security-item-body">
                                                <div className="security-item-label">Приложение-аутентификатор</div>
                                                <div className="security-item-hint">Google Authenticator, Yandex Key и др.</div>
                                            </div>
                                            <Toggle defaultOn={false} />
                                        </div>
                                    </div>
                                </div>

                                <div className="settings-card">
                                    <div className="settings-card-header">
                                        <div className="settings-card-title">Активные сессии</div>
                                        <div className="settings-card-sub">Устройства, с которых выполнен вход</div>
                                    </div>
                                    <div className="settings-card-body">
                                        <div className="session-item">
                                            <div className="session-dot current" />
                                            <div style={{ flex: 1 }}>
                                                <div className="session-label">Chrome · macOS — Текущая сессия</div>
                                                <div className="session-meta">Москва, Россия · 28 апр 2026, 10:41</div>
                                            </div>
                                            <span style={{
                                                fontSize: "11px", fontWeight: 700, color: "var(--success)",
                                                background: "#D1FAE5", padding: "2px 8px", borderRadius: "20px",
                                            }}>Активна</span>
                                        </div>
                                        <div className="session-item">
                                            <div className="session-dot other" />
                                            <div style={{ flex: 1 }}>
                                                <div className="session-label">Safari · iPhone 15</div>
                                                <div className="session-meta">Москва, Россия · 27 апр 2026, 19:05</div>
                                            </div>
                                            <button className="btn btn-ghost btn-sm">Завершить</button>
                                        </div>
                                        <div className="session-item">
                                            <div className="session-dot other" />
                                            <div style={{ flex: 1 }}>
                                                <div className="session-label">Chrome · Windows 11</div>
                                                <div className="session-meta">Санкт-Петербург, Россия · 25 апр 2026, 14:22</div>
                                            </div>
                                            <button className="btn btn-ghost btn-sm">Завершить</button>
                                        </div>
                                    </div>
                                    <div className="settings-card-footer">
                                        <button className="btn btn-danger btn-sm">Завершить все другие сессии</button>
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
                                        <button className="btn btn-secondary btn-sm">Экспортировать</button>
                                    </div>
                                    <div className="danger-item">
                                        <div>
                                            <div className="danger-item-label">Удалить все завершённые опросы</div>
                                            <div className="danger-item-hint">Удалятся все опросы со статусом «Завершён» и их результаты</div>
                                        </div>
                                        <button className="btn btn-danger btn-sm">Удалить</button>
                                    </div>
                                    <div className="danger-item">
                                        <div>
                                            <div className="danger-item-label">Удалить аккаунт</div>
                                            <div className="danger-item-hint">Аккаунт, все опросы и результаты будут удалены без возможности восстановления</div>
                                        </div>
                                        <button className="btn btn-danger btn-sm">Удалить аккаунт</button>
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
