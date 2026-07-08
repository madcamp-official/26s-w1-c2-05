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
<img width="1472" height="868" alt="image" src="https://github.com/user-attachments/assets/08b09e16-6a13-453a-870e-8b79209a82fb" />



---

## API 문서

> API 주소, 요청 방식, 요청값, 응답값, 에러 상황을 정리
>
> 아래 명세는 실제 실행 중인 백엔드(로컬 테스트 DB 기준)에 대해 각 엔드포인트를 직접 호출해 응답을 확인한 뒤 작성했습니다.

### 공통 사항

- **Base URL:** 로컬 개발 기준 `http://localhost:8000` (별도 prefix 없이 아래 경로가 그대로 붙습니다)
- **인증 방식:** `POST /auth/login`으로 받은 `access_token`을 이후 요청의 헤더에 `Authorization: Bearer {access_token}`로 실어 보냅니다. 표에 "인증 필요"로 표시된 엔드포인트는 헤더가 없으면 요청 자체가 거부됩니다.
- **인증 공통 에러**
  - 헤더에 `Authorization`이 아예 없는 경우 → `401 Unauthorized` `{"detail": "Not authenticated"}`
  - 토큰이 있지만 만료·위조되었거나 토큰의 사용자가 존재하지 않는 경우 → `401 Unauthorized` `{"detail": "인증 정보를 확인할 수 없습니다"}` (헤더 `WWW-Authenticate: Bearer` 포함)
- **언어 코드(`lang_id`):** `languages` 테이블 시딩값 기준 1=English, 2=Japanese, 3=Chinese, 4=Spanish, 5=French, 6=German, 7=Italian, 8=Vietnamese (프론트 `frontend/src/pages/Onboarding/data/languages.js`와 순서 동일)
- **레벨 코드:** `A1`(1) · `A2`(2) · `B1`(3) · `B2`(4) · `C1`(5) · `C2`(6)

---

### 인증 (`app/api/auth.py`)

| Method | Endpoint | 설명 | 인증 필요 |
|---|---|---|:---:|
| POST | `/auth/signup` | 회원가입 | ✗ |
| POST | `/auth/login` | 로그인, access/refresh 토큰 발급 | ✗ |
| POST | `/auth/refresh` | refresh token으로 access token 재발급 | ✗ |
| POST | `/auth/logout` | 서버에 저장된 refresh token 폐기 | ✗ |

<details>
<summary>POST /auth/signup</summary>

요청
```json
{ "username": "madcamp", "email": "madcamp@gmail.com", "password": "abcd1234", "pw_repeat": "abcd1234" }
```
비밀번호는 8자 이상이면서 숫자·문자를 모두 포함해야 합니다.

응답
```
200 OK
{ "user_id": "madcamp", "email": "madcamp@gmail.com", "nickname": "The curiositarian", "profile_img": null, "current_learning_id": null }

400 Bad Request
{ "detail": "이미 가입된 이메일입니다." }
{ "detail": "중복된 ID입니다." }
{ "detail": "비밀번호와 비밀번호 확인 문자가 같은지 확인해주세요." }
{ "detail": "비밀번호는 숫자와 문자로 구성되고 8자리 이상이어야 합니다." }
```
</details>

<details>
<summary>POST /auth/login</summary>

요청
```json
{ "id": "madcamp", "password": "abcd1234" }
```

응답
```
200 OK
{ "access_token": "...", "refresh_token": "...", "token_type": "bearer", "SurveyCompleted": true }
```
`SurveyCompleted`는 `current_learning_id`(= 온보딩 완료 여부)를 기준으로 계산되며, 프론트가 로그인 직후 `/onboarding`으로 보낼지 `/dashboard`로 보낼지 판단하는 데 씁니다.
```
401 Unauthorized
{ "detail": "Incorrect id or password" }
```
</details>

<details>
<summary>POST /auth/refresh</summary>

요청
```json
{ "refresh_token": "..." }
```

