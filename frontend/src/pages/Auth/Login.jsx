import { useState } from "react";

function Login() {
  const [id, setId] = useState("");
  const [password, setPassword] = useState("");

  return (
    <div>
      <h1>로그인</h1>

      <div>
        <label>아이디</label>
        <br />
        <input
          type="text"
          placeholder="아이디를 입력하세요"
          value={id}
          onChange={(e) => setId(e.target.value)}
        />
      </div>

      <br />

      <div>
        <label>비밀번호</label>
        <br />
        <input
          type="password"
          placeholder="비밀번호를 입력하세요"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>

      <br />

      <button>로그인</button>
    </div>
  );
}

export default Login;