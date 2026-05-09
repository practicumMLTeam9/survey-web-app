export default function CreatePoll() {
    return (
        <div className="page active">
            <div className="topbar">
                <div className="topbar-title">Создать опрос</div>

                <div className="topbar-actions">
                    <button className="btn btn-secondary">Сохранить черновик</button>
                    <button className="btn btn-primary">● Опубликовать</button>
                </div>
            </div>

            <div className="create-page">
                <div className="create-mode-grid">
                    <div className="create-mode-card">
                        <div className="create-mode-icon">✎</div>
                        <div className="create-mode-title">Создать вручную</div>
                        <div className="create-mode-text">
                            Заполните форму самостоятельно — добавляйте вопросы, выбирайте типы ответов и настраивайте опрос под свои нужды.
                        </div>
                    </div>

                    <div className="create-mode-card active">
                        <div className="create-mode-icon">⚡</div>
                        <div className="create-mode-title">
                            Создать с помощью AI <span>NEW</span>
                        </div>
                        <div className="create-mode-text">
                            Опишите цель опроса — AI сгенерирует структуру, вопросы и типы ответов за секунды.
                        </div>
                    </div>
                </div>

                <div className="create-ai-box">
                    <div className="create-ai-label">⚡ POWERED BY CLAUDE · ОПИШИТЕ ВАШ ОПРОС</div>

                    <textarea placeholder="Например: Нам нужен квартальный пульс-опрос для 200 сотрудников. Хотим понять уровень вовлечённости, отношение к remote-формату и запросы по обучению. Тон — дружелюбный, анонимный." />

                    <div className="create-ai-tags">
                        <span>Пульс-опрос сотрудников</span>
                        <span>NPS после поддержки</span>
                        <span>Оценка онбординга</span>
                        <span>Опрос после события</span>
                        <span>360° оценка руководителя</span>
                        <span>Exit interview</span>
                    </div>

                    <div className="create-ai-bottom">
                        <div className="create-ai-selects">
                            <select><option>🎯 Аудитория: Сотрудники</option></select>
                            <select><option>📝 Тон: Формальный</option></select>
                            <select><option>5 вопросов</option></select>
                            <select><option>🔒 Анонимно</option></select>
                        </div>

                        <button className="create-ai-btn">⚡ Сгенерировать опрос</button>
                    </div>
                </div>

                <div className="create-bottom-grid">
                    <div className="create-form-card">
                        <div className="create-card-title">Основная информация</div>

                        <label>Название опроса</label>
                        <input defaultValue="Оценка удовлетворённости сотрудников Q2" />

                        <label>Описание <span>(необязательно)</span></label>
                        <textarea defaultValue="Помогите нам стать лучше — пройдите короткий опрос о вашем опыте работы. Это займёт около 3 минут." />

                        <div className="create-two-cols">
                            <div>
                                <label>Тип опроса</label>
                                <select><option>Корпоративный</option></select>
                            </div>

                            <div>
                                <label>Язык</label>
                                <select><option>Русский</option></select>
                            </div>
                        </div>
                    </div>

                    <div className="create-settings-card">
                        <div className="create-card-title">Настройки</div>

                        <label>Количество участников</label>
                        <div className="participants-row">
                            <input defaultValue="280" />
                            <span>человек</span>
                            <label className="check">
                                <input type="checkbox" />
                                Без ограничений
                            </label>
                        </div>

                        <div className="setting-row">
                            <div>
                                <b>Показать прогресс</b>
                                <p>Шкала прогресса в опросе</p>
                            </div>
                            <input type="checkbox" defaultChecked />
                        </div>

                        <div className="setting-row">
                            <div>
                                <b>Уведомления</b>
                                <p>Email при новом ответе</p>
                            </div>
                            <input type="checkbox" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}