응답
```
200 OK
{ "access_token": "...", "token_type": "bearer" }

401 Unauthorized
{ "detail": "Invalid refresh-token." }                        // DB에 없는(이미 로그아웃된 포함) 토큰
{ "detail": "Refresh-token이 만료되었거나 유효하지 않습니다." }   // JWT 자체가 만료/위조
{ "detail": "사용자를 찾을 수 없습니다." }
```
</details>

<details>
<summary>POST /auth/logout</summary>

요청
```json
{ "refresh_token": "..." }
```

응답
```
200 OK
{ "message": "로그아웃 하였습니다." }

400 Bad Request
{ "detail": "Invalid refresh-token." }   // 이미 로그아웃되었거나 존재하지 않는 토큰
```
</details>

---

### 온보딩 & 프로필 (`app/api/onboarding.py`, `app/api/me.py`)

| Method | Endpoint | 설명 | 인증 필요 |
|---|---|---|:---:|
| POST | `/onboarding` | 최초 설문조사(학습 언어/레벨/목표 기간) 등록 | ✓ |
| GET | `/users/me` | 본인 프로필 + 현재 학습 언어 진도 조회 | ✓ |
| GET | `/me/languages` | 지원하는 8개 언어 전체와, 언어별 학습 이력/현재 학습 여부 조회 | ✓ |
| POST | `/me/language` | 학습 언어 전환(이미 학습한 언어면 진도 유지, 처음이면 새로 시작) | ✓ |

<details>
<summary>POST /onboarding</summary>

**한 계정당 한 번만 성공합니다.** 이미 `current_learning_id`가 설정된 사용자가 다시 호출하면 언어·레벨 값과 무관하게 400이 반환됩니다 — 학습 언어를 바꾸고 싶을 때는 `/me/language`를 사용하세요.

요청 (헤더: `Authorization: Bearer {access_token}`)
```json
{ "language": 1, "level": "B1", "StudyGoal": 90 }
```
- `language`: 1~8
- `level`: `A1`~`C2`
- `StudyGoal`: 1~365 (일)

응답
```
200 OK
{ "detail": "다 되었습니다! 이제 메인화면으로 이동합니다.", "userInfo": { "userID": "madcamp", "DailyStreak": 0 } }

400 Bad Request
{ "detail": "올바르지 않은 응답입니다" }   // 값 범위 벗어남, 또는 이미 온보딩을 완료한 사용자
```
</details>

<details>
<summary>GET /users/me</summary>

응답
```
200 OK
{
  "userID": "madcamp",
  "email": "madcamp@example.com",
  "current_language": "English",
  "target_days": 90,
  "studied_days": 10,
  "daily_streak": 5
}
```
</details>

<details>
<summary>GET /me/languages</summary>

프로필 화면의 "학습 언어 변경" 모달이 사용합니다. 항목 순서는 `lang_id` 오름차순(1~8) 고정입니다.

응답
```
200 OK
[
  { "lang_id": 1, "language": "English", "in_progress": true, "is_current": true, "current_level": "B1", "studied_days": 12 },
  { "lang_id": 2, "language": "Japanese", "in_progress": false, "is_current": false, "current_level": null, "studied_days": null },
  ...
]
```
- `in_progress`: 이 사용자가 해당 언어로 학습을 시작한 적이 있는지 (LearningProgresses row 존재 여부)
- `is_current`: 지금 활성화된 학습 언어인지
- `current_level` / `studied_days`: `in_progress`가 `false`면 항상 `null`
</details>

<details>
<summary>POST /me/language</summary>

요청 (헤더: `Authorization: Bearer {access_token}`)
```json
{ "language": 8 }
```
이미 학습 이력이 있는 언어(`in_progress: true`)로 전환할 때는 `language`만 보내면 됩니다 — 기존 레벨/목표 기간/연속 학습일 등 진도가 그대로 이어집니다.

