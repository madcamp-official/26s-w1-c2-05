import { useState } from "react";
import client from "../../api/client";
import styles from "./SpeakingPage.module.css";

const MOCK_TOPICS = [
    {
        id: "restaurant",
        title: "Ordering at a Restaurant",
        difficulty: "B1 Intermediate",
        totalExchanges: 8,
        usefulPhrases: ["Me gustaría...", "¿Podría traerme...?", "La cuenta, por favor."],
        script: [
            { sender: "ai", text: "¡Buenas tardes! Bienvenido al Restaurante El Sol. ¿Tiene reservación?" },
            { sender: "user", text: "Sí, tengo una reservación para dos personas a las ocho." },
            {
                sender: "ai",
                text: "¡Perfecto! Venga por aquí, por favor. ¿Le gustaría ver el menú?",
                pronunciationNote: "Good job! \"reservación\" was correct but slightly mispronounced. Focus on the stress: re-ser-va-CIÓN.",
            },
            { sender: "user", text: "Sí, me gustaría ver el menú, por favor. ¿Cuáles son los platos especiales de hoy?" },
            {
                sender: "ai",
                text: "Hoy tenemos paella de mariscos y tortilla española. ¿Qué le gustaría pedir?",
                pronunciationNote: "Nice pace! Try linking words together: \"cuáles_son\" flows more naturally when spoken as one breath.",
            },
            { sender: "user", text: "Me gustaría pedir la paella de mariscos, por favor." },
            { sender: "ai", text: "Excelente elección. ¿Algo para beber?" },
            { sender: "user", text: "Un agua con gas, por favor." },
        ],
    },
    {
        id: "directions",
        title: "Asking for Directions",
        difficulty: "A2 Elementary",
        totalExchanges: 6,
        usefulPhrases: ["¿Dónde está...?", "¿Está lejos de aquí?", "Gracias por su ayuda."],
        script: [
            { sender: "ai", text: "Hola, ¿en qué puedo ayudarle?" },
            { sender: "user", text: "Disculpe, ¿dónde está la estación de tren más cercana?" },
            {
                sender: "ai",
                text: "Está a dos calles de aquí, gire a la derecha en la plaza.",
                pronunciationNote: "Good! Remember \"estación\" has stress on the last syllable: es-ta-CIÓN.",
            },
            { sender: "user", text: "¿Está lejos de aquí caminando?" },
        ],
    },
];

const START_EXCHANGE_COUNT = 2;

function buildInitialState(topic){
    const messages = topic.script.slice(0, START_EXCHANGE_COUNT + 1);
    const nextEntry = topic.script[START_EXCHANGE_COUNT + 1];
    return {
        messages,
        suggestedResponse: nextEntry?.sender === "user" ? nextEntry.text : null,
        scriptIndex: START_EXCHANGE_COUNT + 1,
    };
}

const INITIAL_SCORES = { fluency: 74, accuracy: 82, intonation: 61, rhythm: 68 };

function randomScore(base){
    const delta = Math.round((Math.random() - 0.5) * 16);
    return Math.min(97, Math.max(45, base + delta));
}

