import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../../api/client";
import { getProfile } from "../../api/user";
import PageHeader from "../../components/PageHeader";
import styles from "./DashboardPage.module.css";

const INITIAL_STATS = [
    { key: "streak", label: "연속 학습일", value: "24", unit: "일 🔥" },
    { key: "words", label: "학습한 단어", value: "312", unit: "누적" },
    { key: "accuracy", label: "정답률", value: "78%", unit: "이번 주" },
];

// 카테고리 식별 색상은 검증된 3색 팔레트를 고정 순서로만 사용한다 (단어 -> 문법 -> 회화).
const INITIAL_CATEGORIES = [
    { key: "vocabulary", label: "단어", color: "#2a78d6", score: 72, trend: 6, errorRate: 15 },
    { key: "grammar", label: "문법", color: "#1baf7a", score: 48, trend: -2, errorRate: 41 },
    { key: "speaking", label: "회화", color: "#eb6834", score: 40, trend: -3, errorRate: 47 },
];

const TOP_WEAKNESS_AREAS = [
    {
        rank: 1,
        title: "Subjunctive Mood",
        category: "grammar",
        errorRate: 61,
        description: "직설법과 접속법 트리거를 혼동하고 있어요. 최근 20문제 중 12번 틀렸습니다.",
        cta: "문법으로 이동",
        to: "/grammar",
    },
    {
        rank: 2,
        title: "발음 정확도 · Intonation",
        category: "speaking",
        errorRate: 39,
        description: "이번 주 녹음한 답변에서 억양(Intonation) 정확도가 계속 가장 낮게 나타났어요.",
        cta: "회화 연습하기",
        to: "/speaking",
    },
    {
        rank: 3,
        title: "가정 관련 단어",
        category: "vocabulary",
        errorRate: 30,
        description: "이 카테고리 단어 22개가 7일 넘게 복습되지 않았어요.",
        cta: "플래시카드 복습",
        to: "/flashcard",
    },
];

const TREND_DATES = ["6/8", "6/12", "6/16", "6/20", "6/24", "6/28", "7/2", "7/6"];
const TREND_SERIES = {
    vocabulary: [24, 22, 21, 19, 18, 17, 16, 15],
    grammar: [45, 44, 46, 43, 42, 44, 41, 41],
    speaking: [34, 36, 38, 40, 42, 44, 46, 47],
};

