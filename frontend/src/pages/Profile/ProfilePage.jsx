import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getProfile, logout } from "../../api/user";
import LanguageSwitchModal from "./LanguageSwitchModal";
import styles from "./ProfilePage.module.css";

function ProfilePage(){
    const navigate = useNavigate();
    const [profile, setProfile] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [isLoggingOut, setIsLoggingOut] = useState(false);
    const [isLanguageModalOpen, setIsLanguageModalOpen] = useState(false);

    const loadProfile = () => {
        return getProfile()
            .then((data) => {
                if (typeof data?.userID === "string") {
                    setProfile(data);
                } else {
                    setLoadError(true);
                }
            })
            .catch((err) => {
                console.error("프로필 조회 실패:", err);
                setLoadError(true);
            });
    };

    useEffect(() => {
        loadProfile().finally(() => setIsLoading(false));
    }, []);

    const handleLanguageSwitched = () => {
        setIsLanguageModalOpen(false);
        loadProfile();
    };

    const handleLogout = async () => {
        setIsLoggingOut(true);
        await logout();
        navigate("/login", { replace: true });
    };

    if (isLoading){
        return <div className={styles.page}>프로필을 불러오는 중입니다...</div>;
    }

    if (loadError || !profile){
        return <div className={styles.page}>프로필을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.</div>;
    }

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
                        <span className={styles.infoValue}>
                            {profile.current_language}
                            <button className={styles.changeLanguageButton} onClick={() => setIsLanguageModalOpen(true)}>
                                변경
                            </button>
                        </span>
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

            {isLanguageModalOpen && (
                <LanguageSwitchModal
                    onClose={() => setIsLanguageModalOpen(false)}
                    onSwitched={handleLanguageSwitched}
                />
            )}
        </div>
    );
};

export default ProfilePage;
