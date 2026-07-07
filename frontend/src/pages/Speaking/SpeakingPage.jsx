import { useEffect, useRef, useState } from "react";
import client from "../../api/client";
import { getProfile } from "../../api/user";
import PageHeader from "../../components/PageHeader";
import styles from "./SpeakingPage.module.css";

const LANGUAGE_TO_SPEECH_LOCALE = {
    English: "en-US",
    Japanese: "ja-JP",
    Chinese: "zh-CN",
    Spanish: "es-ES",
    French: "fr-FR",
    German: "de-DE",
    Italian: "it-IT",
    Vietnamese: "vi-VN",
};

const SpeechRecognitionClass =
    typeof window !== "undefined" ? window.SpeechRecognition || window.webkitSpeechRecognition : null;

// 백엔드 /dialogue, /dialoguelog가 아직 없을 때 화면 확인용으로 쓰는 목업 대화 흐름.
const MOCK_TURNS = [
    { content_id: 4321, subject: "Restaurant", flow: "greeting", content: "Welcome to our restaurant. Have you made a reservation?" },
    { content_id: 4321, subject: "Restaurant", flow: "ordering", content: "Ok, I checked your name. Now, what can I get for you?", feedback: "의미는 통하지만 목적어가 빠졌습니다." },
    { content_id: 4321, subject: "Restaurant", flow: "recommendation", content: "Great choice! Would you like a drink with that?", feedback: "좋아요, 자연스러운 문장이었어요." },
    { content_id: 4321, subject: "Restaurant", flow: "closing", content: "Perfect. Your order will be ready shortly. Enjoy your meal!", feedback: "완벽한 문장이에요.", end: true },
];