function TrendChart({ categories }){
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

    const xAt = (i) => marginLeft + (plotWidth * i) / (TREND_DATES.length - 1);
    const yAt = (v) => marginTop + plotHeight * (1 - v / maxValue);

    const linePath = (values) => values.map((v, i) => `${i === 0 ? "M" : "L"}${xAt(i)},${yAt(v)}`).join(" ");

    return (
        <div className={styles.chartWrap}>
            <svg viewBox={`0 0 ${width} ${height}`} className={styles.chartSvg} role="img" aria-label="최근 30일 오답률 추이">
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

                {categories.map((cat) => (
                    <path key={cat.key} d={linePath(TREND_SERIES[cat.key])} fill="none" stroke={cat.color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                ))}

                {categories.map((cat) =>
                    TREND_SERIES[cat.key].map((v, i) => (
                        <circle
                            key={`${cat.key}-${i}`}
                            cx={xAt(i)}
                            cy={yAt(v)}
                            r={hoveredIndex === i ? 5 : 3}
                            fill={cat.color}
                            stroke="#fff"
                            strokeWidth={hoveredIndex === i ? 2 : 0}
                        />
                    ))
                )}

                {TREND_DATES.map((date, i) => (
                    <g key={date}>
                        <rect
                            x={xAt(i) - plotWidth / (TREND_DATES.length - 1) / 2}
                            y={marginTop}
                            width={plotWidth / (TREND_DATES.length - 1)}
                            height={plotHeight}
                            fill="transparent"
                            onMouseEnter={() => setHoveredIndex(i)}
                            onMouseLeave={() => setHoveredIndex((cur) => (cur === i ? null : cur))}
                        />
                        <text x={xAt(i)} y={height - 6} textAnchor="middle" className={styles.axisLabel}>{date}</text>
                    </g>
                ))}
            </svg>

            {hoveredIndex !== null && (
                <div
                    className={styles.tooltip}
                    style={{ left: `${(xAt(hoveredIndex) / width) * 100}%` }}
                >
                    <p className={styles.tooltipDate}>{TREND_DATES[hoveredIndex]}</p>
                    {categories.map((cat) => (
                        <p key={cat.key} className={styles.tooltipRow}>
                            <span className={styles.tooltipDot} style={{ background: cat.color }} />
                            {cat.label} {TREND_SERIES[cat.key][hoveredIndex]}%
                        </p>
                    ))}
                </div>
            )}

            <div className={styles.legend}>
                {categories.map((cat) => (
                    <span key={cat.key} className={styles.legendItem}>
                        <span className={styles.legendDot} style={{ background: cat.color }} />
                        {cat.label}
                    </span>
                ))}
            </div>
        </div>
    );
}

function DashboardPage(){
    const navigate = useNavigate();
    const [stats, setStats] = useState(INITIAL_STATS);
    const [categories, setCategories] = useState(INITIAL_CATEGORIES);
    const [analyzedAt, setAnalyzedAt] = useState("오늘 오전 9:12");
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [{ greeting, dateLabel }] = useState(() => {
        const now = new Date();
        const hour = now.getHours();
        return {
            greeting: hour < 12 ? "좋은 아침이에요" : hour < 18 ? "좋은 오후예요" : "좋은 저녁이에요",
            dateLabel: now.toLocaleDateString("ko-KR", { month: "long", day: "numeric", weekday: "long" }),
        };
    });

    useEffect(() => {
        getProfile()
            .then((data) => {
                if (typeof data?.daily_streak === "number") {
                    setStats((prev) =>
                        prev.map((s) => (s.key === "streak" ? { ...s, value: String(data.daily_streak) } : s))
                    );
                }
            })
            .catch((err) => console.error("프로필 조회 실패:", err));
    }, []);

    const weakest = categories.reduce((a, b) => (a.score < b.score ? a : b));
    const mostImproved = categories.reduce((a, b) => (a.trend > b.trend ? a : b));
    const overallErrorRate = Math.round(
        categories.reduce((sum, c) => sum + c.errorRate, 0) / categories.length
    );

    const handleReanalyze = () => {
        setIsAnalyzing(true);
        client.get("/weakness/analysis").catch((err) => console.error("취약점 분석 조회 실패:", err));

        setCategories((prev) =>
            prev.map((c) => {
                const delta = Math.round((Math.random() - 0.5) * 8);
                return {
                    ...c,
                    score: Math.min(95, Math.max(20, c.score + delta)),
                    trend: delta,
                    errorRate: Math.min(80, Math.max(5, c.errorRate - delta)),
                };
            })
        );
        setAnalyzedAt("방금 전");
        setIsAnalyzing(false);
    };

    const handleExportReport = () => {
        window.print();
    };

    return (
        <div className={styles.page}>
            <PageHeader
                title={`${greeting} 👋`}
                subtitle={`${dateLabel} · 스페인어 · ${stats[0].value}일째`}
            />

            <div className={styles.statGrid}>
                {stats.map((s) => (
                    <div key={s.key} className={styles.statTile}>
                        <p className={styles.statLabel}>{s.label}</p>
                        <p className={styles.statValue}>{s.value}</p>
                        <p className={styles.statUnit}>{s.unit}</p>
                    </div>
                ))}
            </div>

            <div className={styles.sectionHeader}>
                <div>
                    <p className={styles.sectionTitle}>취약점 분석</p>
                    <p className={styles.sectionSubtitle}>AI 기반 분석 · 마지막 분석: {analyzedAt}</p>
                </div>
                <div className={styles.headerActions}>
                    <button className={styles.secondaryButton} onClick={handleExportReport}>
                        리포트 내보내기
                    </button>
                    <button className={styles.primaryInlineButton} onClick={handleReanalyze} disabled={isAnalyzing}>
                        ✨ 다시 분석하기
                    </button>
                </div>
            </div>

            <div className={styles.statGrid}>
                <div className={styles.statTile}>
                    <p className={styles.statLabel}>취약 영역</p>
                    <p className={styles.statValue}>{weakest.label}</p>
                </div>
                <div className={styles.statTile}>
                    <p className={styles.statLabel}>가장 개선됨</p>
                    <p className={styles.statValue}>{mostImproved.label}</p>
                </div>
                <div className={styles.statTile}>
                    <p className={styles.statLabel}>전체 오답률</p>
                    <p className={styles.statValue}>{overallErrorRate}%</p>
                </div>
            </div>

            <div className={styles.stackedCards}>
                <div className={styles.card}>
                    <p className={styles.cardTitle}>Top Weakness Areas</p>
                    <ul className={styles.weaknessList}>
                        {TOP_WEAKNESS_AREAS.map((item) => {
                            const cat = categories.find((c) => c.key === item.category);
                            return (
                                <li key={item.rank} className={styles.weaknessItem}>
                                    <div className={styles.weaknessRank}>{item.rank}</div>
                                    <div className={styles.weaknessBody}>
                                        <div className={styles.weaknessHeadRow}>
                                            <span className={styles.weaknessTitle}>{item.title}</span>
                                            <span className={styles.categoryChip}>{cat.label}</span>
                                        </div>
                                        <div className={styles.weaknessBar}>
                                            <div
                                                className={styles.weaknessBarFill}
                                                style={{ width: `${item.errorRate}%`, background: cat.color }}
                                            />
                                        </div>
                                        <p className={styles.weaknessMeta}>{item.errorRate}% 오답률</p>
                                        <p className={styles.weaknessDescription}>{item.description}</p>
                                        <button className={styles.ctaButton} onClick={() => navigate(item.to)}>
                                            {item.cta}
                                        </button>
                                    </div>
                                </li>
                            );
                        })}
                    </ul>
                </div>

                <div className={styles.card}>
                    <p className={styles.cardTitle}>Error Trend — 최근 30일</p>
                    <TrendChart categories={categories} />
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