처음 시작하는 언어라면 `level`, `StudyGoal`을 함께 보내야 합니다 (온보딩과 동일한 규칙):
```json
{ "language": 8, "level": "A1", "StudyGoal": 30 }
```

응답
```
200 OK
{ "detail": "학습 언어가 전환되었습니다.", "current_language": "Vietnamese" }

400 Bad Request
{ "detail": "올바르지 않은 언어입니다" }                                  // language가 1~8 범위 밖
{ "detail": "처음 시작하는 언어는 레벨과 목표 기간을 함께 보내야 합니다" }   // 새 언어인데 level/StudyGoal 누락 또는 범위 밖
```
</details>

---

### 학습 콘텐츠 (`app/api/vocabulary.py`, `app/api/learning.py`)

모든 학습 콘텐츠 조회는 로그인한 사용자의 `current_learning_id`(= 현재 학습 언어)를 기준으로 응답이 결정됩니다.

| Method | Endpoint | 설명 | 인증 필요 |
|---|---|---|:---:|
| GET | `/vocabulary` | 단어장(오늘 학습할 단어, spaced-repetition 20개) | ✓ |
| GET | `/flashcard` | 플래시카드(단어 20개 + 오답 선택지 3개씩) | ✓ |
| GET | `/grammar` | 오늘의 문법 학습(spaced-repetition 3개 + 각 개념별 퀴즈) | ✓ |
| GET | `/grammar/all` | 전체 문법 커리큘럼(레벨순, 퀴즈 미포함) | ✓ |
| POST | `/answerlog` | 단어/문법 문제 풀이 결과 기록 | ✓ |

<details>
<summary>GET /vocabulary</summary>

응답
```
200 OK
{
  "vocabularies": [
    { "number": 1, "content_id": 46, "word": "begin", "meaning": "시작하다", "example": "The class will begin at nine." }
  ]
}
```
</details>

<details>
<summary>GET /flashcard</summary>

응답
```
200 OK
{
  "vocabularies": [
    {
      "number": 1,
      "content_id": 46,
      "language": "English",
      "word": "begin",
      "choices": ["걱정하는", "시작하다", "순조로운", "장소, 곳"],
      "answer": 2
    }
  ]
}
```
`answer`는 정답이 `choices` 배열에서 몇 번째(1-base)인지를 가리키는 인덱스입니다.
</details>

<details>
<summary>GET /grammar</summary>

응답
```
200 OK
{
  "grammars": [
    {
      "number": 1,
      "content_id": 8,
      "subject": "be동사 과거",
      "explanation": "was, were, is 형태: ... 예문: ...",
      "quiz": [
        { "quiz": "She _____ a professor once upon a time.", "quiz_content_id": 11, "answer": "was" }
      ]
    }
  ]
}
```
</details>

<details>
<summary>GET /grammar/all</summary>

학습 진도 알고리즘을 거치지 않고 현재 학습 언어의 전체 문법 개념을 `level` 오름차순으로 반환합니다. 퀴즈는 포함하지 않습니다 (프론트의 "전체 커리큘럼" 탭용).

응답
```
200 OK
{
  "grammars": [
    { "content_id": 6, "level": 1, "subject": "be동사", "explanation": "am are is 형태: ... 예문: ..." },
    { "content_id": 7, "level": 1, "subject": "일반동사", "explanation": "..." }
  ]
}
```
</details>

<details>
<summary>POST /answerlog</summary>

요청
```json
{
  "content_id": 4321,
  "type": "grammar",
  "response_time": 5.23,
  "is_correct": true,
  "time": "2026-07-08T14:30:00Z"
}
```
- `type`: `"flash"`(단어/플래시카드) · `"grammar"`(문법) 중 하나. `content_id`는 각각 `/flashcard`·`/grammar`가 내려준 `content_id`(단어) 또는 `quiz_content_id`(문법)를 그대로 돌려보냅니다.

응답
```
200 OK
null

400 Bad Request
{ "detail": "잘못된 접근: 학습 type이 맞지 않습니다." }
```
</details>

