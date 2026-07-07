import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../../api/client";
import PageHeader from "../../components/PageHeader";
import styles from "./GrammarPage.module.css";

// grammar_expl은 "개념 설명. 형태: ~. 예문: ~ (번역)" 형식의 한 문단으로 오므로,
// 색상 블록으로 나눠 보여주기 위해 형태/예문 구간을 분리한다.
function parseExplanation(text){
    if (!text) return { concept: "", form: "", exampleMain: "", exampleTranslation: "" };

    const formIdx = text.indexOf("형태:");
    const exampleIdx = text.indexOf("예문:");
    if (formIdx === -1 || exampleIdx === -1){
        return { concept: text, form: "", exampleMain: "", exampleTranslation: "" };
    }

    const concept = text.slice(0, formIdx).trim();
    const form = text.slice(formIdx + "형태:".length, exampleIdx).trim();
    const exampleRaw = text.slice(exampleIdx + "예문:".length).trim();

    const match = exampleRaw.match(/^(.*?)(\([^)]*\))\s*$/);
    const exampleMain = match ? match[1].trim() : exampleRaw;
    const exampleTranslation = match ? match[2].trim() : "";

    return { concept, form, exampleMain, exampleTranslation };
}

function GrammarPage(){
    const navigate = useNavigate();
    const exerciseCardRef = useRef(null);
    const conceptShownAt = useRef(null);
    const [grammars, setGrammars] = useState([]);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [answers, setAnswers] = useState({});
    const [checked, setChecked] = useState({});
    const [showAnswers, setShowAnswers] = useState(false);

    useEffect(() => {
        client.get("/grammar")
            .then((res) => {
                if (Array.isArray(res.data?.grammars)){
                    setGrammars(res.data.grammars);
                    conceptShownAt.current = Date.now();
                }
            })
            .catch((err) => console.error("문법 학습 데이터 조회 실패:", err));
    }, []);

    const selectedConcept = grammars[selectedIndex];
    const { concept, form, exampleMain, exampleTranslation } = parseExplanation(selectedConcept?.explanation);

    const handleTakeQuiz = () => {
        exerciseCardRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    const handleSelectConcept = (index) => {
        setSelectedIndex(index);
        setAnswers({});
        setChecked({});
        setShowAnswers(false);
        // 클릭 이벤트 핸들러 안에서만 호출되므로 렌더링과 무관함 (린트 규칙의 오탐).
        // eslint-disable-next-line react-hooks/purity
        conceptShownAt.current = Date.now();
    };

    const handleAnswerChange = (quizContentId, value) => {
        setAnswers((prev) => ({ ...prev, [quizContentId]: value }));
    };

    const handleCheck = (quiz) => {
        setChecked((prev) => ({ ...prev, [quiz.quiz_content_id]: true }));

        const value = (answers[quiz.quiz_content_id] ?? "").trim();
        const isCorrect = value.toLowerCase() === quiz.answer.trim().toLowerCase();
        const responseTime = (Date.now() - conceptShownAt.current) / 1000;

        client.post("/answerlog", {
            content_id: quiz.quiz_content_id,
            type: "grammar",
            response_time: responseTime,
            is_correct: isCorrect,
            time: new Date().toISOString(),
        }).catch((err) => console.error("답변 기록 전송 실패:", err));
    };

    if (!selectedConcept){
        return (
            <div className={styles.page}>
                <PageHeader title="문법 학습" subtitle="문법 데이터를 불러오는 중입니다..." />
            </div>
        );
    }

    return (
        <div className={styles.page}>
            <PageHeader
                title="문법 학습"
                subtitle={`단원: ${selectedConcept.subject} · ${selectedIndex + 1}강`}
                actions={
                    <>
                        <button className={styles.secondaryButton} onClick={() => navigate("/dashboard")}>
                            ← 전체 단원
                        </button>
                        <button className={styles.primaryInlineButton} onClick={handleTakeQuiz}>
                            퀴즈 풀기
                        </button>
                    </>
                }
            />

            <div className={styles.body}>
                <div className={styles.main}>
                    <div className={styles.lessonCard}>
                        <h2 className={styles.lessonTitle}>{selectedConcept.subject}</h2>
                        <p className={styles.summary}>{concept}</p>
                        {form && (
                            <div className={styles.formBox}>
                                <span className={styles.formLabel}>형태</span>
                                <p className={styles.formText}>{form}</p>
                            </div>
                        )}
                        {exampleMain && (
                            <div className={styles.exampleBox}>
                                <span className={styles.exampleLabel}>예문</span>
                                <p className={styles.exampleText}>
                                    {exampleMain}
                                    {exampleTranslation && (
                                        <span className={styles.exampleTranslation}> {exampleTranslation}</span>
                                    )}
                                </p>
                            </div>
                        )}
                    </div>

                    <div className={styles.exerciseCard} ref={exerciseCardRef}>
                        <h2 className={styles.exerciseTitle}>연습 문제</h2>
                        <p className={styles.exerciseSubtitle}>빈칸에 알맞은 표현을 입력하세요.</p>

                        <ul className={styles.exerciseList}>
                            {selectedConcept.quiz.map((quiz, i) => {
                                const isChecked = Boolean(checked[quiz.quiz_content_id]);
                                const value = answers[quiz.quiz_content_id] ?? "";
                                const isCorrect = isChecked && value.trim().toLowerCase() === quiz.answer.trim().toLowerCase();
                                const revealAnswer = showAnswers || (isChecked && !isCorrect);

                                return (
                                    <li key={quiz.quiz_content_id} className={styles.exerciseItem}>
                                        <p className={styles.exercisePrompt}>
                                            {i + 1}. {quiz.quiz}
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
                                                value={value}
                                                onChange={(e) => handleAnswerChange(quiz.quiz_content_id, e.target.value)}
                                            />
                                            <button className={styles.checkButton} onClick={() => handleCheck(quiz)}>
                                                확인
                                            </button>
                                        </div>
                                        {revealAnswer && (
                                            <p className={styles.answerHint}>정답: {quiz.answer}</p>
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
                        {grammars.map((concept, index) => {
                            const isSelected = index === selectedIndex;
                            return (
                                <li key={concept.content_id}>
                                    <button
                                        className={
                                            isSelected
                                                ? `${styles.conceptItem} ${styles.conceptItemActive}`
                                                : styles.conceptItem
                                        }
                                        onClick={() => handleSelectConcept(index)}
                                    >
                                        <span className={`${styles.conceptDot} ${isSelected ? styles.dot_current : styles.dot_locked}`} />
                                        {concept.subject}
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
