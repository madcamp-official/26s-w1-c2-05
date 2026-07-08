import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../../api/client";
import styles from "./VocabPage.module.css";

function VocabPage(){
    const navigate = useNavigate();
    const [vocabularies, setVocabularies] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);

    useEffect(() => {
        client.get("/vocabulary", { params: { category: "voca" } })
            .then((res) => {
                if (Array.isArray(res.data?.vocabularies)){
                    setVocabularies(res.data.vocabularies);
                }
            })
            .catch((err) => {
                console.error("단어장 조회 실패:", err);
                setLoadError(true);
            })
            .finally(() => setIsLoading(false));
    }, []);

    if (isLoading){
        return <div className={styles.page}>단어장을 불러오는 중입니다...</div>;
    }

    if (loadError){
        return <div className={styles.page}>단어장을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.</div>;
    }

    return (
        <div className={styles.page}>
            <div className={styles.header}>
                <h1 className={styles.title}>단어 학습</h1>
                <button className={styles.flashcardButton} onClick={() => navigate("/flashcard")}>
                    플래시카드로 학습하기
                </button>
            </div>

            <ul className={styles.wordList}>
                {vocabularies.map((v) => (
                    <li key={v.number} className={styles.wordItem}>
                        <span className={styles.wordNumber}>{v.number}</span>
                        <div className={styles.wordBody}>
                            <p className={styles.word}>{v.word}</p>
                            <p className={styles.meaning}>{v.meaning}</p>
                            <p className={styles.example}>{v.example}</p>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default VocabPage;
