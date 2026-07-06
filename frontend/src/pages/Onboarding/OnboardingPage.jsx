import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ProgressBar from "./components/ProgressBar";
import StepIndicator from "./components/StepIndicator";
import LanguageSelectStep from "./steps/LanguageSelectStep";
import ProficiencyStep from "./steps/ProficiencyStep";
import GoalStep from "./steps/GoalStep";
import { LANGUAGES } from "./data/languages";
import { submitOnboarding } from "./api/onboarding";
import { setCurrentLearningId } from "../../api/user";
import styles from "./onboarding.module.css";

const TOTAL_STEPS = 3;

function OnboardingPage() {
  const navigate = useNavigate();
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
      // 온보딩 응답엔 실제 learning_id가 안 내려오므로, 완료 여부만 로컬에 표시해둔다.
      setCurrentLearningId(true);
      setSubmitStatus("idle");
      navigate("/vocab");
    } catch (err) {
      setSubmitStatus("error");
      const detail = err.response?.data?.detail;
      setSubmitError(typeof detail === "string" ? detail : "온보딩 제출에 실패했습니다.");
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
