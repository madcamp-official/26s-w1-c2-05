import axios from "axios";

const client = axios.create();

client.interceptors.request.use((config) => {
    const accessToken = localStorage.getItem("accessToken") ?? sessionStorage.getItem("accessToken");
    if (accessToken){
        config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
});

// accessToken이 저장된 쪽(localStorage/sessionStorage)을 그대로 따라가서
// 로그인 유지 여부(rememberMe)에 맞춰 다른 사용자 상태도 같이 저장/삭제되게 한다.
export function getAuthStorage() {
    return localStorage.getItem("accessToken") ? localStorage : sessionStorage;
}

export default client;
