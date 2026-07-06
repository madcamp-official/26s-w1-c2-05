import { useEffect, useRef, useState } from "react";
import client from "../../api/client";
import styles from "./FlashcardPage.module.css";

const MOCK_VOCABULARIES = [
    {
        number: 1,
        content_id: 4321,
        language: "Spanish",
        word: "el restaurante",
        meaning: "the restaurant",
        choices: ["the kitchen", "the restaurant", "the market", "the café"],
        answer: "the restaurant",
    },
    {
        number: 2,
        content_id: 4322,
        language: "Spanish",
        word: "la mesa",
        meaning: "the table",
        choices: ["the chair", "the table", "the door", "the window"],
        answer: "the table",
    },
    {
        number: 3,
        content_id: 4323,
        language: "Spanish",
        word: "el menú",
        meaning: "the menu",
        choices: ["the menu", "the bill", "the waiter", "the tip"],
        answer: "the menu",
    },
];

function FlashcardPage(){
    const [vocabularies, setVocabularies] = useState(MOCK_VOCABULARIES);
    const [index, setIndex] = useState(0);
    const [selected, setSelected] = useState(null);
    const [correctCount, setCorrectCount] = useState(0);
    const [incorrectCount, setIncorrectCount] = useState(0);
    const cardShownAt = useRef(Date.now());

    useEffect(() => {
        client.get("/flashcard", { params: { category: "flash" } })
            .then((res) => {
                console.log("플래시카드 응답:", res.data);
                if (Array.isArray(res.data?.vocabularies)){
                    setVocabularies(res.data.vocabularies);
                }
            })
            .catch((err) => console.error("플래시카드 조회 실패:", err));
    }, []);

    useEffect(() => {
        cardShownAt.current = Date.now();
    }, [index]);

    const current = vocabularies[index];

    const cardsDone = correctCount + incorrectCount;
    const accuracy = cardsDone === 0 ? "-" : `${Math.round((correctCount / cardsDone) * 100)}%`;

    const handleSelect = (choice) => {
        if (selected) return;
        setSelected(choice);

        const isCorrect = choice === current.answer;
        const responseTime = (Date.now() - cardShownAt.current) / 1000;

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
    };

    if (!current){
        return <div className={styles.page}>단어를 불러오는 중입니다...</div>;
    }

    return (
        <div className={styles.page}>
            <h1 className={styles.title}>플래시카드 퀴즈</h1>
            <p className={styles.subtitle}>Card {index + 1} of {vocabularies.length}</p>

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
                    </div>

                    <div className={styles.choices}>
                        {current.choices.map((choice, i) => {
                            const isCorrect = choice === current.answer;
                            const isSelected = choice === selected;
                            const showResult = selected !== null;

                            let choiceClass = styles.choice;
                            if (showResult && isCorrect) choiceClass += ` ${styles.choiceCorrect}`;
                            else if (showResult && isSelected) choiceClass += ` ${styles.choiceIncorrect}`;

                            return (
                                <button
                                    key={choice}
                                    className={choiceClass}
                                    onClick={() => handleSelect(choice)}
                                    disabled={showResult}
                                >
                                    <span className={styles.choiceLabel}>{String.fromCharCode(65 + i)}</span>
                                    {choice}
                                </button>
                            );
                        })}
                    </div>

                    <div className={styles.actions}>
                        <button className={styles.secondaryButton} onClick={() => goToIndex(index - 1)}>
                            이전
                        </button>
                        <button className={styles.secondaryButton} onClick={() => goToIndex(index + 1)}>
                            건너뛰기
                        </button>
                        <button
                            className={styles.primaryButton}
                            onClick={() => goToIndex(index + 1)}
                            disabled={!selected}
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
