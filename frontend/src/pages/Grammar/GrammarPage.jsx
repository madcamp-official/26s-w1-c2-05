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
    // 한 번이라도 열어본 개념은 검은 점으로 남겨서, 다른 개념을 봤다가 돌아와도
    // 학습 여부 표시가 사라지지 않게 한다.
    const [visited, setVisited] = useState(() => new Set([0]));

    // "오늘의 학습"(spaced-repetition으로 선별된 소수) 과 별개로, 전체 문법 커리큘럼을
    // level 순으로 훑어볼 수 있는 모드. /grammar/all은 첫 전환 시에만 불러온다.
    const [mode, setMode] = useState("today");
    const [allGrammars, setAllGrammars] = useState([]);
    const [allLoaded, setAllLoaded] = useState(false);
    const [selectedAllIndex, setSelectedAllIndex] = useState(0);

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

    useEffect(() => {
        if (mode !== "all" || allLoaded) return;
        client.get("/grammar/all")
            .then((res) => {
                if (Array.isArray(res.data?.grammars)){
                    setAllGrammars(res.data.grammars);
                    setAllLoaded(true);
                }
            })
            .catch((err) => console.error("전체 문법 커리큘럼 조회 실패:", err));
    }, [mode, allLoaded]);

    const currentList = mode === "today" ? grammars : allGrammars;
    const currentIndex = mode === "today" ? selectedIndex : selectedAllIndex;
    const selectedConcept = currentList[currentIndex];
    const { concept, form, exampleMain, exampleTranslation } = parseExplanation(selectedConcept?.explanation);

    const handleTakeQuiz = () => {
        exerciseCardRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    const handleSelectConcept = (index) => {
        setSelectedIndex(index);
        // quiz_content_id는 개념 간에도 고유하므로, 다른 개념으로 이동했다가 돌아와도
        // 이미 풀었던 문제의 답/정오답 표시가 사라지지 않도록 answers/checked는 초기화하지 않는다.
        setVisited((prev) => (prev.has(index) ? prev : new Set(prev).add(index)));
        setShowAnswers(false);
        // 클릭 이벤트 핸들러 안에서만 호출되므로 렌더링과 무관함 (린트 규칙의 오탐).
        // eslint-disable-next-line react-hooks/purity
        conceptShownAt.current = Date.now();
    };

    const handleSelectAllConcept = (index) => {
        setSelectedAllIndex(index);
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
                <div className={styles.tabs}>
                    <button
                        className={mode === "today" ? `${styles.tab} ${styles.tabActive}` : styles.tab}
                        onClick={() => setMode("today")}
                    >
                        오늘의 학습
                    </button>
                    <button
                        className={mode === "all" ? `${styles.tab} ${styles.tabActive}` : styles.tab}
                        onClick={() => setMode("all")}
                    >
                        전체 커리큘럼
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.page}>
            <PageHeader
                title="문법 학습"
                subtitle={
                    mode === "today"
                        ? `단원: ${selectedConcept.subject} · ${selectedIndex + 1}강`
                        : `Lv.${selectedConcept.level} · ${selectedConcept.subject}`
                }
                actions={
                    <>
                        <button className={styles.secondaryButton} onClick={() => navigate("/dashboard")}>
                            ← 전체 단원
                        </button>
                    </>
                }
            />

            <div className={styles.tabs}>
                <button
                    className={mode === "today" ? `${styles.tab} ${styles.tabActive}` : styles.tab}
                    onClick={() => setMode("today")}
                >
                    오늘의 학습
                </button>
                <button
                    className={mode === "all" ? `${styles.tab} ${styles.tabActive}` : styles.tab}
                    onClick={() => setMode("all")}
                >
                    전체 커리큘럼
                </button>
            </div>

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

                    {Array.isArray(selectedConcept.quiz) && (
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
                    )}
                </div>

                <div className={styles.sidebar}>
                    <p className={styles.sidebarTitle}>{mode === "today" ? "개념 일람" : "전체 커리큘럼"}</p>
                    {mode === "today" ? (
                    <ul className={styles.conceptList}>
                        {grammars.map((concept, index) => {
                            const isSelected = index === selectedIndex;
                            const isVisited = visited.has(index);
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
                                        <span className={`${styles.conceptDot} ${isVisited ? styles.dot_current : styles.dot_locked}`} />
                                        {concept.subject}
                                    </button>
                                </li>
                            );
                        })}
                    </ul>
                    ) : (
                    <ul className={styles.conceptList}>
                        {allGrammars.map((item, index) => {
                            const isSelected = index === selectedAllIndex;
                            const prevLevel = index > 0 ? allGrammars[index - 1].level : null;
                            const showLevelHeading = item.level !== prevLevel;
                            return (
                                <li key={item.content_id}>
                                    {showLevelHeading && (
                                        <p className={styles.sidebarGroupLabel}>레벨 {item.level}</p>
                                    )}
                                    <button
                                        className={
                                            isSelected
                                                ? `${styles.conceptItem} ${styles.conceptItemActive}`
                                                : styles.conceptItem
                                        }
                                        onClick={() => handleSelectAllConcept(index)}
                                    >
                                        {item.subject}
                                    </button>
                                </li>
                            );
                        })}
                    </ul>
                    )}
                </div>
            </div>
        </div>
    );
};

export default GrammarPage;
