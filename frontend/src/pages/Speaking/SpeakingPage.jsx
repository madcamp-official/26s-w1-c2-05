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

function SpeakingPage(){
    const [dialogue, setDialogue] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [interimText, setInterimText] = useState("");
    const [ended, setEnded] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [speechLocale, setSpeechLocale] = useState("en-US");
    const recognitionRef = useRef(null);
    const turnShownAt = useRef(Date.now());

    useEffect(() => {
        let ignore = false;

        client.get("/dialogue")
            .then((res) => {
                if (ignore) return;
                const data = res.data;
                if (data?.content){
                    setDialogue(data);
                    setMessages([{ sender: "ai", text: data.content, translation: data.translation }]);
                    turnShownAt.current = Date.now();
                } else {
                    setLoadError(true);
                }
            })
            .catch((err) => {
                if (ignore) return;
                console.error("회화 학습 조회 실패:", err);
                setLoadError(true);
            })
            .finally(() => {
                if (!ignore) setIsLoading(false);
            });

        getProfile()
            .then((data) => {
                if (ignore) return;
                const locale = LANGUAGE_TO_SPEECH_LOCALE[data?.current_language];
                if (locale) setSpeechLocale(locale);
            })
            .catch((err) => console.error("프로필 조회 실패:", err));

        return () => {
            ignore = true;
            recognitionRef.current?.stop();
        };
    }, []);

    const handleSubmit = () => {
        if (!input.trim() || ended || !dialogue || isSubmitting) return;

        const responseText = input.trim();
        const responseTime = (Date.now() - turnShownAt.current) / 1000;
        // 이번 응답 이전까지의 대화. 백엔드가 turn을 저장하지 않으므로, LLM이 이미 오간 내용을
        // 기억한 채 판단하도록(예: 이름을 이미 받았으면 다시 묻지 않도록) 매번 함께 보낸다.
        const history = messages.map((m) => ({ role: m.sender === "user" ? "user" : "ai", content: m.text }));
        setMessages((prev) => [...prev, { sender: "user", text: responseText }]);
        setInput("");
        setIsSubmitting(true);
        setSubmitError(false);

        client.post("/dialoguelog", {
            content_id: dialogue.content_id,
            flow: dialogue.flow,
            response: responseText,
            response_time: responseTime,
            time: new Date().toISOString(),
            history,
        })
            .then((res) => {
                const data = res.data;
                setMessages((prev) => {
                    const next = [...prev];
                    next[next.length - 1] = { ...next[next.length - 1], feedback: data.feedback };
                    if (data.content){
                        next.push({ sender: "ai", text: data.content, translation: data.translation });
                    }
                    return next;
                });
                setDialogue(data);
                turnShownAt.current = Date.now();
                if (data.end) setEnded(true);
            })
            .catch((err) => {
                console.error("회화 응답 전송 실패:", err);
                setSubmitError(true);
                // 실패한 응답은 되돌려서 사용자가 다시 입력해 재전송할 수 있게 한다.
                setMessages((prev) => prev.slice(0, -1));
                setInput(responseText);
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

    if (isLoading){
        return (
            <div className={styles.page}>
                <PageHeader title="Speaking Practice" subtitle="대화를 불러오는 중입니다..." />
            </div>
        );
    }

    if (loadError || !dialogue){
        return (
            <div className={styles.page}>
                <PageHeader title="Speaking Practice" subtitle="회화 콘텐츠를 불러오지 못했습니다" />
                <p className={styles.placeholder}>잠시 후 다시 시도해주세요.</p>
            </div>
        );
    }

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
                                        {m.translation && m.translation.trim() !== m.text?.trim() && (
                                            <p className={styles.translationText}>{m.translation}</p>
                                        )}
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
                                {submitError && (
                                    <p className={styles.errorText}>
                                        전송에 실패했어요. 다시 시도해주세요.
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
