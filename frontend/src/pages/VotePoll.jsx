import { useEffect, useRef, useState } from "react"
import { useParams } from "react-router-dom"
import { getPollForVote, startVote, submitVote } from "../api/voting"

export default function VotePoll() {
    const { pollId } = useParams()

    const [poll, setPoll] = useState(null)
    const [step, setStep] = useState(0)
    const [answers, setAnswers] = useState({})
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState("")
    const [finished, setFinished] = useState(false)
    const [submitting, setSubmitting] = useState(false)
    const startedRef = useRef(false)

    useEffect(() => {
        async function loadPoll() {
            try {
                const data = await getPollForVote(pollId)
                setPoll(data)

                if (!startedRef.current) {
                    startedRef.current = true
                    await startVote(pollId).catch(() => null)
                }
            } catch (err) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }

        loadPoll()
    }, [pollId])

    if (loading) return <div className="page-loader">Загружаем опрос...</div>
    if (error) return <div className="page-error">{error}</div>
    if (!poll) return <div className="page-error">Опрос не найден</div>

    const questions = poll.questions || []
    const current = questions[step]

    if (!current) {
        return <div className="page-error">В опросе нет вопросов</div>
    }

    const progress = Math.round(((step + 1) / questions.length) * 100)

    const currentAnswer = answers[current.id]

    const isAnswered =
        current.type === "text"
            ? Boolean(currentAnswer?.trim())
            : current.type === "multiple_choice"
                ? Array.isArray(currentAnswer) && currentAnswer.length > 0
                : Boolean(currentAnswer)

    const setSingleAnswer = (questionId, optionId) => {
        setAnswers({
            ...answers,
            [questionId]: optionId,
        })
    }

    const toggleMultipleAnswer = (questionId, optionId) => {
        const prev = answers[questionId] || []

        setAnswers({
            ...answers,
            [questionId]: prev.includes(optionId)
                ? prev.filter(id => id !== optionId)
                : [...prev, optionId],
        })
    }

    const setTextAnswer = (questionId, value) => {
        setAnswers({
            ...answers,
            [questionId]: value,
        })
    }

    const handleNext = () => {
        if (current.is_required && !isAnswered) {
            alert("Ответьте на вопрос, чтобы продолжить")
            return
        }

        setStep(step + 1)
    }

    const handleSubmit = async () => {
        if (submitting) return
        if (current.is_required && !isAnswered) {
            alert("Ответьте на вопрос, чтобы отправить")
            return
        }

        const payloadAnswers = Object.entries(answers).flatMap(([questionId, value]) => {
            const question = questions.find(q => String(q.id) === String(questionId))

            if (Array.isArray(value)) {
                return value.map(optionId => ({
                    question_id: Number(questionId),
                    option_id: Number(optionId),
                    text_value: null,
                }))
            }

            if (question?.type === "text") {
                return {
                    question_id: Number(questionId),
                    option_id: null,
                    text_value: value,
                }
            }

            return {
                question_id: Number(questionId),
                option_id: Number(value),
                text_value: null,
            }
        })

        setSubmitting(true)

        try {
            await submitVote(pollId, payloadAnswers)
            setFinished(true)
        } catch (err) {
            alert(err.message)
        } finally {
            setSubmitting(false)
        }
    }

    if (finished) {
        return (
            <div className="vote-page">
                <div className="vote-card finish-card">
                    <div className="finish-glow"></div>

                    <div className="finish-icon">
                        ✓
                    </div>

                    <div className="finish-kicker">
                        SurveyPulse
                    </div>

                    <h1>
                        Спасибо за участие!
                    </h1>

                    <p>
                        Ваш ответ сохранён анонимно. Вы помогаете сделать опрос точнее и полезнее.
                    </p>

                    <button
                        className="btn btn-primary finish-btn"
                        onClick={() => window.close()}
                    >
                        Закрыть страницу
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="vote-page">
            <div className="vote-card">
                <div className="vote-hero">
                    <div className="survey-company">SurveyPulse</div>
                    <h1>{poll.title}</h1>
                    {poll.description && <p>{poll.description}</p>}
                </div>

                <div className="vote-content">
                    <div className="vote-step-row">
                        <span>
                            Вопрос {step + 1} из {questions.length}
                        </span>

                        <span>
                            {progress}%
                        </span>
                    </div>

                    <div className="vote-progress">
                        <div
                            className="vote-progress-bar"
                            style={{ width: `${progress}%` }}
                        />
                    </div>

                    <div className="vote-question">
                        <div className="sq-label">
                            {current.text}
                            {current.is_required && (
                                <span className="sq-required">*</span>
                            )}
                        </div>

                        {current.type === "text" ? (
                            <textarea
                                className="form-textarea vote-textarea"
                                value={currentAnswer || ""}
                                onChange={(e) =>
                                    setTextAnswer(current.id, e.target.value)
                                }
                                placeholder="Введите ваш ответ..."
                            />
                        ) : current.type === "scale" ? (
                            <div className="vote-scale">
                                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((value) => {
                                    const option = (current.options || []).find(
                                        o => String(o.text) === String(value)
                                    )

                                    const optionId =
                                        option?.id ||
                                        option?.position ||
                                        value

                                    const checked = currentAnswer === optionId

                                    return (
                                        <button
                                            type="button"
                                            key={value}
                                            className={`vote-scale-btn ${checked ? "selected" : ""}`}
                                            onClick={() => setSingleAnswer(current.id, optionId)}
                                        >
                                            {value}
                                        </button>
                                    )
                                })}

                                <div className="vote-scale-labels">
                                    <span>Совсем не согласен</span>
                                    <span>Полностью согласен</span>
                                </div>
                            </div>
                        ) : (
                            <div className="vote-options">
                                {(current.options || []).map((option) => {
                                    const optionId = option.id || option.position || option.text

                                    const checked =
                                        current.type === "multiple_choice"
                                            ? (currentAnswer || []).includes(optionId)
                                            : currentAnswer === optionId

                                    return (
                                        <label
                                            className={`vote-option ${checked ? "selected" : ""}`}
                                            key={optionId}
                                        >
                                            <input
                                                type={
                                                    current.type === "multiple_choice"
                                                        ? "checkbox"
                                                        : "radio"
                                                }
                                                name={`question-${current.id}`}
                                                checked={checked}
                                                onChange={() => {
                                                    if (current.type === "multiple_choice") {
                                                        toggleMultipleAnswer(current.id, optionId)
                                                    } else {
                                                        setSingleAnswer(current.id, optionId)
                                                    }
                                                }}
                                            />

                                            <span>{option.text}</span>
                                        </label>
                                    )
                                })}
                            </div>
                        )}
                    </div>

                    <div className="vote-actions">
                        <button
                            className="btn btn-secondary"
                            disabled={step === 0}
                            onClick={() => setStep(step - 1)}
                        >
                            ← Назад
                        </button>

                        {step < questions.length - 1 ? (
                            <button
                                className="btn btn-primary"
                                onClick={handleNext}
                            >
                                Далее →
                            </button>
                        ) : (
                            <button
                                className="btn btn-primary"
                                onClick={handleSubmit}
                                disabled={submitting}
                            >
                                {submitting ? "Отправляем..." : "Отправить ответы"}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}