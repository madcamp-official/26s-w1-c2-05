import { getAuthStorage } from "./client";

const CURRENT_LEARNING_ID_KEY = "current_learning_id";

// 로그인 응답에 current_learning_id가 없어서, 온보딩 완료 여부를 이 브라우저의
// 로컬 캐시로만 판단한다. 다른 기기/캐시 삭제 시엔 다시 온보딩이 뜰 수 있음.
export async function getCurrentUser() {
    const current_learning_id = getAuthStorage().getItem(CURRENT_LEARNING_ID_KEY) ?? null;
    return { current_learning_id };
}

export function setCurrentLearningId(id) {
    getAuthStorage().setItem(CURRENT_LEARNING_ID_KEY, id);
}
