import axios from "axios";

const client = axios.create();

client.interceptors.request.use((config) => {
    const accessToken = localStorage.getItem("accessToken") ?? sessionStorage.getItem("accessToken");
    if (accessToken){
        config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
});

export default client;
