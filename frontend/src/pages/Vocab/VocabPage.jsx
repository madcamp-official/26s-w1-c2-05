import { useEffect, useState } from "react";
import client from "../../api/client";
import styles from "./VocabPage.module.css";

const MOCK_VOCABULARIES = [
    { number: 1, word: "careless", meaning: "경솔한", example: "Careless people need to think twice before they move on." },
    { number: 2, word: "restaurant", meaning: "식당", example: "We booked a table at the restaurant." },
    { number: 3, word: "order", meaning: "주문하다", example: "I'd like to order the pasta, please." },
];

function VocabPage(){
    const [vocabularies, setVocabularies] = useState(MOCK_VOCABULARIES);

    useEffect(() => {
        client.get("/vocabulary", { params: { category: "voca" } })
            .then((res) => {
                if (Array.isArray(res.data?.vocabularies)){
                    setVocabularies(res.data.vocabularies);
                }
            })
            .catch((err) => console.error("단어장 조회 실패:", err));
    }, []);

    return (
        <div className={styles.page}>
            <h1 className={styles.title}>단어 학습</h1>

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
