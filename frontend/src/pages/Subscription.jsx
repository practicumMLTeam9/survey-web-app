import { useState } from "react"

export default function Subscription() {
    const [period, setPeriod] = useState("monthly")

    const proPrice = period === "monthly" ? "2 990 ₽" : "2 392 ₽"
    const proPeriodLabel = period === "monthly"
        ? "в месяц · при оплате ежемесячно"
        : "в месяц · при оплате ежегодно"

    return (
        <div className="page active">
            <div className="topbar">
                <div className="topbar-title">Подписка</div>
                <div className="topbar-actions">
                    <span style={{ fontSize: "13px", color: "var(--gray-500)" }}>Текущий план:</span>
                    <span style={{
                        fontSize: "13px",
                        fontWeight: 700,
                        color: "var(--brand)",
                        background: "var(--brand-light)",
                        padding: "4px 12px",
                        borderRadius: "20px",
                    }}>Pro</span>
                </div>
            </div>

            <div style={{ padding: "28px" }}>

                {/* Current plan banner */}
                <div style={{
                    background: "linear-gradient(135deg,#1E1B4B,#312E81,#1E3A5F)",
                    borderRadius: "var(--radius)",
                    padding: "24px 28px",
                    marginBottom: "28px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    position: "relative",
                    overflow: "hidden",
                }}>
                    <div style={{
                        position: "absolute",
                        top: "-50px",
                        right: "-50px",
                        width: "220px",
                        height: "220px",
                        borderRadius: "50%",
                        background: "radial-gradient(circle,rgba(124,58,237,.3) 0%,transparent 70%)",
                    }} />
                    <div style={{ position: "relative", zIndex: 1 }}>
                        <div style={{
                            fontSize: "11px",
                            fontWeight: 700,
                            color: "rgba(255,255,255,.6)",
                            textTransform: "uppercase",
                            letterSpacing: ".06em",
                            marginBottom: "6px",
                        }}>Активный план</div>
                        <div style={{ fontSize: "22px", fontWeight: 900, color: "#fff", marginBottom: "4px" }}>
                            Pro{" "}
                            <span style={{ fontSize: "14px", fontWeight: 500, color: "rgba(255,255,255,.6)" }}>
                                · оплачено до 28 апреля 2027
                            </span>
                        </div>
                        <div style={{ fontSize: "13px", color: "rgba(255,255,255,.55)" }}>
                            Следующее списание:{" "}
                            <strong style={{ color: "rgba(255,255,255,.85)" }}>2 990 ₽</strong>
                            {" "}· 28 апреля 2027
                        </div>
                    </div>
                    <div style={{ position: "relative", zIndex: 1, display: "flex", gap: "10px" }}>
                        <button className="btn btn-sm" style={{
                            background: "rgba(255,255,255,.12)",
                            border: "1px solid rgba(255,255,255,.2)",
                            color: "#fff",
                        }}>
                            История платежей
                        </button>
                        <button className="btn btn-sm" style={{ background: "#fff", color: "#312E81", fontWeight: 700 }}>
                            Управление картой
                        </button>
                    </div>
                </div>

                {/* Usage stats */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "16px", marginBottom: "28px" }}>
                    <div className="stat-card">
                        <div className="stat-icon indigo">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M3 5a1 1 0 000 2h14a1 1 0 100-2H3zm0 4a1 1 0 000 2h14a1 1 0 100-2H3zm0 4a1 1 0 000 2h8a1 1 0 100-2H3z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div className="stat-label">Опросов</div>
                        <div className="stat-value">12</div>
                        <div className="stat-delta" style={{ color: "var(--gray-400)" }}>из 50 в месяц</div>
                        <div className="progress-bar" style={{ marginTop: "8px" }}>
                            <div className="progress-fill" style={{ width: "24%" }} />
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-icon green">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zm8 0a3 3 0 11-6 0 3 3 0 016 0zm-4.07 11c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                            </svg>
                        </div>
                        <div className="stat-label">Ответов</div>
                        <div className="stat-value">1 842</div>
                        <div className="stat-delta" style={{ color: "var(--gray-400)" }}>из 5 000 в месяц</div>
                        <div className="progress-bar" style={{ marginTop: "8px" }}>
                            <div className="progress-fill" style={{ width: "37%", background: "var(--success)" }} />
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-icon amber">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zm8 0a3 3 0 11-6 0 3 3 0 016 0zm-4.07 11c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                            </svg>
                        </div>
                        <div className="stat-label">Участников</div>
                        <div className="stat-value">280</div>
                        <div className="stat-delta" style={{ color: "var(--gray-400)" }}>из 1 000 в аккаунте</div>
                        <div className="progress-bar" style={{ marginTop: "8px" }}>
                            <div className="progress-fill" style={{ width: "28%", background: "var(--warning)" }} />
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-icon indigo">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" />
                            </svg>
                        </div>
                        <div className="stat-label">AI-запросов</div>
                        <div className="stat-value">47</div>
                        <div className="stat-delta" style={{ color: "var(--gray-400)" }}>из 200 в месяц</div>
                        <div className="progress-bar" style={{ marginTop: "8px" }}>
                            <div className="progress-fill" style={{ width: "24%" }} />
                        </div>
                    </div>
                </div>

                {/* Plan selection */}
                <div className="section-header" style={{ marginBottom: "20px" }}>
                    <div className="section-title">Выберите план</div>
                    <div style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        background: "var(--gray-100)",
                        borderRadius: "8px",
                        padding: "4px",
                    }}>
                        <span
                            onClick={() => setPeriod("monthly")}
                            style={{
                                padding: "5px 14px",
                                borderRadius: "6px",
                                fontSize: "13px",
                                fontWeight: 600,
                                cursor: "pointer",
                                ...(period === "monthly"
                                    ? { background: "#fff", color: "var(--gray-900)", boxShadow: "0 1px 3px rgba(0,0,0,.1)" }
                                    : { color: "var(--gray-500)" }
                                ),
                            }}
                        >
                            Ежемесячно
                        </span>
                        <span
                            onClick={() => setPeriod("annual")}
                            style={{
                                padding: "5px 14px",
                                borderRadius: "6px",
                                fontSize: "13px",
                                fontWeight: 600,
                                cursor: "pointer",
                                ...(period === "annual"
                                    ? { background: "#fff", color: "var(--gray-900)", boxShadow: "0 1px 3px rgba(0,0,0,.1)" }
                                    : { color: "var(--gray-500)" }
                                ),
                            }}
                        >
                            Ежегодно{" "}
                            <span style={{ fontSize: "11px", color: "var(--success)", fontWeight: 700 }}>−20%</span>
                        </span>
                    </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "20px", marginBottom: "32px" }}>

                    {/* Free */}
                    <div className="card" style={{ position: "relative" }}>
                        <div className="card-body" style={{ padding: "28px" }}>
                            <div style={{
                                fontSize: "13px",
                                fontWeight: 700,
                                color: "var(--gray-500)",
                                textTransform: "uppercase",
                                letterSpacing: ".05em",
                                marginBottom: "10px",
                            }}>Free</div>
                            <div style={{ fontSize: "36px", fontWeight: 900, color: "var(--gray-900)", lineHeight: 1, marginBottom: "4px" }}>0 ₽</div>
                            <div style={{ fontSize: "13px", color: "var(--gray-400)", marginBottom: "24px" }}>Бесплатно навсегда</div>
                            <button className="btn btn-secondary" style={{ width: "100%", justifyContent: "center", marginBottom: "24px" }}>
                                Текущий план ниже
                            </button>
                            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                                {[
                                    [true, "До 5 опросов в месяц"],
                                    [true, "До 100 ответов в месяц"],
                                    [true, "До 10 участников"],
                                    [true, "Базовые типы вопросов"],
                                    [false, "AI-генерация опросов"],
                                    [false, "AI-аналитика"],
                                    [false, "Экспорт PDF"],
                                ].map(([ok, label]) => (
                                    <div key={label} style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "8px",
                                        fontSize: "13px",
                                        color: ok ? "var(--gray-600)" : "var(--gray-300)",
                                    }}>
                                        <span style={{ fontWeight: 700, color: ok ? "var(--success)" : undefined }}>{ok ? "✓" : "✗"}</span>
                                        {label}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Pro (current, highlighted) */}
                    <div className="card" style={{
                        position: "relative",
                        borderColor: "var(--brand)",
                        boxShadow: "0 0 0 2px rgba(79,70,229,.15),var(--shadow-md)",
                    }}>
                        <div style={{
                            position: "absolute",
                            top: "-12px",
                            left: "50%",
                            transform: "translateX(-50%)",
                            background: "var(--brand)",
                            color: "#fff",
                            fontSize: "11px",
                            fontWeight: 800,
                            padding: "3px 14px",
                            borderRadius: "20px",
                            whiteSpace: "nowrap",
                            letterSpacing: ".04em",
                        }}>ТЕКУЩИЙ ПЛАН</div>
                        <div className="card-body" style={{ padding: "28px" }}>
                            <div style={{
                                fontSize: "13px",
                                fontWeight: 700,
                                color: "var(--brand)",
                                textTransform: "uppercase",
                                letterSpacing: ".05em",
                                marginBottom: "10px",
                            }}>Pro</div>
                            <div style={{ fontSize: "36px", fontWeight: 900, color: "var(--gray-900)", lineHeight: 1, marginBottom: "4px" }}>
                                {proPrice}
                            </div>
                            <div style={{ fontSize: "13px", color: "var(--gray-400)", marginBottom: "24px" }}>
                                {proPeriodLabel}
                            </div>
                            <button className="btn btn-primary" style={{
                                width: "100%",
                                justifyContent: "center",
                                marginBottom: "24px",
                                opacity: .5,
                                cursor: "default",
                            }}>
                                Активен
                            </button>
                            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                                {[
                                    [true, "До 50 опросов в месяц"],
                                    [true, "До 5 000 ответов в месяц"],
                                    [true, "До 1 000 участников"],
                                    [true, "Все типы вопросов"],
                                    [true, "AI-генерация (200/мес)"],
                                    [true, "AI-аналитика и инсайты"],
                                    [true, "Экспорт PDF"],
                                    [false, "Безлимитные участники"],
                                    [false, "SSO / корпоративный вход"],
                                ].map(([ok, label]) => (
                                    <div key={label} style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "8px",
                                        fontSize: "13px",
                                        color: ok ? "var(--gray-600)" : "var(--gray-300)",
                                    }}>
                                        <span style={{ fontWeight: 700, color: ok ? "var(--success)" : undefined }}>{ok ? "✓" : "✗"}</span>
                                        {label}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Enterprise */}
                    <div className="card" style={{
                        position: "relative",
                        background: "linear-gradient(160deg,#1E1B4B 0%,#1e2a4b 100%)",
                        borderColor: "#312E81",
                    }}>
                        <div className="card-body" style={{ padding: "28px" }}>
                            <div style={{
                                fontSize: "13px",
                                fontWeight: 700,
                                color: "#A78BFA",
                                textTransform: "uppercase",
                                letterSpacing: ".05em",
                                marginBottom: "10px",
                            }}>Enterprise</div>
                            <div style={{ fontSize: "36px", fontWeight: 900, color: "#fff", lineHeight: 1, marginBottom: "4px" }}>
                                По запросу
                            </div>
                            <div style={{ fontSize: "13px", color: "rgba(255,255,255,.4)", marginBottom: "24px" }}>
                                Индивидуальные условия
                            </div>
                            <button className="btn btn-sm" style={{
                                width: "100%",
                                justifyContent: "center",
                                marginBottom: "24px",
                                background: "rgba(255,255,255,.15)",
                                border: "1px solid rgba(255,255,255,.25)",
                                color: "#fff",
                                padding: "10px",
                            }}>
                                Связаться с нами
                            </button>
                            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                                {[
                                    "Безлимитные опросы",
                                    "Безлимитные ответы",
                                    "Безлимитные участники",
                                    "AI-генерация без ограничений",
                                    "SSO / корпоративный вход",
                                    "Выделенный менеджер",
                                    "SLA и приоритетная поддержка",
                                    "Брендирование интерфейса",
                                ].map((label) => (
                                    <div key={label} style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "8px",
                                        fontSize: "13px",
                                        color: "rgba(255,255,255,.75)",
                                    }}>
                                        <span style={{ fontWeight: 700, color: "#10B981" }}>✓</span>
                                        {label}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                </div>

                {/* Payment history */}
                <div className="section-header" style={{ marginBottom: "16px" }}>
                    <div className="section-title">История платежей</div>
                    <button className="btn btn-ghost btn-sm">Скачать все</button>
                </div>
                <div className="survey-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Дата</th>
                                <th>Описание</th>
                                <th>Сумма</th>
                                <th>Статус</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {[
                                ["28 мар 2026", "Pro · Ежемесячный план", "Visa •••• 4242", "2 990 ₽"],
                                ["28 фев 2026", "Pro · Ежемесячный план", "Visa •••• 4242", "2 990 ₽"],
                                ["28 янв 2026", "Pro · Ежемесячный план", "Visa •••• 4242", "2 990 ₽"],
                                ["28 дек 2025", "Переход с Free на Pro", "Visa •••• 4242", "2 990 ₽"],
                            ].map(([date, desc, card, amount]) => (
                                <tr key={date}>
                                    <td style={{ color: "var(--gray-500)", fontSize: "13px" }}>{date}</td>
                                    <td>
                                        <div className="survey-name">{desc}</div>
                                        <div className="survey-meta">{card}</div>
                                    </td>
                                    <td style={{ fontWeight: 700, color: "var(--gray-900)" }}>{amount}</td>
                                    <td><span className="status-badge active">Оплачено</span></td>
                                    <td><button className="btn btn-ghost btn-sm">Квитанция</button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

            </div>
        </div>
    )
}
