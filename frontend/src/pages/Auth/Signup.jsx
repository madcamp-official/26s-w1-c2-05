import { useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../../api/client";
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

        if (password.length < 8 || !/[0-9]/.test(password) || !/[a-zA-Z]/.test(password)){
            alert("비밀번호는 숫자와 문자로 구성되고 8자리 이상이어야 합니다.");
            return;
        }

        try {
            await client.post("/auth/signup", {
                username: id,
                email,
                password,
                pw_repeat: pwRepeat,
            });

            alert("회원가입이 완료되었습니다. 로그인해주세요.");
            navigate("/login");
        } catch (err) {
            console.error("회원가입 실패:", err.response?.data);
            const detail = err.response?.data?.detail;
            const message = Array.isArray(detail)
                ? detail.map((d) => d.msg).join("\n")
                : detail ?? "회원가입에 실패했습니다.";
            alert(message);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-form-side">
                <p className="auth-logo">LinguaAI</p>
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
                    이미 계정이 있으신가요? <a href="/login">로그인</a>
                </p>
            </div>
        </div>
    );
};

export default Signup;
