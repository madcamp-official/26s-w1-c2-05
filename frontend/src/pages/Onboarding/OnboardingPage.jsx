import { useState } from "react";
import ProgressBar from "./components/ProgressBar";
import StepIndicator from "./components/StepIndicator";
import LanguageSelectStep from "./steps/LanguageSelectStep";
import ProficiencyStep from "./steps/ProficiencyStep";
import GoalStep from "./steps/GoalStep";
import { LANGUAGES } from "./data/languages";
import { submitOnboarding } from "./api/onboarding";
import styles from "./onboarding.module.css";

const TOTAL_STEPS = 3;

function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [answers, setAnswers] = useState({
    language: null,
    level: null,
    studyGoal: null,
  });
  const [submitStatus, setSubmitStatus] = useState("idle"); // "idle" | "submitting" | "error"
  const [submitError, setSubmitError] = useState(null);

  const goToNextStep = () => setStep((s) => Math.min(s + 1, TOTAL_STEPS));
  const goToPrevStep = () => setStep((s) => Math.max(s - 1, 1));

  const handleComplete = async () => {
    setSubmitStatus("submitting");
    setSubmitError(null);
    try {
      await submitOnboarding(answers);
      setSubmitStatus("idle");
      // TODO: 라우터 연결되면 메인 화면으로 이동
    } catch (err) {
      setSubmitStatus("error");
      setSubmitError(err.message);
    }
  };

  const selectedLanguageName = LANGUAGES.find((lang) => lang.id === answers.language)?.name ?? "";

  return (
    <div className={styles.page}>
      <ProgressBar currentStep={step} totalSteps={TOTAL_STEPS} />
      <StepIndicator currentStep={step} />

      {step === 1 && (
        <LanguageSelectStep
          selectedLanguageId={answers.language}
          onSelect={(language) => setAnswers((a) => ({ ...a, language }))}
          onNext={goToNextStep}
        />
      )}
      {step === 2 && (
        <ProficiencyStep
          languageName={selectedLanguageName}
          selectedLevel={answers.level}
          onSelect={(level) => setAnswers((a) => ({ ...a, level }))}
          onNext={goToNextStep}
          onBack={goToPrevStep}
        />
      )}
      {step === 3 && (
        <GoalStep
          selectedDays={answers.studyGoal}
          onSelect={(studyGoal) => setAnswers((a) => ({ ...a, studyGoal }))}
          onBack={goToPrevStep}
          onComplete={handleComplete}
          isSubmitting={submitStatus === "submitting"}
          errorMessage={submitStatus === "error" ? submitError : null}
        />
      )}
    </div>
  );
}

export default OnboardingPage;
