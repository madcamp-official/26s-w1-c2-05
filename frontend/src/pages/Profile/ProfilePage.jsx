import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getProfile, logout } from "../../api/user";
import styles from "./ProfilePage.module.css";

const MOCK_PROFILE = {
    userID: "MADCAMP123",
    email: "madcamp@example.com",
    current_language: "English",
    target_days: 180,
    studied_days: 10,
    daily_streak: 5,
};

function ProfilePage(){
    const navigate = useNavigate();
    const [profile, setProfile] = useState(MOCK_PROFILE);
    const [isLoggingOut, setIsLoggingOut] = useState(false);

    useEffect(() => {
        getProfile()
            .then((data) => setProfile(data))
            .catch((err) => console.error("프로필 조회 실패:", err));
    }, []);

    const handleLogout = async () => {
        setIsLoggingOut(true);
        await logout();
        navigate("/login", { replace: true });
    };

    const progressPercent = Math.min(
        100,
        Math.round((profile.studied_days / profile.target_days) * 100)
    );

    return (
        <div className={styles.page}>
            <h1 className={styles.title}>프로필</h1>
            <p className={styles.subtitle}>계정 정보 및 학습 현황</p>

            <div className={styles.body}>
                <div className={styles.card}>
                    <p className={styles.cardTitle}>계정 정보</p>
                    <div className={styles.accountRow}>
                        <div className={styles.avatar}>{profile.userID.slice(0, 2).toUpperCase()}</div>
                        <div>
                            <p className={styles.userId}>{profile.userID}</p>
                            <p className={styles.userEmail}>{profile.email}</p>
                        </div>
                    </div>

                    <button className={styles.logoutButton} onClick={handleLogout} disabled={isLoggingOut}>
                        로그아웃
                    </button>
                </div>

                <div className={styles.card}>
                    <p className={styles.cardTitle}>학습 현황</p>

                    <div className={styles.infoRow}>
                        <span>학습 언어</span>
                        <span className={styles.infoValue}>{profile.current_language}</span>
                    </div>
                    <div className={styles.infoRow}>
                        <span>연속 학습</span>
                        <span className={styles.infoValue}>{profile.daily_streak}일 🔥</span>
                    </div>

                    <div className={styles.progressHeader}>
                        <span>목표 달성률</span>
                        <span className={styles.infoValue}>
                            {profile.studied_days} / {profile.target_days}일 ({progressPercent}%)
                        </span>
                    </div>
                    <div className={styles.progressBar}>
                        <div className={styles.progressBarFill} style={{ width: `${progressPercent}%` }} />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProfilePage;
