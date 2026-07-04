import { STUDY_PERIODS } from "../data/studyPeriods";
import styles from "../onboarding.module.css";

function GoalStep({ selectedDays, onSelect, onBack, onComplete, isSubmitting, errorMessage }) {
  return (
    <div>
      <h1 className={styles.stepTitle}>학습 목표를 설정해주세요</h1>
      <p className={styles.stepSubtitle}>일정에 맞춘 맞춤 학습 계획을 세워드릴게요.</p>

      <label className={styles.fieldLabel} htmlFor="study-period">
        목표 학습 기간
      </label>
      <select
        id="study-period"
        className={styles.select}
        value={selectedDays ?? ""}
        onChange={(e) => onSelect(Number(e.target.value))}
      >
        <option value="" disabled>
          선택해주세요
        </option>
        {STUDY_PERIODS.map((period) => (
          <option key={period.days} value={period.days}>
            {period.label}
          </option>
        ))}
      </select>

      {errorMessage && <p className={styles.errorText}>{errorMessage}</p>}

      <div className={styles.actions}>
        <button type="button" className={styles.backButton} onClick={onBack} disabled={isSubmitting}>
          이전
        </button>
        <button
          type="button"
          className={styles.nextButton}
          disabled={selectedDays == null || isSubmitting}
          onClick={onComplete}
        >
          {isSubmitting ? "처리 중..." : "학습 시작하기"}
        </button>
      </div>
    </div>
  );
}

export default GoalStep;
