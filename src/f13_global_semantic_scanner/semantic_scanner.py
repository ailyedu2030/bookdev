"""F13: 全局语义扫描系统

跨章节语义安全扫描,检测:
1. 单话题跨章节传播路径
2. 多话题组合风险
3. 全局风险评分
"""

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════
# 内置敏感词库 (可扩展)
# ═══════════════════════════════════════════════════════════════

_SENSITIVE_TOPICS: dict[str, float] = {
    "台海": 0.70,
    "台湾": 0.65,
    "西藏": 0.65,
    "新疆": 0.60,
    "香港": 0.55,
    "南海": 0.55,
    "钓鱼岛": 0.55,
    "领土": 0.55,
    "争议": 0.50,
    "主权": 0.65,
    "领土争端": 0.65,
    "主权争议": 0.70,
    "意识形态": 0.55,
    "政治体制": 0.55,
    "民主": 0.45,
    "自由": 0.40,
    "人权": 0.55,
    "民族": 0.50,
    "宗教": 0.55,
    "舆论引导": 0.55,
    "舆论管控": 0.60,
    "网络审查": 0.55,
    "军事": 0.50,
    "军队": 0.50,
    "国防": 0.50,
    "国家安全": 0.60,
    "分裂": 0.70,
    "独立": 0.55,
    "颜色革命": 0.80,
    "暴力": 0.60,
    "极端": 0.60,
    "极端主义": 0.75,
    "恐怖": 0.75,
    "历史观": 0.50,
    "历史认知": 0.55,
    "历史虚无主义": 0.70,
    "国际干预": 0.55,
    "外部势力": 0.55,
    "地缘政治": 0.50,
    "宣传": 0.40,
    "洗脑": 0.70,
    "颠覆": 0.70,
}

# 预编译正则缓存
_TOPIC_PATTERNS: dict[str, re.Pattern] = {topic: re.compile(re.escape(topic)) for topic in _SENSITIVE_TOPICS}


# ═══════════════════════════════════════════════════════════════
# Data Class
# ═══════════════════════════════════════════════════════════════


@dataclass
class ScanResult:
    topic_id: str
    risk_score: float
    affected_chapters: list[str] = field(default_factory=list)
    combined_risks: list[str] = field(default_factory=list)
    base_weight: float = 0.0
    frequency: int = 0
    chapter_count: int = 0


# ═══════════════════════════════════════════════════════════════
# TopicTracker
# ═══════════════════════════════════════════════════════════════


class TopicTracker:
    """跨章节话题追踪器

    追踪敏感话题在全书各章节的分布,计算跨章节传播风险。
    """

    def __init__(self) -> None:
        self._topics: dict[str, dict] = {}
        # topic -> {chapters: {ch_id: weight}, total_weight: float, frequency: int}
        self._chapter_map: dict[str, set[str]] = defaultdict(set)
        # chapter_id -> set of topic_ids

    def track_topic(self, topic: str, chapter_id: str, weight: float = 1.0) -> None:
        """追踪话题在章节中的出现

        Args:
            topic: 话题标识符
            chapter_id: 章节ID
            weight: 权重 (0.0-1.0)
        """
        if topic not in self._topics:
            self._topics[topic] = {
                "chapters": {},
                "total_weight": 0.0,
                "frequency": 0,
            }
        entry = self._topics[topic]
        if chapter_id in entry["chapters"]:
            entry["chapters"][chapter_id] = max(entry["chapters"][chapter_id], weight)
        else:
            entry["chapters"][chapter_id] = weight
        entry["total_weight"] += weight
        entry["frequency"] += 1
        self._chapter_map[chapter_id].add(topic)

    def get_topic_chapters(self, topic: str) -> list[str]:
        """获取话题出现的所有章节"""
        if topic in self._topics:
            return sorted(self._topics[topic]["chapters"].keys())
        return []

    def get_chapter_topics(self, chapter_id: str) -> list[str]:
        """获取章节中所有话题"""
        return sorted(self._chapter_map.get(chapter_id, set()))

    def get_risk_score(self, topic: str) -> float:
        """计算话题的跨章节风险评分

        风险 = min(1.0, spread_factor * weight_factor)
        - spread_factor: 章节分布广度 (出现在越多章节 → 越高)
        - weight_factor: 累积权重
        """
        if topic not in self._topics:
            return 0.0

        entry = self._topics[topic]
        chapter_count = len(entry["chapters"])
        total_weight = entry["total_weight"]
        frequency = entry["frequency"]

        if chapter_count == 0:
            return 0.0

        # 分布因子: 章节数越多风险越高 (sigmoid-like)
        spread_factor = math.tanh(chapter_count / 4.0)

        # 权重因子: 累积权重归一化
        weight_factor = min(1.0, total_weight / max(frequency, 1))

        # 频率加强: 高频出现加强风险
        freq_boost = min(1.0, math.log1p(frequency) / math.log1p(10))

        raw_score = spread_factor * weight_factor * (0.7 + 0.3 * freq_boost)
        return round(min(1.0, raw_score), 4)


