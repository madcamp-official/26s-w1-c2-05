import { getAuthStorage } from "./client";

const CURRENT_LEARNING_ID_KEY = "current_learning_id";

// TODO(backend): 연동되면 아래 mock 대신 실제 호출로 교체
// import client from "./client";
// export async function getCurrentUser() {
//   const res = await client.get("/users/me");
//   return res.data; // { current_learning_id, ... }
// }
export async function getCurrentUser() {
    const current_learning_id = getAuthStorage().getItem(CURRENT_LEARNING_ID_KEY) ?? null;
    return { current_learning_id };
}

// TODO(backend): 온보딩 완료 응답에 current_learning_id가 내려오면 그 값으로 교체
export function setCurrentLearningId(id) {
    getAuthStorage().setItem(CURRENT_LEARNING_ID_KEY, id);
}
