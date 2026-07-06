import { NavLink, Outlet } from "react-router-dom";
import "./AppLayout.css";

const NAV_ITEMS = [
    { to: "/dashboard", label: "대시보드" },
    { to: "/vocab", label: "단어 학습" },
    { to: "/flashcard", label: "플래시카드 퀴즈" },
    { to: "/grammar", label: "문법" },
    { to: "/speaking", label: "말하기" },
    { to: "/weakness", label: "취약점 분석" },
    { to: "/profile", label: "프로필" },
];

function AppLayout(){
    return (
        <div className="app-layout">
            <aside className="app-sidebar">
                <p className="app-sidebar-logo">[서비스 이름]</p>
                <p className="app-sidebar-tagline">AI 학습 도우미</p>

                <nav className="app-nav">
                    {NAV_ITEMS.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) =>
                                isActive ? "app-nav-item app-nav-item-active" : "app-nav-item"
                            }
                        >
                            {item.label}
                        </NavLink>
                    ))}
                </nav>
            </aside>

            <main className="app-content">
                <Outlet />
            </main>
        </div>
    );
};

export default AppLayout;
