import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { loginUser, registerUser } from "../api/auth"

export default function Login() {
    const [tab, setTab] = useState("login")

    const navigate = useNavigate()

    const [loginForm, setLoginForm] = useState({
        email: "",
        password: "",
    })

    const [registerForm, setRegisterForm] = useState({
        first_name: "",
        last_name: "",
        email: "",
        company_name: "",
        password: "",
        confirmed_password: "",
    })

    const [error, setError] = useState("")
    const [loading, setLoading] = useState(false)

    const handleLoginChange = (e) => {
        setLoginForm({
            ...loginForm,
            [e.target.name]: e.target.value,
        })
    }

    const handleRegisterChange = (e) => {
        setRegisterForm({
            ...registerForm,
            [e.target.name]: e.target.value,
        })
    }

    const handleLoginSubmit = async (e) => {
        e.preventDefault()
        setError("")
        setLoading(true)

        try {
            const data = await loginUser(loginForm)

            localStorage.setItem("access_token", data.access_token.access_token)
            localStorage.setItem("refresh_token", data.refresh_token.refresh_token)
            localStorage.setItem("user_email", data.access_token.user_email)

            navigate("/")
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const handleRegisterSubmit = async (e) => {
        e.preventDefault()
        setError("")
        setLoading(true)

        try {
            await registerUser({
                ...registerForm,
                position: "",
                phone: "",
                interface_language: "ru",
                avatar_url: "",
            })

            setTab("login")
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="auth-overlay">
            <div className="auth-left">
                <div className="auth-left-content">
                    <div className="auth-brand">
                        <div className="auth-brand-icon">
                            <svg viewBox="0 0 20 20">
                                <path d="M2 4h16v2H2V4zm0 5h10v2H2V9zm0 5h13v2H2v-2z" />
                            </svg>
                        </div>
                        <span className="auth-brand-name">SurveyPulse</span>
                        <span className="auth-brand-badge">BETA</span>
                    </div>

                    <div className="auth-hero-title">
                        Корпоративные опросы<br />
                        нового <span>поколения</span>
                    </div>

                    <div className="auth-hero-sub">
                        Создавайте опросы, собирайте ответы и получайте AI-аналитику в одном инструменте.
                        Быстро, удобно, безопасно.
                    </div>

                    <div className="auth-features">
                        <div className="auth-feature">
                            <div className="auth-feature-dot">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path d="M11.3 1.05a.75.75 0 0 1 .44.86L10.6 7h4.65a.75.75 0 0 1 .58 1.23l-8 9.75a.75.75 0 0 1-1.31-.62L7.65 12H3.75a.75.75 0 0 1-.62-1.17l7.25-9.5a.75.75 0 0 1 .92-.28z" />
                                </svg>
                            </div>
                            <span className="auth-feature-text">AI генерирует опросы по описанию за секунды</span>
                        </div>

                        <div className="auth-feature">
                            <div className="auth-feature-dot">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path d="M9.65 17.55l-.05-.03C4.9 14.1 2 11.45 2 8.2A4.2 4.2 0 0 1 6.25 4c1.35 0 2.65.63 3.4 1.63A4.27 4.27 0 0 1 13.05 4 4.2 4.2 0 0 1 17.3 8.2c0 3.25-2.9 5.9-7.6 9.32l-.05.03z" />
                                </svg>
                            </div>
                            <span className="auth-feature-text">Анализ тональности и ключевых тем из ответов</span>
                        </div>

                        <div className="auth-feature">
                            <div className="auth-feature-dot">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path d="M7 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm6.5 0a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM7 10.5c-3 0-5 1.45-5 3.25V15a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1.25c0-1.8-2-3.25-5-3.25zm6.5.25c-.45 0-.88.04-1.28.12.8.7 1.28 1.65 1.28 2.88V15a2.6 2.6 0 0 1-.08.6H17a1 1 0 0 0 1-1v-.85c0-1.66-1.8-3-4.5-3z" />
                                </svg>
                            </div>
                            <span className="auth-feature-text">Сегментация по отделам, ролям и группам</span>
                        </div>

                        <div className="auth-feature">
                            <div className="auth-feature-dot">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path d="M5 8V6a5 5 0 0 1 10 0v2h.5A1.5 1.5 0 0 1 17 9.5v6A1.5 1.5 0 0 1 15.5 17h-11A1.5 1.5 0 0 1 3 15.5v-6A1.5 1.5 0 0 1 4.5 8H5zm2 0h6V6a3 3 0 0 0-6 0v2z" />
                                </svg>
                            </div>
                            <span className="auth-feature-text">Полная анонимность и защита данных</span>
                        </div>
                    </div>
                </div>

                <div className="auth-left-footer">
                    <div className="auth-left-footer-text">© 2026 SurveyPulse · Все права защищены</div>
                </div>
            </div>

            <div className="auth-right">
                <div className="auth-box">
                    <div className="auth-tabs">
                        <div
                            className={`auth-tab ${tab === "login" ? "active" : ""}`}
                            onClick={() => setTab("login")}
                        >
                            Войти
                        </div>

                        <div
                            className={`auth-tab ${tab === "register" ? "active" : ""}`}
                            onClick={() => setTab("register")}
                        >
                            Регистрация
                        </div>
                    </div>

                    {error && <div style={{ color: "red", marginBottom: 12 }}>{error}</div>}

                    <form
                        className={`auth-form ${tab === "login" ? "active" : ""}`}
                        onSubmit={handleLoginSubmit}
                    >
                        <div className="auth-title">Добро пожаловать</div>
                        <div className="auth-subtitle">Введите данные вашего аккаунта</div>

                        <div className="auth-field">
                            <label>Email</label>
                            <input
                                name="email"
                                type="email"
                                placeholder="you@company.com"
                                value={loginForm.email}
                                onChange={handleLoginChange}
                            />
                        </div>

                        <div className="auth-field">
                            <label>Пароль</label>
                            <input
                                name="password"
                                type="password"
                                placeholder="Ваш пароль"
                                value={loginForm.password}
                                onChange={handleLoginChange}
                            />
                        </div>

                        <div className="auth-forgot">
                            <a href="#">Забыли пароль?</a>
                        </div>

                        <button className="auth-submit" disabled={loading}>
                            {loading ? "Входим..." : "Войти в аккаунт"}
                        </button>

                        <div className="auth-switch">
                            Нет аккаунта?{" "}
                            <a onClick={() => setTab("register")}>Зарегистрироваться</a>
                        </div>
                    </form>

                    <form
                        className={`auth-form ${tab === "register" ? "active" : ""}`}
                        onSubmit={handleRegisterSubmit}
                    >
                        <div className="auth-title">Создать аккаунт</div>
                        <div className="auth-subtitle">Начните бесплатно — без карты</div>

                        <div className="auth-row">
                            <div className="auth-field">
                                <label>Имя</label>
                                <input
                                    name="first_name"
                                    type="text"
                                    placeholder="Алексей"
                                    value={registerForm.first_name}
                                    onChange={handleRegisterChange}
                                />
                            </div>

                            <div className="auth-field">
                                <label>Фамилия</label>
                                <input
                                    name="last_name"
                                    type="text"
                                    placeholder="Козлов"
                                    value={registerForm.last_name}
                                    onChange={handleRegisterChange}
                                />
                            </div>
                        </div>

                        <div className="auth-field">
                            <label>Рабочий email</label>
                            <input
                                name="email"
                                type="email"
                                placeholder="you@company.com"
                                value={registerForm.email}
                                onChange={handleRegisterChange}
                            />
                        </div>

                        <div className="auth-field">
                            <label>Название компании</label>
                            <input
                                name="company_name"
                                type="text"
                                placeholder="TechCorp"
                                value={registerForm.company_name}
                                onChange={handleRegisterChange}
                            />
                        </div>

                        <div className="auth-row">
                            <div className="auth-field">
                                <label>Пароль</label>
                                <input
                                    name="password"
                                    type="password"
                                    placeholder="Минимум 8 символов"
                                    value={registerForm.password}
                                    onChange={handleRegisterChange}
                                />
                            </div>

                            <div className="auth-field">
                                <label>Повторите пароль</label>
                                <input
                                    name="confirmed_password"
                                    type="password"
                                    placeholder="••••••••"
                                    value={registerForm.confirmed_password}
                                    onChange={handleRegisterChange}
                                />
                            </div>
                        </div>

                        <button className="auth-submit" disabled={loading}>
                            {loading ? "Создаём..." : "Создать аккаунт"}
                        </button>

                        <div className="auth-terms">
                            Регистрируясь, вы соглашаетесь с{" "}
                            <a href="#">Условиями использования</a> и{" "}
                            <a href="#">Политикой конфиденциальности</a>
                        </div>

                        <div className="auth-switch">
                            Уже есть аккаунт?{" "}
                            <a onClick={() => setTab("login")}>Войти</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    )
}