function SpeakingPage(){
    const [topicIndex, setTopicIndex] = useState(0);
    const topic = MOCK_TOPICS[topicIndex];

    const [{ messages, suggestedResponse }, setConversation] = useState(() => buildInitialState(topic));
    const [exchangeCount, setExchangeCount] = useState(START_EXCHANGE_COUNT);
    const [scores, setScores] = useState(INITIAL_SCORES);
    const [isRecording, setIsRecording] = useState(false);
    const [lastPlayed, setLastPlayed] = useState(null);
    const [sessionEnded, setSessionEnded] = useState(false);

    const avgAccuracy = Math.round((scores.fluency + scores.accuracy + scores.intonation + scores.rhythm) / 4);

    const logAnswer = (isCorrect) => {
        client.post("/answerlog", {
            content_id: topic.id,
            type: "speaking",
            is_correct: isCorrect,
            time: new Date().toISOString(),
        }).catch((err) => console.error("답변 기록 전송 실패:", err));
    };

    const advanceScript = (pushUserBubble) => {
        setConversation((prev) => {
            const nextMessages = [...prev.messages];
            let index = prev.scriptIndex;

            const currentEntry = topic.script[index];
            if (currentEntry?.sender === "user"){
                if (pushUserBubble) nextMessages.push(currentEntry);
                index += 1;
            }

            const aiEntry = topic.script[index];
            if (aiEntry?.sender === "ai"){
                nextMessages.push(aiEntry);
                index += 1;
            }

            const nextEntry = topic.script[index];
            return {
                messages: nextMessages,
                suggestedResponse: nextEntry?.sender === "user" ? nextEntry.text : null,
                scriptIndex: index,
            };
        });
    };

    const handleSubmit = () => {
        if (!suggestedResponse || sessionEnded) return;

        const nextScores = {
            fluency: randomScore(INITIAL_SCORES.fluency),
            accuracy: randomScore(INITIAL_SCORES.accuracy),
            intonation: randomScore(INITIAL_SCORES.intonation),
            rhythm: randomScore(INITIAL_SCORES.rhythm),
        };
        setScores(nextScores);
        logAnswer(nextScores.accuracy >= 70);
        setExchangeCount((c) => Math.min(topic.totalExchanges, c + 1));
        setIsRecording(false);
        advanceScript(true);
    };

    const handleSkip = () => {
        if (!suggestedResponse || sessionEnded) return;
        setIsRecording(false);
        advanceScript(false);
    };

    const handleRecordToggle = () => {
        if (sessionEnded) return;
        setIsRecording((v) => !v);
    };

    const handlePlayback = () => {
        const lastUserMessage = [...messages].reverse().find((m) => m.sender === "user");
        setLastPlayed(lastUserMessage?.text ?? null);
    };

    const handleChangeTopic = () => {
        const nextIndex = (topicIndex + 1) % MOCK_TOPICS.length;
        const nextTopic = MOCK_TOPICS[nextIndex];
        setTopicIndex(nextIndex);
        setConversation(buildInitialState(nextTopic));
        setExchangeCount(START_EXCHANGE_COUNT);
        setScores(INITIAL_SCORES);
        setIsRecording(false);
        setLastPlayed(null);
        setSessionEnded(false);
    };

    const handleEndSession = () => {
        setSessionEnded(true);
        setIsRecording(false);
    };

    return (
        <div className={styles.page}>
            <div className={styles.header}>
                <div>
                    <h1 className={styles.title}>Speaking Practice</h1>
                    <p className={styles.subtitle}>
                        {sessionEnded ? "세션이 종료되었습니다" : `AI Conversation Partner · Topic: ${topic.title}`}
                    </p>
                </div>
                <div className={styles.headerActions}>
                    <button className={styles.secondaryButton} onClick={handleChangeTopic}>
                        Change Topic
                    </button>
                    <button className={styles.secondaryButton} onClick={handleEndSession} disabled={sessionEnded}>
                        End Session
                    </button>
                </div>
            </div>

            <div className={styles.body}>
                <div className={styles.main}>
                    <div className={styles.conversationCard}>
                        <p className={styles.cardTitle}>CONVERSATION</p>

                        <ul className={styles.messageList}>
                            {messages.map((m, i) => (
                                <li
                                    key={i}
                                    className={m.sender === "user" ? `${styles.messageRow} ${styles.messageRowUser}` : styles.messageRow}
                                >
                                    <div className={m.sender === "user" ? `${styles.bubble} ${styles.bubbleUser}` : styles.bubble}>
                                        <p className={styles.bubbleText}>{m.text}</p>
                                        {m.pronunciationNote && (
                                            <div className={styles.pronunciationNote}>
                                                <p className={styles.pronunciationLabel}>PRONUNCIATION NOTE</p>
                                                <p className={styles.pronunciationText}>{m.pronunciationNote}</p>
                                            </div>
                                        )}
                                        <p className={styles.bubbleMeta}>{m.sender === "user" ? "You" : "AI Tutor"}</p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className={styles.responseCard}>
                        {suggestedResponse && !sessionEnded ? (
                            <>
                                <p className={styles.cardTitle}>SUGGESTED RESPONSE</p>
                                <p className={styles.suggestedText}>&ldquo;{suggestedResponse}&rdquo;</p>
                            </>
                        ) : (
                            <p className={styles.placeholder}>
                                {sessionEnded ? "세션을 다시 시작하려면 Change Topic을 눌러주세요." : "대화를 모두 마쳤습니다. 수고하셨어요!"}
                            </p>
                        )}

                        {lastPlayed && (
                            <p className={styles.playbackHint}>▶ 재생: {lastPlayed}</p>
                        )}

                        <div className={styles.actions}>
                            <button
                                className={isRecording ? `${styles.recordButton} ${styles.recordButtonActive}` : styles.recordButton}
                                onClick={handleRecordToggle}
                                disabled={!suggestedResponse || sessionEnded}
                            >
                                ● {isRecording ? "Recording..." : "Record Answer"}
                            </button>
                            <button className={styles.secondaryButton} onClick={handlePlayback} disabled={sessionEnded}>
                                Playback Last
                            </button>
                            <button
                                className={styles.primaryButton}
                                onClick={handleSubmit}
                                disabled={!suggestedResponse || sessionEnded}
                            >
                                Submit &amp; Get Feedback
                            </button>
                            <button
                                className={styles.secondaryButton}
                                onClick={handleSkip}
                                disabled={!suggestedResponse || sessionEnded}
                            >
                                Skip
                            </button>
                        </div>
                    </div>
                </div>

                <div className={styles.sidebar}>
                    <div className={styles.sideCard}>
                        <p className={styles.sidebarTitle}>Session Info</p>
                        <div className={styles.infoRow}>
                            <span>Topic</span>
                            <span className={styles.infoValue}>{topic.title}</span>
                        </div>
                        <div className={styles.infoRow}>
                            <span>Difficulty</span>
                            <span className={styles.infoValue}>{topic.difficulty}</span>
                        </div>
                        <div className={styles.infoRow}>
                            <span>Exchanges</span>
                            <span className={styles.infoValue}>{exchangeCount} / {topic.totalExchanges}</span>
                        </div>
                        <div className={styles.infoRow}>
                            <span>Avg. Accuracy</span>
                            <span className={styles.infoValue}>{avgAccuracy}%</span>
                        </div>
                    </div>

                    <div className={styles.sideCard}>
                        <p className={styles.sidebarTitle}>Pronunciation Score</p>
                        {Object.entries(scores).map(([key, value]) => (
                            <div key={key} className={styles.scoreItem}>
                                <div className={styles.scoreLabelRow}>
                                    <span className={styles.scoreLabel}>{key[0].toUpperCase() + key.slice(1)}</span>
                                    <span className={styles.scoreValue}>{value}%</span>
                                </div>
                                <div className={styles.scoreBar}>
                                    <div className={styles.scoreBarFill} style={{ width: `${value}%` }} />
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className={styles.sideCard}>
                        <p className={styles.sidebarTitle}>Useful Phrases</p>
                        <ul className={styles.phraseList}>
                            {topic.usefulPhrases.map((phrase) => (
                                <li key={phrase} className={styles.phraseItem}>{phrase}</li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SpeakingPage;
