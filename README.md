# 26s-w1-c2-05

## 공통과제 I : 웹 기반 프로젝트 (2인 1팀)

**목적:** 공통 과제를 함께 수행하며 웹 개발의 전체 흐름을 빠르게 익히고 협업에 적응하기

**결과물:** 기획부터 배포까지 완료된 웹 서비스와 관련 문서 일체

---

## 팀원

| 이름 | GitHub | 역할 |
|---|---|---|
| 이재준 | dannyiscard | 백엔드 |
| 박소요 | oyossss | 프론트엔드 |

---

## 기획안

> 프로젝트 주제, 목적, 핵심 기능, 예상 사용자, 팀원별 역할 등 정리

- **주제:** 효율적 외국어 학습을 위한 웹사이트
- **목적:** 사용자들로 하여금 외국어 학습을 최대한 효율적으로 할 수 있도록 한다
- **핵심 기능:** 1. 원하는 언어에 맞는 플랫폼 학습 제공. 2. 진도 저장 및 로드 3. 단어장, 문법, 회화 연습 등
- **예상 사용자:** 외국어 학습을 원하는 사람들

---

## 기능 명세서

> 구현할 기능을 사용자 관점에서 정리하고, 필수 기능과 선택 기능을 구분

### 필수 기능

- [이메일을 통한 회원가입 및 로그인]
- [학습 목적 등 설문조사 및 이를 기반으로 커리큘럼 생성]
- [단어장]
- [단어 학습]
- [문법 학습]
- [회화 학습]

### 선택 기능

- []


## IA 및 화면 설계서

> 서비스의 전체 페이지 구조와 페이지 간 이동 흐름; 각 페이지의 주요 UI 구성, 입력 요소, 버튼, 사용자 행동 흐름 등을 간단한 와이어프레임 형태로 정리

<!-- Figma 링크 또는 이미지 첨부 -->

---

## DB 스키마

> 필요한 테이블, 주요 필드, 데이터 타입, 테이블 간 관계를 정리

<!-- ERD 이미지 또는 테이블 정의 -->
<img width="1472" height="868" alt="image" src="https://github.com/user-attachments/assets/94a25548-16fb-444a-ae22-8f49691c3edb" />


---

## API 문서

> API 주소, 요청 방식, 요청값, 응답값, 에러 상황을 정리

| Method | Endpoint | 설명 | 요청 | 응답 |
|---|---|---|---|---|
| POST | /auth/signup | 회원가입 | JSON {"id": "madcamp", "email": "madcamp@gmail.com", "password": "123456", "pw_repeat": "123456"} | 200 OK {"detail": "회원가입이 완료되었습니다."} 400 Bad Request {"detail": "이미 가입된 이메일입니다."} {"detail": "비밀번호와 비밀번호 확인 문자가 같은지 확인해주세요."} {"detail": "비밀번호는 숫자와 문자로 구성되고 8자리 이상이어야 합니다."} {"detail": "중복된 아이디입니다."}|
|POST|/auth/login|로그인|JSON {"id": "madcamp", "password": "123456"}|200 OK {"accessToken": "...", "refreshToken": "...", "token_type": "bearer", "SurveyCompleted": false} 400 Bad Request {"detail: ID 또는 비밀번호가 일치하지 않습니다."}|
|POST|/auth/logout|로그아웃|JSON {"refresh_token": "..."}|200 OK {"detail": "로그아웃 되었습니다."}|
|POST|/onboarding|최초 설문조사|JSON {"language": 1, "level": "B1", "StudyGoal": 90}|200 OK {detail: "다 되었습니다! 이제 메인화면으로 이동합니다.", "userInfo": {"userID": "MADCAMP123", "DailyStreak": 0}} 400 Bad Request {detail: "올바르지 않은 응답입니다."}|
|GET|/users/me|본인 프로필 조회||200 OK {"userID": "MADCAMP123", "email": "madcamp@example.com", "current_anguage": "English", "target_days": 180, "studied_days": 10, "daily_streak": 5}|
|GET|/vocabulary|단어장으로 이동||200 OK {"vocabularies": [{"number": 1,  "word": "careless", "meaning": "경솔한", "example": "Careless people need to think twice before they move on."}]}|
|GET|/flashcard|플래시카드로 이동|JSON {"category": "flash"}|200 OK {"vocabularies": [{"number": 1, "content_id": 4321, "language": "Spanish", "word": "careless", "choices": ["choice1", "choice2", "choice3", "choice4"]}]}|
|POST|/answerlog|응답 결과를 전송|JSON {"user_id": "MADCAMP123", "content_id": 4321, "type": "flash", "response_time": 5.2324242s, "choice": 3, "time": 2023-07-04T14:30:00Z}|200 OK {"is_correct": true, "answer": 3}|
|GET|||||
---

## 배포 결과물

> 접속 가능한 링크, 실행 방법, 주요 구현 내용

- **서비스 URL:**
- **실행 방법:**

```bash
# 실행 방법 작성
```

---

## 회고 문서

> 개발 과정에서의 어려움, 해결 방법, 역할 분담, 다음에 개선할 점 (KPT 방법론 참고)

### Keep

### Problem

### Try

---

## 참고 자료

- [SDD(스펙 주도 개발) 이해하기](https://news.hada.io/topic?id=21338)
- [Software Design Document Best Practices](https://www.atlassian.com/work-management/project-management/design-document)
- [IA 정보구조도 작성 방법](https://brunch.co.kr/@nyonyo/7)
- [기획자 화면설계서 작성법](https://brunch.co.kr/@soup/10)
- [Figma 와이어프레임 가이드](https://www.figma.com/ko-kr/resource-library/what-is-wireframing/)
- [무료 Figma 와이어프레임 키트](https://www.figma.com/ko-kr/templates/wireframe-kits/)
- [ERD/DB 설계 총정리](https://inpa.tistory.com/entry/DB-%F0%9F%93%9A-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EB%AA%A8%EB%8D%B8%EB%A7%81-%EA%B0%9C%EB%85%90-ERD-%EB%8B%A4%EC%9D%B4%EC%96%B4%EA%B7%B8%EB%9E%A8)
- [API 명세서 작성 가이드라인](https://velog.io/@sebinChu/BackEnd-API-%EB%AA%85%EC%84%B8%EC%84%9C-%EC%9E%91%EC%84%B1-%EA%B0%80%EC%9D%B4%EB%93%9C-%EB%9D%BC%EC%9D%B8)
- [좋은 README 작성하는 방법](https://velog.io/@sabo/good-readme)
- [단기 프로젝트 회고 KPT 방법론](https://velog.io/@habwa/%EB%8B%A8%EA%B8%B0-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8-%ED%9A%8C%EA%B3%A0-KPT-%EB%B0%A9%EB%B2%95%EB%A1%A0)
