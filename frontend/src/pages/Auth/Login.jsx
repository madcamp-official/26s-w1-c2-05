import { useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../../api/client";
import { getCurrentUser } from "../../api/user";
import "./Auth.css";

function Login(){
    const [id, setId] = useState("");
    const [password, setPassword] = useState("");
    const [rememberMe, setRememberMe] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async ()=>{
        if (!id || !password){
            alert("아이디와 비밀번호를 입력해주세요.");
            return;
        }

        try {
            const res = await client.post("/auth/login", { id, password });
            const { access_token, refresh_token } = res.data;

            const storage = rememberMe ? localStorage : sessionStorage;
            storage.setItem("accessToken", access_token);
            storage.setItem("refreshToken", refresh_token);

            const { current_learning_id } = await getCurrentUser();
            navigate(current_learning_id ? "/vocab" : "/onboarding");
        } catch (err) {
            const detail = err.response?.data?.detail;
            alert(typeof detail === "string" ? detail : "로그인에 실패했습니다.");
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-form-side">
                <p className="auth-logo">[서비스 이름]</p>
                <p className="auth-tagline">Language Learning</p>

                <h1 className="auth-title">로그인</h1>

                <div className="auth-field">
                    <label>아이디</label>
                    <input
                        type="text"
                        placeholder="아이디를 입력하세요"
                        value={id}
                        onChange={(e) => setId(e.target.value)}
                    />
                </div>

                <div className="auth-field">
                    <label>비밀번호</label>
                    <input
                        type="password"
                        placeholder="비밀번호를 입력하세요"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>

                <div className="auth-row">
                    <label>
                        <input
                            type="checkbox"
                            checked={rememberMe}
                            onChange={(e) => setRememberMe(e.target.checked)}
                        />
                        로그인 상태 유지
                    </label>
                    <a>비밀번호를 잊으셨나요?</a>
                </div>

                <button className="auth-submit" onClick={handleLogin}>로그인</button>

                <p className="auth-switch">
                    계정이 없으신가요? <a href="/signup">회원가입</a>
                </p>
            </div>
        </div>
    );
};

export default Login;
