import client from "../../../api/client";

export async function submitOnboarding({ language, level, studyGoal }) {
  const res = await client.post("/onboarding", {
    language,
    level,
    StudyGoal: studyGoal,
  });
  return res.data;
}
