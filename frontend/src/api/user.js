import client, { getAuthStorage } from "./client";

const CURRENT_LEARNING_ID_KEY = "current_learning_id";

// 로그인 응답의 SurveyCompleted로 매번 갱신되는 온보딩 완료 캐시.
export async function getCurrentUser() {
    const current_learning_id = getAuthStorage().getItem(CURRENT_LEARNING_ID_KEY) ?? null;
    return { current_learning_id };
}

// falsy를 넘기면 캐시를 지운다 (문자열 "false"로 저장하면 항상 truthy가 되는 버그 방지).
export function setCurrentLearningId(completed) {
    const storage = getAuthStorage();
    if (completed) {
        storage.setItem(CURRENT_LEARNING_ID_KEY, "true");
    } else {
        storage.removeItem(CURRENT_LEARNING_ID_KEY);
    }
}

export async function getProfile() {
    const res = await client.get("/users/me");
    return res.data;
}

export async function logout() {
    const storage = getAuthStorage();
    const refreshToken = storage.getItem("refreshToken");

    if (refreshToken) {
        await client.post("/auth/logout", { refresh_token: refreshToken })
            .catch((err) => console.error("로그아웃 요청 실패:", err));
    }

    storage.removeItem("accessToken");
    storage.removeItem("refreshToken");
    storage.removeItem(CURRENT_LEARNING_ID_KEY);
}