# ═══════════════════════════════════════════════════════════════
# CombinationAnalyzer
# ═══════════════════════════════════════════════════════════════


class CombinationAnalyzer:
    """组合敏感分析器

    检测多个话题同时出现时的组合风险。
    某些话题单独出现无害,但组合后风险显著升高。
    """

    def __init__(self) -> None:
        self._combinations: dict[str, int] = defaultdict(int)
        # "topic1||topic2" -> occurrence count
        self._rules: dict[str, float] = {}
        # "topic1||topic2" -> base risk weight
        self._observed_combinations: dict[str, dict] = {}
        # "topic1||topic2" -> {count, score, topics}

    def add_rule(self, topic1: str, topic2: str, risk_weight: float) -> None:
        """添加组合规则

        Args:
            topic1: 话题1
            topic2: 话题2
            risk_weight: 组合基础风险权重 (0.0-1.0)
        """
        key = self._make_key(topic1, topic2)
        self._rules[key] = max(0.0, min(1.0, risk_weight))

    def analyze_combination(self, topics: list[str]) -> float:
        """分析一组话题的组合风险

        Args:
            topics: 同时出现的话题列表

        Returns:
            组合风险评分 (0.0-1.0)
        """
        if len(topics) < 2:
            return 0.0

        sorted_topics = sorted(set(topics))
        key = "||".join(sorted_topics)
        self._combinations[key] += 1
        count = self._combinations[key]

        # 基础分: 话题数量 × 出现频率 (上限0.5)
        base_score = min(0.5, 0.1 * len(topics) * count)

        # 规则加成: 检查所有2-组合是否有规则
        rule_bonus = 0.0
        rule_matches = 0
        matched_rule_pairs: list[tuple[str, str, float]] = []
        for i in range(len(sorted_topics)):
            for j in range(i + 1, len(sorted_topics)):
                pair_key = self._make_key(sorted_topics[i], sorted_topics[j])
                if pair_key in self._rules:
                    rw = self._rules[pair_key]
                    rule_bonus += rw
                    rule_matches += 1
                    matched_rule_pairs.append((sorted_topics[i], sorted_topics[j], rw))

        has_rules = rule_matches > 0

        if has_rules:
            avg_rule_weight = rule_bonus / rule_matches
            # 规则主导: 95%规则 + 5%基础
            combined = base_score * 0.05 + avg_rule_weight * 0.95
            # 频率微调: 次数加成 (饱和,最多15%)
            freq_mod = min(1.15, 1.0 + 0.05 * math.log1p(count))
            combined = min(1.0, combined * freq_mod)
        else:
            combined = base_score

        # 存储观测
        self._observed_combinations[key] = {
            "count": count,
            "score": round(combined, 4),
            "topics": sorted_topics,
            "has_rules": has_rules,
            "rule_pairs": matched_rule_pairs,
        }

        return round(combined, 4)

    def get_dangerous_combinations(self, threshold: float = 0.7) -> list[dict]:
        """获取超过阈值的危险组合

        仅返回至少匹配一条规则的组合。

        Args:
            threshold: 风险阈值 (0.0-1.0)

        Returns:
            危险组合列表,按风险降序排列
        """
        dangerous = []
        for _key, obs in self._observed_combinations.items():
            # 仅规则匹配的组合才算危险
            if not obs.get("has_rules", False):
                continue
            score = obs["score"]
            if score >= threshold:
                topics = obs["topics"]
                rule_pairs = obs.get("rule_pairs", [])

                dangerous.append(
                    {
                        "topics": topics,
                        "score": score,
                        "occurrences": obs["count"],
                        "matched_rules": [{"pair": (t1, t2), "rule_weight": rw} for t1, t2, rw in rule_pairs],
                    }
                )

        dangerous.sort(key=lambda x: x["score"], reverse=True)
        return dangerous

    @staticmethod
    def _make_key(topic1: str, topic2: str) -> str:
        """生成排序后的组合键"""
        return "||".join(sorted([topic1, topic2]))


