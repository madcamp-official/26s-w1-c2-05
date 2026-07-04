import { useMemo, useState } from "react";
import { LANGUAGES, FEATURED_LANGUAGE_IDS } from "../data/languages";
import styles from "../onboarding.module.css";

function LanguageSelectStep({ selectedLanguageId, onSelect, onNext }) {
  const [query, setQuery] = useState("");

  const featuredLanguages = useMemo(
    () => FEATURED_LANGUAGE_IDS.map((id) => LANGUAGES.find((lang) => lang.id === id)),
    []
  );
  const searchResults = useMemo(() => {
    const trimmed = query.trim().toLowerCase();
    if (!trimmed) return [];
    return LANGUAGES.filter((lang) => lang.name.toLowerCase().includes(trimmed));
  }, [query]);

  const gridLanguages = query.trim() ? searchResults : featuredLanguages;

  return (
    <div>
      <h1 className={styles.stepTitle}>어떤 언어를 배우고 싶으신가요?</h1>
      <p className={styles.stepSubtitle}>시작하려는 언어를 선택해주세요</p>

      <div className={styles.languageGrid}>
        {gridLanguages.map((lang) => (
          <button
            key={lang.id}
            type="button"
            className={[styles.languageCard, selectedLanguageId === lang.id && styles.languageCardSelected]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onSelect(lang.id)}
          >
            <span className={styles.languageFlag}>{lang.flag}</span>
            <span className={styles.languageName}>{lang.name}</span>
          </button>
        ))}
        {query.trim() && gridLanguages.length === 0 && (
          <p className={styles.languageGridEmpty}>"{query}"와(과) 일치하는 언어가 없습니다</p>
        )}
      </div>

      <button
        type="button"
        className={styles.nextButton}
        disabled={selectedLanguageId == null}
        onClick={onNext}
      >
        다음
      </button>
    </div>
  );
}

export default LanguageSelectStep;
