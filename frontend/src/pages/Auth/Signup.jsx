import { useState } from "react";
import axios from "axios";

function Signup(){
    const [id, setId] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [pwRepeat, setPwRepeat] = useState("");

    const handleSignup = ()=>{
        if (!id || !email || !password || !pwRepeat){
            alert("모든 항목을 입력해주세요.");
            return;
        }

        if (password !== pwRepeat){
            alert("비밀번호가 일치하지 않습니다.");
            return;
        }

        console.log({
            id,
            email,
            password,
            pwRepeat
        });
    };
    return (
        <div>
            <h1>회원가입</h1>
            <div>
                <label>아이디</label>
                <br />
                <input type = "text" placeholder ="아이디를 입력하세요" value={id} onChange={(e) => setId(e.target.value)}/>
            </div>
            <div>
                <label>이메일</label>
                <br />
                <input type = "text" placeholder = "이메일을 입력하세요" value={email} onChange={(e) => setEmail(e.target.value)}/>
            </div>

            <div>
                <label>비밀번호</label>
                <br />
                <input type = "password" placeholder = "비밀번호를 입력하세요" value={password} onChange={(e) => setPassword(e.target.value)}/>
            </div>
            <div>
                <label>비밀번호 확인</label>
                <br />
                <input type = "password" placeholder = "비밀번호를 다시 입력하세요" value={pwRepeat} onChange={(e) => setPwRepeat(e.target.value)}/>
            </div>

            <br />

            <button onClick={handleSignup}>회원가입</button>
        </div>

    );

};

export default Signup;