---

### 회화 (`app/api/learning.py`, 내부적으로 `app/api/gemini.py`가 Gemini로 문장을 생성)

| Method | Endpoint | 설명 | 인증 필요 |
|---|---|---|:---:|
| GET | `/dialogue` | 오늘의 회화 주제 + 시작 문장 생성 | ✓ |
| POST | `/dialoguelog` | 사용자 응답 전송, 다음 대화 턴 + 피드백 생성 | ✓ |

<details>
<summary>GET /dialogue</summary>

응답
```
200 OK
{
  "content_id": 3881,
  "subject": "호텔 체크인하기",
  "flow": "greeting",
  "flow_stages": ["greeting", "reservation_check", "room_preference", "payment", "key_handoff", "closing"],
  "content": "Welcome to our hotel! Are you here to check in today?",
  "translation": "저희 호텔에 오신 것을 환영합니다! 오늘 체크인하시러 오셨나요?"
}

404 Not Found
{ "detail": "학습할 수 있는 회화 콘텐츠가 없습니다." }
```
`flow_stages`는 이 대화 주제 전체의 단계 목록이고, `flow`는 그중 현재 단계입니다. 프론트는 이 값으로 상단 진행 단계 표시줄을 그립니다.
</details>

<details>
<summary>POST /dialoguelog</summary>

요청
```json
{
  "content_id": 3881,
  "flow": "greeting",
  "response": "Yes, I have a reservation under the name Alice.",
  "response_time": 4.5,
  "time": "2026-07-08T14:30:00Z",
  "history": [
    { "role": "ai", "content": "Welcome to our hotel! Are you here to check in today?" },
    { "role": "user", "content": "Yes, I have a reservation under the name Alice." }
  ]
}
```
`history`는 이번 응답 이전까지의 전체 대화입니다. 서버가 턴 단위 대화를 저장하지 않으므로, LLM이 문맥(예: 이미 말한 이름을 또 묻는 등)을 잃지 않도록 매 요청마다 프론트가 함께 보냅니다.

응답
```
200 OK
{
  "content_id": 3881,
  "end": false,
  "subject": "호텔 체크인하기",
  "flow": "reservation_check",
  "flow_stages": ["greeting", "reservation_check", "room_preference", "payment", "key_handoff", "closing"],
  "content": "Great, let me check that for you. Could you spell your last name, please?",
  "translation": "네, 확인해 드릴게요. 성함 스펠링을 말씀해주시겠어요?",
  "feedback": "문법적으로 완벽하며 상대방에게 본인의 신원을 밝히는 적절한 인사입니다."
}

400 Bad Request
{ "detail": "잘못된 접근: flow가 해당 회화 콘텐츠의 흐름에 속하지 않습니다." }

404 Not Found
{ "detail": "회화 콘텐츠를 찾을 수 없습니다." }
```
`end: true`가 내려오면 해당 대화가 마지막 단계까지 끝난 것이며, 서버가 자동으로 `event_logs`에 학습 기록을 남깁니다(별도로 `/answerlog`를 호출할 필요 없음).
</details>

---

### 대시보드 (`app/api/dashboard.py`)

| Method | Endpoint | 설명 | 인증 필요 |
|---|---|---|:---:|
| GET | `/dashboard` | 현재 학습 언어의 이번 주 학습 현황·취약점 분석 | ✓ |

<details>
<summary>GET /dashboard</summary>

