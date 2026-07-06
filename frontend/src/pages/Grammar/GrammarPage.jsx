import { useEffect, useState } from "react";
import client from "../../api/client";
import styles from "./GrammarPage.module.css";

const MOCK_CONCEPTS = [
    { id: 1, title: "Ser vs Estar", status: "done" },
    { id: 2, title: "Preterite Tense", status: "done" },
    { id: 3, title: "Imperfect Tense", status: "done" },
    { id: 4, title: "Subjunctive Mood", status: "current" },
    { id: 5, title: "Conditional Tense", status: "locked" },
    { id: 6, title: "Future Tense", status: "locked" },
];

const MOCK_LESSON = {
    conceptId: 4,
    title: "The Subjunctive Mood",
    explanation: {
        summary: "가정법(el subjuntivo)은 의심, 바람, 감정, 가정 상황을 표현할 때 사용합니다. 직설법과 달리 사실을 서술하지 않습니다.",
        usages: [
            { label: "의심", example: "Dudo que él venga.", translation: "나는 그가 올지 의심스럽다." },
            { label: "바람", example: "Quiero que estudies.", translation: "나는 네가 공부하길 원한다." },
            { label: "감정", example: "Me alegra que estés aquí.", translation: "네가 여기 있어서 기쁘다." },
            { label: "무인칭 표현", example: "Es importante que practiques.", translation: "네가 연습하는 것이 중요하다." },
        ],
    },
    examples: [
        { es: "Espero que tengas un buen día.", ko: "네가 좋은 하루를 보내길 바라." },
        { es: "No creo que sea verdad.", ko: "그게 사실이라고 생각하지 않아." },
        { es: "Ojalá que llueva mañana.", ko: "내일 비가 왔으면 좋겠다." },
    ],
    conjugation: {
        verb: "hablar",
        label: "현재 접속법 (Present Subjunctive)",
        forms: [
            { pronoun: "yo", form: "hable" },
            { pronoun: "tú", form: "hables" },
            { pronoun: "él/ella", form: "hable" },
            { pronoun: "nosotros", form: "hablemos" },
            { pronoun: "vosotros", form: "habléis" },
            { pronoun: "ellos", form: "hablen" },
        ],
    },
};

const MOCK_EXERCISES = [
    { id: 1, prompt: "Quiero que tú ___ conmigo.", hint: "hablar", answer: "hables" },
    { id: 2, prompt: "Es importante que nosotros ___ los verbos.", hint: "aprender", answer: "aprendamos" },
    { id: 3, prompt: "Dudo que ellos ___ la verdad.", hint: "decir", answer: "digan" },
];

const TABS = [
    { key: "explanation", label: "설명" },
    { key: "examples", label: "예문" },
    { key: "conjugation", label: "변화형" },
];