# ═══════════════════════════════════════════════════════════════
# GlobalSemanticScanner
# ═══════════════════════════════════════════════════════════════


class GlobalSemanticScanner:
    """全局语义扫描器

    协调 TopicTracker 和 CombinationAnalyzer,
    对全书进行跨章节语义安全扫描。
    """

    def __init__(self) -> None:
        self.topic_tracker = TopicTracker()
        self.combination_analyzer = CombinationAnalyzer()
        self._scanned_chapters: set[str] = set()
        self._chapter_results: dict[str, list[ScanResult]] = {}

        # 内置危险组合规则
        self._init_default_rules()

    def _init_default_rules(self) -> None:
        """初始化内置危险组合规则"""
        rules = [
            ("台海", "军事", 0.85),
            ("台湾", "独立", 0.90),
            ("西藏", "独立", 0.90),
            ("新疆", "独立", 0.90),
            ("领土", "军事", 0.75),
            ("主权", "国际干预", 0.75),
            ("意识形态", "颜色革命", 0.85),
            ("意识形态", "颠覆", 0.80),
            ("宗教", "极端主义", 0.80),
            ("民族", "分裂", 0.85),
            ("历史观", "意识形态", 0.65),
            ("舆论引导", "宣传", 0.55),
            ("舆论管控", "自由", 0.60),
            ("网络审查", "自由", 0.60),
            ("暴力", "恐怖", 0.85),
            ("极端", "暴力", 0.80),
            ("国家安全", "外部势力", 0.75),
            ("地缘政治", "国际干预", 0.65),
            ("领土争端", "主权争议", 0.70),
            ("香港", "独立", 0.80),
        ]
        for t1, t2, weight in rules:
            self.combination_analyzer.add_rule(t1, t2, weight)

    def scan_chapter(self, chapter_id: str, content: str) -> list[ScanResult]:
        """扫描章节内容,检测敏感话题

        Args:
            chapter_id: 章节标识符
            content: 章节文本内容

        Returns:
            ScanResult列表
        """
        if not content or not content.strip():
            return []

        self._scanned_chapters.add(chapter_id)
        results: list[ScanResult] = []
        detected_topics: set[str] = set()

        # 关键词匹配
        for topic, base_weight in _SENSITIVE_TOPICS.items():
            pattern = _TOPIC_PATTERNS[topic]
            matches = pattern.findall(content)
            if matches:
                count = len(matches)
                detected_topics.add(topic)

                # 计算权重: base_weight * 出现次数因子
                freq_factor = min(1.0, math.log1p(count) / math.log1p(5))
                weight = base_weight * (0.6 + 0.4 * freq_factor)

                self.topic_tracker.track_topic(topic, chapter_id, weight)

                result = ScanResult(
                    topic_id=topic,
                    risk_score=round(min(1.0, weight), 4),
                    base_weight=base_weight,
                    frequency=count,
                    chapter_count=1,
                )
                results.append(result)

        # 组合分析: 章节内同时出现的话题
        if len(detected_topics) >= 2:
            combo_score = self.combination_analyzer.analyze_combination(list(detected_topics))
            if combo_score > 0:
                for r in results:
                    r.combined_risks.append(f"组合风险:{'+'.join(sorted(detected_topics))}={combo_score:.4f}")

        # 更新 affected_chapters
        for r in results:
            r.affected_chapters = self.topic_tracker.get_topic_chapters(r.topic_id)
            r.chapter_count = len(r.affected_chapters)

        self._chapter_results[chapter_id] = results
        return results

    def get_global_risk_score(self) -> float:
        """计算全局风险评分

        综合:
        - 所有话题的跨章节风险
        - 危险组合数量
        - 扫描章节数
        """
        if not self._scanned_chapters:
            return 0.0

        # 话题风险平均
        topic_scores = []
        for results in self._chapter_results.values():
            for r in results:
                topic_scores.append(self.topic_tracker.get_risk_score(r.topic_id))

        if not topic_scores:
            return 0.0

        avg_topic_risk = sum(topic_scores) / len(topic_scores)

        # 组合风险加成
        dangerous = self.combination_analyzer.get_dangerous_combinations(threshold=0.3)
        combo_penalty = min(1.0, len(dangerous) * 0.1)

        # 章节覆盖因子
        chapter_factor = min(1.0, len(self._scanned_chapters) / 10.0)

        raw_score = (avg_topic_risk * 0.6 + combo_penalty * 0.4) * (0.5 + 0.5 * chapter_factor)
        return round(min(1.0, raw_score), 4)

    def get_cross_chapter_risks(self) -> list[dict]:
        """获取跨章节风险列表

        检测同一话题在多个章节中出现的情况。
        """
        risks: list[dict] = []

        for topic, entry in self.topic_tracker._topics.items():
            chapters = list(entry["chapters"].keys())
            if len(chapters) >= 2:
                risk_score = self.topic_tracker.get_risk_score(topic)
                avg_weight = entry["total_weight"] / max(entry["frequency"], 1)

                risks.append(
                    {
                        "topic": topic,
                        "chapters": chapters,
                        "chapter_count": len(chapters),
                        "risk_score": risk_score,
                        "total_weight": round(entry["total_weight"], 4),
                        "frequency": entry["frequency"],
                        "avg_weight": round(avg_weight, 4),
                        "severity": self._classify_severity(risk_score),
                    }
                )

        risks.sort(key=lambda x: x["risk_score"], reverse=True)
        return risks

    def generate_scan_report(self) -> dict:
        """生成完整扫描报告"""
        cross_risks = self.get_cross_chapter_risks()
        dangerous = self.combination_analyzer.get_dangerous_combinations(threshold=0.3)

        # 汇总统计
        total_topics_detected = 0
        for results in self._chapter_results.values():
            total_topics_detected += len(results)

        unique_topics = set()
        for results in self._chapter_results.values():
            for r in results:
                unique_topics.add(r.topic_id)

        return {
            "global_risk_score": self.get_global_risk_score(),
            "total_chapters_scanned": len(self._scanned_chapters),
            "total_topics_detected": total_topics_detected,
            "unique_topics_count": len(unique_topics),
            "cross_chapter_risks": cross_risks,
            "dangerous_combinations": dangerous,
            "high_severity_count": sum(1 for r in cross_risks if r["severity"] == "HIGH"),
            "medium_severity_count": sum(1 for r in cross_risks if r["severity"] == "MEDIUM"),
            "low_severity_count": sum(1 for r in cross_risks if r["severity"] == "LOW"),
            "scanned_chapter_ids": sorted(self._scanned_chapters),
        }

    @staticmethod
    def _classify_severity(score: float) -> str:
        """根据评分分类严重程度"""
        if score >= 0.7:
            return "HIGH"
        elif score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