응답
```
200 OK
{
  "language": "English",
  "daily_streak": 5,
  "language_total": 312,
  "accuracy_rate": 78,
  "most_weak": "회화",
  "most_improved": "단어",
  "feedback_voca": "이번 주 가장 헷갈려 한 단어는 instinct예요.",
  "feedback_grammar": "가장 많이 헷갈려하는 부분은 현재분사와 과거분사 구분이에요.",
  "feedback_dialogue": "이번 주 회화 학습 기록이 없어요. 학습을 시작해보세요!",
  "error_trend": {
    "voca": [20, 19, 18, 18, 19, 18, 16, 16],
    "grammar": [20, 19, 18, 18, 19, 18, 16, 16],
    "dialogue": [20, 19, 18, 18, 19, 18, 16, 16]
  },
  "today_activity": {
    "voca": { "count": 0, "goal": 20 },
    "grammar": { "count": 1, "goal": 3 },
    "dialogue": { "count": 0, "goal": 1 }
  }
}
```
- `error_trend`는 오늘을 포함한 최근 8일의 카테고리별 오답률(%) 추이입니다. 해당 날짜에 기록이 없으면 그 전날 값을 그대로 이어씁니다(그래프가 0으로 끊겨 보이지 않도록).
- `most_weak` / `most_improved`와 각 `feedback_*`는 이번 주 학습 기록이 전혀 없는 카테고리라면 오해를 막기 위해 `null` 대신 "기록이 없다"는 안내 문장을 내려줍니다.
- `today_activity.goal`은 카테고리별 "오늘의 학습" 목표 개수로, 각 GET 엔드포인트(`/vocabulary`,`/grammar`,`/dialogue`)가 실제로 내려주는 콘텐츠 개수와 항상 일치합니다.
</details>
---

## 배포 결과물

> 접속 가능한 링크, 실행 방법, 주요 구현 내용

- **서비스 URL:** https://languaai.madcamp-kaist.org/
- **실행 방법:** Chrome 접속후 URL 입력 후 이용

---

## 회고 문서

> 개발 과정에서의 어려움, 해결 방법, 역할 분담, 다음에 개선할 점 (KPT 방법론 참고)

### Keep
- **Frontend와 Backend로 역할분담**: 실무적인 웹개발에서 하듯이 Front와 Back으로 역할을 나누고, 인당 하나씩 역할을 맡아 개발했다. 이 방식으로 개발을 하니 API 명세서만 제대로 작성되어 있다면, 프런트엔드와 백엔드 각자 이를 기반으로 독립적으로 개발을 진행하는데 문제가 없었다.

- **Github branch 관리**: 하나의 branch에서 개발하지 않고 front와 backend로 branch를 나눠 각각 개발하고 나중에 merge하는 방식을 사용했었다. 확실히 개발을 하는 과정에서 서로 브랜치가 충돌날 일이 매우 적었고, 그래서 개발이 수월했던 것 같다. 실무에서 쓰는 branch 관리 이론들을 상세하게 적용할까 고민도 했었지만, 2인 개발이었기 때문에 branch 관리가 그리 어렵지 않을 거라 생각해 backend와 frontend로만 나눴다.

### Problem
- **상대적으로 부실했던 초기 설계**: 초기 db스키마와 api 명세서 설계를 직접 손으로 했는데, 크게 중요하지 않다 생각해서 엄밀하게 하지 않았다. 그랬더니 후에 백엔드에서 기능을 설계하는 과정에서 DB스키마와 약간 다르게 구현하는 등 구현에서 어려움이 있었다. 또한 api 명세서를 조금만 설계하고, 설계하면서 내용을 조금씩 추가하는 방식으로 개발했는데, 프런트와 백의 개발속도에서 조금씩 차이가 나 한 쪽이 API 구현을 끝내고 api 명세서가 추가되기까지 기다리는 병목현상도 존재했었다. 

### Try
- **LLM을 활용한 초반 설계**: 모든 설계를 LLM에게 맡기는 것이 아니다. 초기 설계 과정에서 본인이 생각하는 DB 스키마 구조와 API 요청/응답 프로토콜 양식, 그리고 구현하고 싶은 기능들을 LLM에 입력하고 API명세서와 DB 스키마의 초안을 받는다. 이 초안들을 직접 훑어보면서 가져갈 부분과 바꿀부분을 적절히 선택해가면서 설계서를 작성하면 초반 설계에 걸리는 시간을 획기적으로 줄일 수 있을 것 같다.

- ****
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
