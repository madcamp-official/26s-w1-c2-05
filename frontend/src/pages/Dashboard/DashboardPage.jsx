import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../../api/client";
import PageHeader from "../../components/PageHeader";
import styles from "./DashboardPage.module.css";

// 카테고리 식별 색상은 검증된 3색 팔레트를 고정 순서로만 사용한다 (단어 -> 문법 -> 회화).
const CATEGORY_META = {
    voca: { label: "단어", color: "#2a78d6", to: "/flashcard" },
    grammar: { label: "문법", color: "#1baf7a", to: "/grammar" },
    dialogue: { label: "회화", color: "#eb6834", to: "/speaking" },
};

// 카테고리별 순위를 매길 단일 오답률이 없으므로, error_trend(최근 8일 일별 오답률)의
// 평균을 근사치로 쓴다.
function averageErrorRate(values){
    if (!Array.isArray(values) || values.length === 0) return 0;
    return Math.round(values.reduce((sum, v) => sum + v, 0) / values.length);
}

// error_trend 배열은 (오늘 포함) 최근 8일치이므로, 실제 날짜(M/D)로 라벨을 만든다.
function buildTrendLabels(){
    const today = new Date();
    return Array.from({ length: 8 }, (_, i) => {
        const d = new Date(today);
        d.setDate(d.getDate() - (7 - i));
        return `${d.getMonth() + 1}/${d.getDate()}`;
    });
}

