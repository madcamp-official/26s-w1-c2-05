import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./Auth.css";

function Signup(){
    const [id, setId] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [pwRepeat, setPwRepeat] = useState("");
    const navigate = useNavigate();

    const handleSignup = async ()=>{
        if (!id || !email || !password || !pwRepeat){
            alert("모든 항목을 입력해주세요.");
            return;
        }

        if (password !== pwRepeat){
            alert("비밀번호가 일치하지 않습니다.");
            return;
        }

        try {
            const res = await axios.post("/auth/signup", {
                id,
                email,
                password,
                pw_repeat: pwRepeat,
            });
            const { accessToken, refreshToken, isOnboardingComplete } = res.data;

            localStorage.setItem("accessToken", accessToken);
            localStorage.setItem("refreshToken", refreshToken);

            navigate(isOnboardingComplete ? "/dashboard" : "/onboarding");
        } catch (err) {
            alert(err.response?.data?.message ?? "회원가입에 실패했습니다.");
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-form-side">
                <p className="auth-logo">[서비스 이름]</p>
                <p className="auth-tagline">Language Learning</p>

                <h1 className="auth-title">회원가입</h1>

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
                    <label>이메일</label>
                    <input
                        type="text"
                        placeholder="user@email.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
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

                <div className="auth-field">
                    <label>비밀번호 확인</label>
                    <input
                        type="password"
                        placeholder="비밀번호를 다시 입력하세요"
                        value={pwRepeat}
                        onChange={(e) => setPwRepeat(e.target.value)}
                    />
                </div>

                <button className="auth-submit" onClick={handleSignup}>회원가입</button>

                <p className="auth-switch">
                    이미 계정이 있으신가요? <a>로그인</a>
                </p>
            </div>
        </div>
    );
};

export default Signup;
