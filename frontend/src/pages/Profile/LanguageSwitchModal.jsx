import { useEffect, useState } from "react";
import { getLanguages, switchLanguage } from "../../api/user";
import { LANGUAGES } from "../Onboarding/data/languages";
import { LEVELS } from "../Onboarding/data/levels";
import { STUDY_PERIODS } from "../Onboarding/data/studyPeriods";
import styles from "./LanguageSwitchModal.module.css";

const FLAG_BY_ID = Object.fromEntries(LANGUAGES.map((l) => [l.id, l.flag]));

function LanguageSwitchModal({ onClose, onSwitched }){
    const [languages, setLanguages] = useState(null);
    const [loadError, setLoadError] = useState(false);
    // 학습 이력이 없는 언어를 고르면, 온보딩과 동일하게 레벨/목표 기간을 먼저 물어본다.
    const [newLangId, setNewLangId] = useState(null);
    const [level, setLevel] = useState(LEVELS[0].code);
    const [studyGoal, setStudyGoal] = useState(STUDY_PERIODS[0].days);
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState("");

    useEffect(() => {
        getLanguages()
            .then(setLanguages)
            .catch((err) => {
                console.error("언어 목록 조회 실패:", err);
                setLoadError(true);
            });
    }, []);

    const handleSelect = async (lang) => {
        if (lang.is_current) return;
        setSubmitError("");

        if (!lang.in_progress){
            setNewLangId(lang.lang_id);
            return;
        }

        setSubmitting(true);
        try {
            await switchLanguage({ language: lang.lang_id });
            onSwitched();
        } catch (err) {
            console.error("언어 전환 실패:", err);
            setSubmitError("언어 전환에 실패했습니다. 잠시 후 다시 시도해주세요.");
        } finally {
            setSubmitting(false);
        }
    };

    const handleStartNewLanguage = async () => {
        setSubmitting(true);
        setSubmitError("");
        try {
            await switchLanguage({ language: newLangId, level, studyGoal });
            onSwitched();
        } catch (err) {
            console.error("새 언어 시작 실패:", err);
            setSubmitError("언어 전환에 실패했습니다. 잠시 후 다시 시도해주세요.");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className={styles.overlay} onClick={onClose}>
            <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                <div className={styles.header}>
                    <h2 className={styles.title}>학습 언어 변경</h2>
                    <button className={styles.closeButton} onClick={onClose} disabled={submitting}>
                        ×
                    </button>
                </div>

                {newLangId ? (
                    <div className={styles.newLangForm}>
                        <p className={styles.newLangIntro}>
                            {FLAG_BY_ID[newLangId]} {languages.find((l) => l.lang_id === newLangId)?.language}을(를) 처음 시작해요.
                            현재 실력과 목표 기간을 알려주세요.
                        </p>

                        <p className={styles.fieldLabel}>현재 실력</p>
                        <div className={styles.levelGrid}>
                            {LEVELS.map((lv) => (
                                <button
                                    key={lv.code}
                                    className={level === lv.code ? `${styles.levelOption} ${styles.levelOptionActive}` : styles.levelOption}
                                    onClick={() => setLevel(lv.code)}
                                    disabled={submitting}
                                >
                                    <span className={styles.levelCode}>{lv.code}</span>
                                    <span className={styles.levelText}>{lv.label}</span>
                                </button>
                            ))}
                        </div>

                        <p className={styles.fieldLabel}>목표 기간</p>
                        <div className={styles.goalRow}>
                            {STUDY_PERIODS.map((period) => (
                                <button
                                    key={period.days}
                                    className={studyGoal === period.days ? `${styles.goalOption} ${styles.goalOptionActive}` : styles.goalOption}
                                    onClick={() => setStudyGoal(period.days)}
                                    disabled={submitting}
                                >
                                    {period.label}
                                </button>
                            ))}
                        </div>

                        {submitError && <p className={styles.errorText}>{submitError}</p>}

                        <div className={styles.formActions}>
                            <button className={styles.secondaryButton} onClick={() => setNewLangId(null)} disabled={submitting}>
                                ← 목록으로
                            </button>
                            <button className={styles.primaryButton} onClick={handleStartNewLanguage} disabled={submitting}>
                                {submitting ? "전환 중..." : "이 언어로 시작하기"}
                            </button>
                        </div>
                    </div>
                ) : (
                    <>
                        {loadError && <p className={styles.errorText}>언어 목록을 불러오지 못했습니다.</p>}
                        {submitError && <p className={styles.errorText}>{submitError}</p>}
                        <ul className={styles.langList}>
                            {(languages ?? []).map((lang) => (
                                <li key={lang.lang_id}>
                                    <button
                                        className={lang.is_current ? `${styles.langItem} ${styles.langItemCurrent}` : styles.langItem}
                                        onClick={() => handleSelect(lang)}
                                        disabled={submitting || lang.is_current}
                                    >
                                        <span className={styles.langFlag}>{FLAG_BY_ID[lang.lang_id]}</span>
                                        <span className={styles.langName}>{lang.language}</span>
                                        {lang.is_current && <span className={styles.langTag}>현재 학습 중</span>}
                                        {!lang.is_current && lang.in_progress && (
                                            <span className={styles.langMeta}>Lv.{lang.current_level} · {lang.studied_days}일 학습</span>
                                        )}
                                        {!lang.in_progress && <span className={styles.langMeta}>새로 시작</span>}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </>
                )}
            </div>
        </div>
    );
};

export default LanguageSwitchModal;
