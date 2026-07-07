import { useEffect, useRef, useState } from "react";
import client from "../../api/client";
import styles from "./FlashcardPage.module.css";

const MOCK_VOCABULARIES = [
    {
        number: 1,
        content_id: 4321,
        language: "Spanish",
        word: "el restaurante",
        choices: ["the kitchen", "the restaurant", "the market", "the café"],
        answer: 2,
    },
    {
        number: 2,
        content_id: 4322,
        language: "Spanish",
        word: "la mesa",
        choices: ["the chair", "the table", "the door", "the window"],
        answer: 2,
    },
    {
        number: 3,
        content_id: 4323,
        language: "Spanish",
        word: "el menú",
        choices: ["the menu", "the bill", "the waiter", "the tip"],
        answer: 1,
    },
];

function FlashcardPage(){
    const [vocabularies, setVocabularies] = useState(MOCK_VOCABULARIES);
    const [index, setIndex] = useState(0);
    const [selected, setSelected] = useState(null);
    const [correctCount, setCorrectCount] = useState(0);
    const [incorrectCount, setIncorrectCount] = useState(0);
    const [lastResponseTime, setLastResponseTime] = useState(null);
    const [isPaused, setIsPaused] = useState(false);
    const [elapsed, setElapsed] = useState(0);
    const cardShownAt = useRef(null);
    const pausedAt = useRef(null);

    useEffect(() => {
        client.get("/flashcard", { params: { category: "flash" } })
            .then((res) => {
                console.log("플래시카드 응답:", res.data);
                if (Array.isArray(res.data?.vocabularies)){
                    setVocabularies(res.data.vocabularies);
                    cardShownAt.current = Date.now();
                }
            })
            .catch((err) => console.error("플래시카드 조회 실패:", err));
    }, []);

    useEffect(() => {
        cardShownAt.current = Date.now();
    }, [index]);

    useEffect(() => {
        if (isPaused || selected) return undefined;

        const tick = () => setElapsed((Date.now() - cardShownAt.current) / 1000);
        tick();
        const id = setInterval(tick, 100);
        return () => clearInterval(id);
    }, [isPaused, selected, index]);

    const current = vocabularies[index];

    const cardsDone = correctCount + incorrectCount;
    const accuracy = cardsDone === 0 ? "-" : `${Math.round((correctCount / cardsDone) * 100)}%`;

    const handleSelect = (choice, choiceIndex) => {
        if (selected) return;
        setSelected(choice);

        const isCorrect = choiceIndex + 1 === current.answer;
        // 클릭 이벤트 핸들러 안에서만 호출되므로 렌더링과 무관함 (린트 규칙의 오탐).
        // eslint-disable-next-line react-hooks/purity
        const responseTime = (Date.now() - cardShownAt.current) / 1000;
        setLastResponseTime(responseTime);

        client.post("/answerlog", {
            content_id: current.content_id,
            type: "flash",
            response_time: responseTime,
            is_correct: isCorrect,
            time: new Date().toISOString(),
        }).catch((err) => console.error("답변 기록 전송 실패:", err));

        if (isCorrect){
            setCorrectCount((c) => c + 1);
        } else {
            setIncorrectCount((c) => c + 1);
        }
    };

    const goToIndex = (nextIndex) => {
        if (nextIndex < 0 || nextIndex >= vocabularies.length) return;
        setIndex(nextIndex);
        setSelected(null);
        setLastResponseTime(null);
        setIsPaused(false);
        setElapsed(0);
        pausedAt.current = null;
    };

    const handleTogglePause = () => {
        if (isPaused){
            const pausedDuration = Date.now() - pausedAt.current;
            cardShownAt.current += pausedDuration;
            pausedAt.current = null;
            setIsPaused(false);
        } else {
            pausedAt.current = Date.now();
            setIsPaused(true);
        }
    };

    const handleResetTimer = () => {
        cardShownAt.current = Date.now();
        setElapsed(0);
        if (isPaused){
            pausedAt.current = Date.now();
        }
    };

    if (!current){
        return <div className={styles.page}>단어를 불러오는 중입니다...</div>;
    }

    return (
        <div className={styles.page}>
            <div className={styles.headerRow}>
                <div>
                    <h1 className={styles.title}>플래시카드 퀴즈</h1>
                    <p className={styles.subtitle}>Card {index + 1} of {vocabularies.length}</p>
                </div>

                <div className={styles.timerCluster}>
                    <span className={styles.timerBadge}>
                        <span className={isPaused ? styles.timerDotPaused : styles.timerDot} />
                        {elapsed.toFixed(1)}s
                    </span>
                    <button
                        className={isPaused ? `${styles.pauseButton} ${styles.pauseButtonActive}` : styles.pauseButton}
                        onClick={handleTogglePause}
                    >
                        {isPaused ? "▶ 재개" : "⏸ 일시정지"}
                    </button>
                    <button
                        className={`${styles.pauseButton} ${styles.resetButton}`}
                        onClick={handleResetTimer}
                    >
                        <span className={styles.resetIcon}>⟲</span> 리셋
                    </button>
                </div>
            </div>

            <div className={styles.progressBar}>
                <div
                    className={styles.progressBarFill}
                    style={{ width: `${(cardsDone / vocabularies.length) * 100}%` }}
                />
            </div>

            <div className={styles.body}>
                <div className={styles.cardArea}>
                    <div className={styles.card}>
                        <p className={styles.word}>{current.word}</p>
                        <p className={styles.hint}>알맞은 뜻을 선택하세요</p>

                        {isPaused && (
                            <div className={styles.pauseOverlay}>
                                <span className={styles.pauseOverlayIcon}>⏸</span>
                                <span>일시정지 중</span>
                            </div>
                        )}
                    </div>

                    <div className={styles.choices}>
                        {current.choices.map((choice, i) => {
                            const isCorrect = i + 1 === current.answer;
                            const isSelected = choice === selected;
                            const showResult = selected !== null;

                            let choiceClass = styles.choice;
                            if (showResult && isCorrect) choiceClass += ` ${styles.choiceCorrect}`;
                            else if (showResult && isSelected) choiceClass += ` ${styles.choiceIncorrect}`;

                            return (
                                <button
                                    key={choice}
                                    className={choiceClass}
                                    onClick={() => handleSelect(choice, i)}
                                    disabled={showResult || isPaused}
                                >
                                    <span className={styles.choiceLabel}>{String.fromCharCode(65 + i)}</span>
                                    {choice}
                                </button>
                            );
                        })}
                    </div>

                    {lastResponseTime !== null && (
                        <p className={styles.hint}>{lastResponseTime.toFixed(1)}초 만에 답했어요</p>
                    )}

                    <div className={styles.actions}>
                        <button className={styles.secondaryButton} onClick={() => goToIndex(index - 1)} disabled={isPaused}>
                            이전
                        </button>
                        <button className={styles.secondaryButton} onClick={() => goToIndex(index + 1)} disabled={isPaused}>
                            건너뛰기
                        </button>
                        <button
                            className={styles.primaryButton}
                            onClick={() => goToIndex(index + 1)}
                            disabled={!selected || isPaused}
                        >
                            다음
                        </button>
                    </div>
                </div>

                <div className={styles.stats}>
                    <p className={styles.statsTitle}>SESSION STATS</p>
                    <div className={styles.statRow}>
                        <span>Cards done</span>
                        <span>{cardsDone} / {vocabularies.length}</span>
                    </div>
                    <div className={styles.statRow}>
                        <span>Correct</span>
                        <span>{correctCount}</span>
                    </div>
                    <div className={styles.statRow}>
                        <span>Incorrect</span>
                        <span>{incorrectCount}</span>
                    </div>
                    <div className={styles.statRow}>
                        <span>Accuracy</span>
                        <span>{accuracy}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FlashcardPage;
