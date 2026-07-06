export function submitOnboarding({ language, level, studyGoal }) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        message: "다 되었습니다! 이제 메인화면으로 이동합니다.",
        userInfo: { userID: "MADCAMP123", DailyStreak: 0 },
      });
    }, 800);
  });
}
