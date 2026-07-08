import { useTheme } from "./ThemeContext";
import styles from "./ThemeToggle.module.css";

function ThemeToggle({ className = "" }){
    const { theme, toggleTheme } = useTheme();
    const isDark = theme === "dark";

    return (
        <button
            type="button"
            className={`${styles.toggle} ${className}`}
            onClick={toggleTheme}
            aria-label={isDark ? "라이트 모드로 전환" : "다크 모드로 전환"}
            title={isDark ? "라이트 모드로 전환" : "다크 모드로 전환"}
        >
            {isDark ? "☀️" : "🌙"}
        </button>
    );
}

export default ThemeToggle;
