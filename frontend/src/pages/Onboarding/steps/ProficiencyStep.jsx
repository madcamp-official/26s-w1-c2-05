import { LEVELS } from "../data/levels";
import styles from "../onboarding.module.css";

function ProficiencyStep({ languageName, selectedLevel, onSelect, onNext, onBack }) {
  return (
    <div>
      <h1 className={styles.stepTitle}>{languageName} 실력은 어느 정도인가요?</h1>
      <p className={styles.stepSubtitle}>학습 경로를 맞춤 설정하는 데 도움이 됩니다.</p>

      <div className={styles.levelList}>
        {LEVELS.map((level) => (
          <button
            key={level.code}
            type="button"
            className={[styles.levelOption, selectedLevel === level.code && styles.levelOptionSelected]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onSelect(level.code)}
          >
            <span
              className={[styles.levelRadio, selectedLevel === level.code && styles.levelRadioChecked]
                .filter(Boolean)
                .join(" ")}
            />
            <span className={styles.levelText}>
              <span className={styles.levelTitle}>
                {level.code} — {level.label}
              </span>
              <span className={styles.levelDescription}>{level.description}</span>
            </span>
          </button>
        ))}
      </div>

      <div className={styles.actions}>
        <button type="button" className={styles.backButton} onClick={onBack}>
          이전
        </button>
        <button
          type="button"
          className={styles.nextButton}
          disabled={selectedLevel == null}
          onClick={onNext}
        >
          다음
        </button>
      </div>
    </div>
  );
}

export default ProficiencyStep;