function SpeakingPage(){
    const [dialogue, setDialogue] = useState(MOCK_TURNS[0]);
    const [messages, setMessages] = useState([{ sender: "ai", text: MOCK_TURNS[0].content }]);
    const [input, setInput] = useState("");
    const [interimText, setInterimText] = useState("");
    const [ended, setEnded] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [speechLocale, setSpeechLocale] = useState("en-US");
    const recognitionRef = useRef(null);
    const mockStepRef = useRef(0);

    useEffect(() => {
        client.get("/dialogue")
            .then((res) => {
                const data = res.data;
                if (data?.content){
                    setDialogue(data);
                    setMessages([{ sender: "ai", text: data.content }]);
                }
            })
            .catch((err) => console.error("회화 학습 조회 실패:", err));

        getProfile()
            .then((data) => {
                const locale = LANGUAGE_TO_SPEECH_LOCALE[data?.current_language];
                if (locale) setSpeechLocale(locale);
            })
            .catch((err) => console.error("프로필 조회 실패:", err));

        return () => {
            recognitionRef.current?.stop();
        };
    }, []);

    const handleSubmit = () => {
        if (!input.trim() || ended || !dialogue || isSubmitting) return;

        const responseText = input.trim();
        setMessages((prev) => [...prev, { sender: "user", text: responseText }]);
        setInput("");
        setIsSubmitting(true);

        client.post("/dialoguelog", {
            content_id: dialogue.content_id,
            flow: dialogue.flow,
            response: responseText,
        })
            .then((res) => {
                const data = res.data;
                setMessages((prev) => {
                    const next = [...prev];
                    next[next.length - 1] = { ...next[next.length - 1], feedback: data.feedback };
                    if (data.content){
                        next.push({ sender: "ai", text: data.content });
                    }
                    return next;
                });
                setDialogue(data);
                if (data.end) setEnded(true);
            })
            .catch((err) => {
                console.error("회화 응답 전송 실패, 목업 대화로 대체:", err);
                mockStepRef.current = Math.min(mockStepRef.current + 1, MOCK_TURNS.length - 1);
                const nextTurn = MOCK_TURNS[mockStepRef.current];
                setMessages((prev) => {
                    const next = [...prev];
                    next[next.length - 1] = { ...next[next.length - 1], feedback: nextTurn.feedback };
                    next.push({ sender: "ai", text: nextTurn.content });
                    return next;
                });
                setDialogue(nextTurn);
                if (nextTurn.end) setEnded(true);
            })
            .finally(() => setIsSubmitting(false));
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey){
            e.preventDefault();
            handleSubmit();
        }
    };

    const handleToggleRecording = () => {
        if (!SpeechRecognitionClass || ended || isSubmitting) return;

        if (isRecording){
            recognitionRef.current?.stop();
            return;
        }

        const recognition = new SpeechRecognitionClass();
        recognition.lang = speechLocale;
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onresult = (event) => {
            let finalTranscript = "";
            let interim = "";
            for (let i = event.resultIndex; i < event.results.length; i++){
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal){
                    finalTranscript += transcript;
                } else {
                    interim += transcript;
                }
            }
            if (finalTranscript.trim()){
                setInput((prev) => (prev ? `${prev} ${finalTranscript.trim()}` : finalTranscript.trim()));
            }
            setInterimText(interim);
        };

        recognition.onerror = (event) => {
            console.error("음성 인식 오류:", event.error);
            setIsRecording(false);
            setInterimText("");
        };

        recognition.onend = () => {
            setIsRecording(false);
            setInterimText("");
        };

        recognitionRef.current = recognition;
        recognition.start();
        setIsRecording(true);
    };

    const turnCount = messages.filter((m) => m.sender === "user").length;

    return (
        <div className={styles.page}>
            <PageHeader
                title="Speaking Practice"
                subtitle={ended ? "대화가 종료되었습니다" : `Topic: ${dialogue.subject} · ${dialogue.flow}`}
            />

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
                                        {m.feedback && (
                                            <div className={styles.pronunciationNote}>
                                                <p className={styles.pronunciationLabel}>FEEDBACK</p>
                                                <p className={styles.pronunciationText}>{m.feedback}</p>
                                            </div>
                                        )}
                                        <p className={styles.bubbleMeta}>{m.sender === "user" ? "You" : "AI Tutor"}</p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className={styles.responseCard}>
                        {ended ? (
                            <p className={styles.placeholder}>대화를 모두 마쳤습니다. 수고하셨어요!</p>
                        ) : (
                            <>
                                <p className={styles.cardTitle}>YOUR RESPONSE</p>
                                <textarea
                                    className={styles.responseInput}
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder={SpeechRecognitionClass ? "마이크를 누르고 말해보세요, 또는 직접 입력하세요..." : "영어로 답해보세요..."}
                                    rows={3}
                                    disabled={isSubmitting}
                                />
                                {isRecording && (
                                    <p className={styles.interimHint}>
                                        듣고 있어요{interimText ? `: ${interimText}` : "..."}
                                    </p>
                                )}
                                {!SpeechRecognitionClass && (
                                    <p className={styles.interimHint}>
                                        이 브라우저는 음성 인식을 지원하지 않아요. 텍스트로 입력해주세요.
                                    </p>
                                )}
                                <div className={styles.actions}>
                                    {SpeechRecognitionClass && (
                                        <button
                                            className={isRecording ? `${styles.recordButton} ${styles.recordButtonActive}` : styles.recordButton}
                                            onClick={handleToggleRecording}
                                            disabled={isSubmitting}
                                        >
                                            ● {isRecording ? "Stop" : "Record"}
                                        </button>
                                    )}
                                    <button
                                        className={styles.primaryButton}
                                        onClick={handleSubmit}
                                        disabled={!input.trim() || isSubmitting}
                                    >
                                        전송
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                <div className={styles.sidebar}>
                    <div className={styles.sideCard}>
                        <p className={styles.sidebarTitle}>Session Info</p>
                        <div className={styles.infoRow}>
                            <span>Subject</span>
                            <span className={styles.infoValue}>{dialogue.subject}</span>
                        </div>
                        <div className={styles.infoRow}>
                            <span>Flow</span>
                            <span className={styles.infoValue}>{dialogue.flow}</span>
                        </div>
                        <div className={styles.infoRow}>
                            <span>Turns</span>
                            <span className={styles.infoValue}>{turnCount}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SpeakingPage;
