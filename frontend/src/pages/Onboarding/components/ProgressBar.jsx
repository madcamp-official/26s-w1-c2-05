import styles from "../onboarding.module.css";

function ProgressBar({ currentStep, totalSteps }) {
  const percent = (currentStep / totalSteps) * 100;

  return (
    <div className={styles.progressBar}>
      <div className={styles.progressBarFill} style={{ width: `${percent}%` }} />
    </div>
  );
}

export default ProgressBar;