function GrammarPage(){
    const [concepts, setConcepts] = useState(MOCK_CONCEPTS);
    const [selectedConceptId, setSelectedConceptId] = useState(MOCK_LESSON.conceptId);
    const [lesson, setLesson] = useState(MOCK_LESSON);
    const [activeTab, setActiveTab] = useState("explanation");
    const [exercises] = useState(MOCK_EXERCISES);
    const [answers, setAnswers] = useState({});
    const [checked, setChecked] = useState({});
    const [showAnswers, setShowAnswers] = useState(false);

    useEffect(() => {
        client.get("/grammar", { params: { category: "grammar" } })
            .then((res) => {
                if (Array.isArray(res.data?.concepts)){
                    setConcepts(res.data.concepts);
                }
                if (res.data?.lesson){
                    setLesson(res.data.lesson);
                }
            })
            .catch((err) => console.error("문법 학습 데이터 조회 실패:", err));
    }, []);

    const selectedConcept = concepts.find((c) => c.id === selectedConceptId);
    const hasLessonContent = selectedConceptId === lesson.conceptId;

    const handleSelectConcept = (concept) => {
        if (concept.status === "locked") return;
        setSelectedConceptId(concept.id);
        setActiveTab("explanation");
    };

    const handleAnswerChange = (id, value) => {
        setAnswers((prev) => ({ ...prev, [id]: value }));
    };

    const handleCheck = (exercise) => {
        setChecked((prev) => ({ ...prev, [exercise.id]: true }));

        const isCorrect = (answers[exercise.id] ?? "").trim().toLowerCase() === exercise.answer.toLowerCase();
        client.post("/answerlog", {
            content_id: exercise.id,
            type: "grammar",
            is_correct: isCorrect,
            time: new Date().toISOString(),
        }).catch((err) => console.error("답변 기록 전송 실패:", err));
    };

    return (
        <div className={styles.page}>
            <h1 className={styles.title}>문법 학습</h1>
            <p className={styles.subtitle}>{selectedConcept?.title ?? "단원을 선택하세요"}</p>

            <div className={styles.body}>
                <div className={styles.main}>
                    <div className={styles.lessonCard}>
                        <h2 className={styles.lessonTitle}>{hasLessonContent ? lesson.title : selectedConcept?.title}</h2>

                        {hasLessonContent ? (
                            <>
                                <nav className={styles.tabs}>
                                    {TABS.map((tab) => (
                                        <button
                                            key={tab.key}
                                            className={activeTab === tab.key ? `${styles.tab} ${styles.tabActive}` : styles.tab}
                                            onClick={() => setActiveTab(tab.key)}
                                        >
                                            {tab.label}
                                        </button>
                                    ))}
                                </nav>

                                {activeTab === "explanation" && (
                                    <div className={styles.tabContent}>
                                        <p className={styles.summary}>{lesson.explanation.summary}</p>
                                        <ul className={styles.usageList}>
                                            {lesson.explanation.usages.map((usage) => (
                                                <li key={usage.label} className={styles.usageItem}>
                                                    <span className={styles.usageLabel}>{usage.label}</span>
                                                    <span className={styles.usageExample}>{usage.example}</span>
                                                    <span className={styles.usageTranslation}>{usage.translation}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {activeTab === "examples" && (
                                    <div className={styles.tabContent}>
                                        <ul className={styles.exampleList}>
                                            {lesson.examples.map((ex) => (
                                                <li key={ex.es} className={styles.exampleItem}>
                                                    <p className={styles.exampleEs}>{ex.es}</p>
                                                    <p className={styles.exampleKo}>{ex.ko}</p>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {activeTab === "conjugation" && (
                                    <div className={styles.tabContent}>
                                        <p className={styles.conjugationLabel}>
                                            {lesson.conjugation.verb} — {lesson.conjugation.label}
                                        </p>
                                        <table className={styles.conjugationTable}>
                                            <tbody>
                                                {lesson.conjugation.forms.map((f) => (
                                                    <tr key={f.pronoun}>
                                                        <td className={styles.pronoun}>{f.pronoun}</td>
                                                        <td className={styles.form}>{f.form}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </>
                        ) : (
                            <p className={styles.placeholder}>
                                {selectedConcept?.status === "locked"
                                    ? "이전 단원을 먼저 완료하면 잠금이 해제됩니다."
                                    : "이 단원의 학습 콘텐츠는 준비 중입니다."}
                            </p>
                        )}
                    </div>

                    <div className={styles.exerciseCard}>
                        <h2 className={styles.exerciseTitle}>연습 문제</h2>
                        <p className={styles.exerciseSubtitle}>빈칸에 알맞은 접속법 형태를 입력하세요.</p>

                        <ul className={styles.exerciseList}>
                            {exercises.map((exercise, i) => {
                                const isChecked = Boolean(checked[exercise.id]);
                                const value = answers[exercise.id] ?? "";
                                const isCorrect = isChecked && value.trim().toLowerCase() === exercise.answer.toLowerCase();
                                const revealAnswer = showAnswers || (isChecked && !isCorrect);

                                return (
                                    <li key={exercise.id} className={styles.exerciseItem}>
                                        <p className={styles.exercisePrompt}>
                                            {i + 1}. {exercise.prompt}
                                        </p>
                                        <div className={styles.exerciseRow}>
                                            <input
                                                className={
                                                    isChecked
                                                        ? isCorrect
                                                            ? `${styles.exerciseInput} ${styles.inputCorrect}`
                                                            : `${styles.exerciseInput} ${styles.inputIncorrect}`
                                                        : styles.exerciseInput
                                                }
                                                type="text"
                                                placeholder={`(${exercise.hint})`}
                                                value={value}
                                                onChange={(e) => handleAnswerChange(exercise.id, e.target.value)}
                                            />
                                            <button className={styles.checkButton} onClick={() => handleCheck(exercise)}>
                                                확인
                                            </button>
                                        </div>
                                        {revealAnswer && (
                                            <p className={styles.answerHint}>정답: {exercise.answer}</p>
                                        )}
                                    </li>
                                );
                            })}
                        </ul>

                        <button className={styles.linkButton} onClick={() => setShowAnswers((v) => !v)}>
                            {showAnswers ? "정답 숨기기" : "정답 보기"}
                        </button>
                    </div>
                </div>

                <div className={styles.sidebar}>
                    <p className={styles.sidebarTitle}>개념 일람</p>
                    <ul className={styles.conceptList}>
                        {concepts.map((concept) => {
                            const isSelected = concept.id === selectedConceptId;
                            return (
                                <li key={concept.id}>
                                    <button
                                        className={
                                            isSelected
                                                ? `${styles.conceptItem} ${styles.conceptItemActive}`
                                                : styles.conceptItem
                                        }
                                        onClick={() => handleSelectConcept(concept)}
                                        disabled={concept.status === "locked"}
                                    >
                                        <span className={`${styles.conceptDot} ${styles[`dot_${concept.status}`]}`}>
                                            {concept.status === "done" ? "✓" : ""}
                                        </span>
                                        {concept.title}
                                    </button>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default GrammarPage;