function TrendChart({ errorTrend }){
    const width = 600;
    const height = 200;
    const marginLeft = 32;
    const marginRight = 12;
    const marginTop = 12;
    const marginBottom = 24;
    const plotWidth = width - marginLeft - marginRight;
    const plotHeight = height - marginTop - marginBottom;
    const maxValue = 60;
    const [hoveredIndex, setHoveredIndex] = useState(null);
    const [trendLabels] = useState(buildTrendLabels);

    const categoryKeys = Object.keys(CATEGORY_META).filter((key) => Array.isArray(errorTrend[key]));

    const xAt = (i) => marginLeft + (plotWidth * i) / (trendLabels.length - 1);
    const yAt = (v) => marginTop + plotHeight * (1 - v / maxValue);

    const linePath = (values) => values.map((v, i) => `${i === 0 ? "M" : "L"}${xAt(i)},${yAt(v)}`).join(" ");

    return (
        <div className={styles.chartWrap}>
            <svg viewBox={`0 0 ${width} ${height}`} className={styles.chartSvg} role="img" aria-label="최근 오답률 추이">
                {[0, 20, 40, 60].map((v) => (
                    <g key={v}>
                        <line x1={marginLeft} x2={width - marginRight} y1={yAt(v)} y2={yAt(v)} className={styles.gridline} />
                        <text x={marginLeft - 8} y={yAt(v) + 4} textAnchor="end" className={styles.axisLabel}>{v}%</text>
                    </g>
                ))}

                {hoveredIndex !== null && (
                    <line
                        x1={xAt(hoveredIndex)}
                        x2={xAt(hoveredIndex)}
                        y1={marginTop}
                        y2={height - marginBottom}
                        className={styles.crosshair}
                    />
                )}

                {categoryKeys.map((key) => (
                    <path key={key} d={linePath(errorTrend[key])} fill="none" stroke={CATEGORY_META[key].color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                ))}

                {categoryKeys.map((key) =>
                    errorTrend[key].map((v, i) => (
                        <circle
                            key={`${key}-${i}`}
                            cx={xAt(i)}
                            cy={yAt(v)}
                            r={hoveredIndex === i ? 5 : 3}
                            fill={CATEGORY_META[key].color}
                            stroke="#fff"
                            strokeWidth={hoveredIndex === i ? 2 : 0}
                        />
                    ))
                )}

                {trendLabels.map((label, i) => (
                    <g key={`${label}-${i}`}>
                        <rect
                            x={xAt(i) - plotWidth / (trendLabels.length - 1) / 2}
                            y={marginTop}
                            width={plotWidth / (trendLabels.length - 1)}
                            height={plotHeight}
                            fill="transparent"
                            onMouseEnter={() => setHoveredIndex(i)}
                            onMouseLeave={() => setHoveredIndex((cur) => (cur === i ? null : cur))}
                        />
                        <text x={xAt(i)} y={height - 6} textAnchor="middle" className={styles.axisLabel}>{label}</text>
                    </g>
                ))}
            </svg>

            {hoveredIndex !== null && (
                <div
                    className={styles.tooltip}
                    style={{ left: `${(xAt(hoveredIndex) / width) * 100}%` }}
                >
                    <p className={styles.tooltipDate}>{trendLabels[hoveredIndex]}</p>
                    {categoryKeys.map((key) => (
                        <p key={key} className={styles.tooltipRow}>
                            <span className={styles.tooltipDot} style={{ background: CATEGORY_META[key].color }} />
                            {CATEGORY_META[key].label} {errorTrend[key][hoveredIndex]}%
                        </p>
                    ))}
                </div>
            )}

            <div className={styles.legend}>
                {categoryKeys.map((key) => (
                    <span key={key} className={styles.legendItem}>
                        <span className={styles.legendDot} style={{ background: CATEGORY_META[key].color }} />
                        {CATEGORY_META[key].label}
                    </span>
                ))}
            </div>
        </div>
    );
}

// 오늘 카테고리별로 몇 개를 풀었는지를, 백엔드가 하루치로 내려주는 콘텐츠 개수(goal:
// 단어 20개/문법 3개/회화 1개, app/api/learning.py의 DAILY_GOALS와 동일) 대비 진행률로 보여준다.
function TodayActivityChart({ todayActivity }){
    const categoryKeys = Object.keys(CATEGORY_META);
    const total = categoryKeys.reduce((sum, key) => sum + (todayActivity[key]?.count ?? 0), 0);

    if (total === 0){
        return <p className={styles.todayEmpty}>오늘 아직 학습 기록이 없어요. 학습을 시작해보세요!</p>;
    }

    return (
        <div className={styles.todayActivity}>
            {categoryKeys.map((key) => {
                const { count = 0, goal = 0 } = todayActivity[key] ?? {};
                const percent = goal > 0 ? Math.min(100, Math.round((count / goal) * 100)) : 0;
                const achieved = goal > 0 && count >= goal;
                return (
                    <div key={key} className={styles.todayActivityRow}>
                        <span className={styles.todayActivityLabel}>{CATEGORY_META[key].label}</span>
                        <div className={styles.todayActivityBarTrack}>
                            <div
                                className={styles.todayActivityBarFill}
                                style={{ width: `${percent}%`, background: CATEGORY_META[key].color }}
                            />
                        </div>
                        <span className={styles.todayActivityCount}>
                            {count}/{goal}{achieved ? " ✓" : ""}
                        </span>
                    </div>
                );
            })}
            <p className={styles.todayActivityTotal}>오늘 총 {total}개 학습</p>
        </div>
    );
}

function DashboardPage(){
    const navigate = useNavigate();
    const [dashboard, setDashboard] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [{ greeting, dateLabel }] = useState(() => {
        const now = new Date();
        const hour = now.getHours();
        return {
            greeting: hour < 12 ? "좋은 아침이에요" : hour < 18 ? "좋은 오후예요" : "좋은 저녁이에요",
            dateLabel: now.toLocaleDateString("ko-KR", { month: "long", day: "numeric", weekday: "long" }),
        };
    });

    const fetchDashboard = () => {
        return client.get("/dashboard")
            .then((res) => {
                setDashboard(res.data);
                setLoadError(false);
            })
            .catch((err) => {
                console.error("대시보드 조회 실패:", err);
                setLoadError(true);
            })
            .finally(() => setIsLoading(false));
    };

    useEffect(() => {
        fetchDashboard();
    }, []);

    const handleReanalyze = () => {
        setIsLoading(true);
        fetchDashboard();
    };

    // 최초 로딩 중이거나(dashboard 없음) 실패했을 때는 전체 화면을 대체한다.
    // "다시 분석하기" 재조회 중에는 기존 데이터를 유지한 채 버튼만 비활성화한다.
    if (isLoading && !dashboard){
        return (
            <div className={styles.page}>
                <PageHeader title={`${greeting} 👋`} subtitle={dateLabel} />
                <p className={styles.loadingText}>대시보드를 불러오는 중입니다...</p>
            </div>
        );
    }

    if (loadError && !dashboard){
        return (
            <div className={styles.page}>
                <PageHeader title={`${greeting} 👋`} subtitle={dateLabel} />
                <p className={styles.loadingText}>대시보드를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.</p>
            </div>
        );
    }

    const feedbackItems = [
        { key: "voca", text: dashboard.feedback_voca },
        { key: "grammar", text: dashboard.feedback_grammar },
        { key: "dialogue", text: dashboard.feedback_dialogue },
    ].filter((item) => item.text);

    const errorTrend = dashboard.error_trend ?? {};

    return (
        <div className={styles.page}>
            <PageHeader
                title={`${greeting} 👋`}
                subtitle={`${dateLabel} · ${dashboard.language} · ${dashboard.daily_streak}일째`}
            />

            <div className={styles.statGrid}>
                <div className={styles.statTile}>
                    <p className={styles.statLabel}>연속 학습일</p>
                    <p className={styles.statValue}>{dashboard.daily_streak}</p>
                    <p className={styles.statUnit}>일 🔥</p>
                </div>
                <div className={styles.statTile}>
                    <p className={styles.statLabel}>총 학습량</p>
                    <p className={styles.statValue}>{dashboard.language_total}</p>
                    <p className={styles.statUnit}>누적</p>
                </div>
                <div className={styles.statTile}>
                    <p className={styles.statLabel}>정답률</p>
                    <p className={styles.statValue}>{dashboard.accuracy_rate}%</p>
                    <p className={styles.statUnit}>이번 주</p>
                </div>
            </div>

            <div className={styles.card}>
                <p className={styles.cardTitle}>오늘 학습량</p>
                <TodayActivityChart todayActivity={dashboard.today_activity ?? {}} />
            </div>

            <div className={styles.sectionHeader}>
                <div>
                    <p className={styles.sectionTitle}>취약점 분석</p>
                    <p className={styles.sectionSubtitle}>학습 기록 기반 분석</p>
                </div>
                <div className={styles.headerActions}>
                    <button className={styles.secondaryButton} onClick={() => window.print()}>
                        리포트 내보내기
                    </button>
                    <button className={styles.primaryInlineButton} onClick={handleReanalyze} disabled={isLoading}>
                        ✨ 다시 분석하기
                    </button>
                </div>
            </div>

            <div className={styles.statGrid}>
                <div className={styles.statTile}>
                    <p className={styles.statLabel}>취약 영역</p>
                    <p className={dashboard.most_weak ? styles.statValue : styles.statValueEmpty}>
                        {dashboard.most_weak ?? "아직 데이터가 없어요"}
                    </p>
                    <p className={styles.statUnit}>이번 주 정답률이 가장 낮은 영역</p>
                </div>
                <div className={styles.statTile}>
                    <p className={styles.statLabel}>가장 개선됨</p>
                    <p className={dashboard.most_improved ? styles.statValue : styles.statValueEmpty}>
                        {dashboard.most_improved ?? "아직 데이터가 없어요"}
                    </p>
                    <p className={styles.statUnit}>지난주 대비 정답률이 가장 많이 오른 영역</p>
                </div>
            </div>

            <div className={styles.stackedCards}>
                <div className={styles.card}>
                    <p className={styles.cardTitle}>피드백</p>
                    <ul className={styles.weaknessList}>
                        {feedbackItems.map((item) => (
                            <li key={item.key} className={styles.weaknessItem}>
                                <div className={styles.weaknessBody}>
                                    <div className={styles.weaknessHeadRow}>
                                        <span className={styles.categoryChip} style={{ background: `${CATEGORY_META[item.key].color}22`, color: CATEGORY_META[item.key].color }}>
                                            {CATEGORY_META[item.key].label}
                                        </span>
                                    </div>
                                    <p className={styles.weaknessDescription}>{item.text}</p>
                                    <button className={styles.ctaButton} onClick={() => navigate(CATEGORY_META[item.key].to)}>
                                        {CATEGORY_META[item.key].label} 학습하러 가기
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>

                <div className={styles.card}>
                    <p className={styles.cardTitle}>Error Trend</p>
                    <TrendChart errorTrend={errorTrend} />
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
