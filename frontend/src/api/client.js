import axios from "axios";

const client = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || ''
}
);

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

function clearAuthState() {
    for (const storage of [localStorage, sessionStorage]) {
        storage.removeItem("accessToken");
        storage.removeItem("refreshToken");
        storage.removeItem("current_learning_id");
    }
}

// 동시에 여러 요청이 401을 받아도 /auth/refresh는 한 번만 호출되도록 진행 중인 요청을 공유한다.
let refreshPromise = null;

function refreshAccessToken(refreshToken) {
    if (!refreshPromise) {
        // 인터셉터가 걸린 client가 아니라 axios를 그대로 써서 재귀 호출을 피한다.
        refreshPromise = axios
            .post("/auth/refresh", { refresh_token: refreshToken })
            .then((res) => res.data.access_token)
            .finally(() => {
                refreshPromise = null;
            });
    }
    return refreshPromise;
}

client.interceptors.response.use(
    (res) => res,
    async (error) => {
        const { config, response } = error;
        const isAuthEndpoint = config?.url?.startsWith("/auth/");

        if (response?.status !== 401 || isAuthEndpoint || config._retry) {
            return Promise.reject(error);
        }

        const storage = getAuthStorage();
        const refreshToken = storage.getItem("refreshToken");
        if (!refreshToken) {
            clearAuthState();
            window.location.href = "/login";
            return Promise.reject(error);
        }

        config._retry = true;
        try {
            const accessToken = await refreshAccessToken(refreshToken);
            storage.setItem("accessToken", accessToken);
            config.headers.Authorization = `Bearer ${accessToken}`;
            return client(config);
        } catch (refreshError) {
            clearAuthState();
            window.location.href = "/login";
            return Promise.reject(refreshError);
        }
    }
);

export default client;
