// 진행 중인 화면(예: 끝나지 않은 회화)을 벗어나기 전에 확인을 받기 위한 전역 플래그.
// react-router가 BrowserRouter(선언형) 모드라 useBlocker(데이터 라우터 전용)를 쓸 수 없어서,
// 사이드바 네비게이션 클릭을 가로채는 방식으로 대신한다.
let leaveMessage = null;

export function setLeaveGuard(message) {
    leaveMessage = message;
}

export function clearLeaveGuard() {
    leaveMessage = null;
}

export function confirmLeave() {
    if (!leaveMessage) return true;
    return window.confirm(leaveMessage);
}
