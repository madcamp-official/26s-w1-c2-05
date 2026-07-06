import styles from "../onboarding.module.css";

const STEP_LABELS = ["언어 선택", "현재 실력", "학습 목표"];

function StepIndicator({ currentStep }) {
  return (
    <div className={styles.stepIndicator}>
      {STEP_LABELS.map((label, index) => {
        const step = index + 1;
        return (
          <div className={styles.stepIndicatorItem} key={label}>
            <div
              className={[
                styles.circle,
                step === currentStep && styles.circleActive,
                step < currentStep && styles.circleDone,
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {step}
            </div>
            <span className={styles.stepLabel}>{label}</span>
            {step < STEP_LABELS.length && <div className={styles.stepLine} />}
          </div>
        );
      })}
    </div>
  );
}

export default StepIndicator;
