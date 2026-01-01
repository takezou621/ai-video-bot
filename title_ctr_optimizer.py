"""
Title CTR Optimizer - Analyze and optimize YouTube titles for click-through rate
Based on SEO best practices and the blog's approach to search intent optimization
"""
import re
from typing import Dict, List, Tuple, Optional


class TitleCTROptimizer:
    """
    Analyzes and optimizes YouTube titles for maximum CTR.

    Best practices:
    - Optimal length: 50-70 characters (Japanese)
    - Include numbers for list-style content
    - Use emotional trigger words
    - Front-load important keywords
    - Use question format when appropriate
    """

    # Character length constraints
    OPTIMAL_MIN_LENGTH = 20
    OPTIMAL_MAX_LENGTH = 50
    ABSOLUTE_MAX_LENGTH = 100  # YouTube's hard limit

    # Emotional trigger words (Japanese)
    TRIGGER_WORDS = {
        "衝撃": {"category": "shock", "weight": 3},
        "驚愕": {"category": "shock", "weight": 3},
        "緊急": {"category": "urgency", "weight": 3},
        "速報": {"category": "urgency", "weight": 3},
        "最新": {"category": "recency", "weight": 2},
        "最強": {"category": "superlative", "weight": 2},
        "最高": {"category": "superlative", "weight": 2},
        "完全": {"category": "completeness", "weight": 2},
        "簡単": {"category": "ease", "weight": 2},
        "秘密": {"category": "curiosity", "weight": 3},
        "真実": {"category": "curiosity", "weight": 2},
        "理由": {"category": "explanation", "weight": 2},
        "方法": {"category": "how_to", "weight": 2},
        "解説": {"category": "explanation", "weight": 1},
        "まとめ": {"category": "summary", "weight": 1},
        "話題": {"category": "trending", "weight": 2},
        "危険": {"category": "warning", "weight": 3},
        "注意": {"category": "warning", "weight": 2}
    }

    @staticmethod
    def analyze_title(title: str, named_entities: List[str] = None) -> Dict:
        """
        Comprehensive title analysis for CTR optimization.

        Args:
            title: YouTube title to analyze
            named_entities: List of important named entities (companies, products)

        Returns:
            Analysis report with CTR score and recommendations
        """
        named_entities = named_entities or []

        analysis = {
            "title": title,
            "length": len(title),
            "ctr_score": 0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "metrics": {}
        }

        # Metric 1: Length check
        length_score = TitleCTROptimizer._analyze_length(title)
        analysis["metrics"]["length"] = length_score
        analysis["ctr_score"] += length_score["score"]

        if length_score["optimal"]:
            analysis["strengths"].append(f"最適な長さ（{len(title)}文字）")
        else:
            if len(title) < TitleCTROptimizer.OPTIMAL_MIN_LENGTH:
                analysis["weaknesses"].append(f"タイトルが短い（{len(title)}文字）")
                analysis["recommendations"].append(
                    f"タイトルを{TitleCTROptimizer.OPTIMAL_MIN_LENGTH}文字以上に延長"
                )
            elif len(title) > TitleCTROptimizer.OPTIMAL_MAX_LENGTH:
                analysis["weaknesses"].append(f"タイトルが長い（{len(title)}文字）")
                analysis["recommendations"].append(
                    f"タイトルを{TitleCTROptimizer.OPTIMAL_MAX_LENGTH}文字以下に短縮"
                )

        # Metric 2: Emotional triggers
        trigger_score = TitleCTROptimizer._analyze_triggers(title)
        analysis["metrics"]["triggers"] = trigger_score
        analysis["ctr_score"] += trigger_score["score"]

        if trigger_score["found"]:
            analysis["strengths"].append(
                f"感情トリガーワード使用: {', '.join(trigger_score['words'])}"
            )
        else:
            analysis["recommendations"].append(
                "感情トリガーワード（衝撃、最新、速報など）を追加"
            )

        # Metric 3: Numbers (list-style)
        number_score = TitleCTROptimizer._analyze_numbers(title)
        analysis["metrics"]["numbers"] = number_score
        analysis["ctr_score"] += number_score["score"]

        if number_score["found"]:
            analysis["strengths"].append(f"数値使用: {number_score['numbers']}")
        else:
            analysis["recommendations"].append(
                "リスト形式（例：「5つの理由」）を検討"
            )

        # Metric 4: Question format
        question_score = TitleCTROptimizer._analyze_question(title)
        analysis["metrics"]["question"] = question_score
        analysis["ctr_score"] += question_score["score"]

        if question_score["is_question"]:
            analysis["strengths"].append("疑問形を使用")

        # Metric 5: Named entity placement
        entity_score = TitleCTROptimizer._analyze_entity_placement(title, named_entities)
        analysis["metrics"]["entity_placement"] = entity_score
        analysis["ctr_score"] += entity_score["score"]

        if entity_score["front_loaded"]:
            analysis["strengths"].append(
                f"重要キーワードを前方配置: {entity_score['entity']}"
            )
        elif named_entities and not entity_score["found"]:
            analysis["weaknesses"].append("重要キーワードが含まれていない")
            analysis["recommendations"].append(
                f"企業名・製品名を追加: {', '.join(named_entities[:3])}"
            )

        # Metric 6: Bracket usage (【】)
        bracket_score = TitleCTROptimizer._analyze_brackets(title)
        analysis["metrics"]["brackets"] = bracket_score
        analysis["ctr_score"] += bracket_score["score"]

        if bracket_score["found"]:
            analysis["strengths"].append("括弧【】で強調")

        # Metric 7: Specificity (date, version, etc.)
        specificity_score = TitleCTROptimizer._analyze_specificity(title)
        analysis["metrics"]["specificity"] = specificity_score
        analysis["ctr_score"] += specificity_score["score"]

        if specificity_score["found"]:
            analysis["strengths"].append(
                f"具体性: {', '.join(specificity_score['elements'])}"
            )

        # Normalize CTR score to 0-100
        max_score = 35  # Maximum possible score from all metrics
        analysis["ctr_score"] = min(100, int((analysis["ctr_score"] / max_score) * 100))

        # Add grade
        if analysis["ctr_score"] >= 80:
            analysis["grade"] = "A"
        elif analysis["ctr_score"] >= 60:
            analysis["grade"] = "B"
        elif analysis["ctr_score"] >= 40:
            analysis["grade"] = "C"
        else:
            analysis["grade"] = "D"

        return analysis

    @staticmethod
    def _analyze_length(title: str) -> Dict:
        """Analyze title length."""
        length = len(title)

        optimal = TitleCTROptimizer.OPTIMAL_MIN_LENGTH <= length <= TitleCTROptimizer.OPTIMAL_MAX_LENGTH

        if optimal:
            score = 5
        elif length < TitleCTROptimizer.OPTIMAL_MIN_LENGTH:
            score = max(0, 5 - (TitleCTROptimizer.OPTIMAL_MIN_LENGTH - length) // 5)
        else:
            score = max(0, 5 - (length - TitleCTROptimizer.OPTIMAL_MAX_LENGTH) // 10)

        return {
            "length": length,
            "optimal": optimal,
            "score": score
        }

    @staticmethod
    def _analyze_triggers(title: str) -> Dict:
        """Analyze emotional trigger words."""
        found_words = []
        total_weight = 0

        for word, info in TitleCTROptimizer.TRIGGER_WORDS.items():
            if word in title:
                found_words.append(word)
                total_weight += info["weight"]

        return {
            "found": len(found_words) > 0,
            "words": found_words,
            "score": min(10, total_weight * 2)  # Max 10 points
        }

    @staticmethod
    def _analyze_numbers(title: str) -> Dict:
        """Analyze number usage (list-style titles)."""
        # Match numbers (Arabic or Japanese)
        numbers = re.findall(r'\d+|[一二三四五六七八九十]+', title)

        return {
            "found": len(numbers) > 0,
            "numbers": numbers,
            "score": 5 if numbers else 0
        }

    @staticmethod
    def _analyze_question(title: str) -> Dict:
        """Analyze question format."""
        question_markers = ['？', '?', 'とは', 'なぜ', 'どう', 'いつ', 'どこ', '何']

        is_question = any(marker in title for marker in question_markers)

        return {
            "is_question": is_question,
            "score": 3 if is_question else 0
        }

    @staticmethod
    def _analyze_entity_placement(title: str, entities: List[str]) -> Dict:
        """Analyze named entity placement (front-loading)."""
        if not entities:
            return {"found": False, "front_loaded": False, "score": 0}

        # Check if any entity appears in first 15 characters
        first_segment = title[:15]

        for entity in entities:
            if entity in title:
                front_loaded = entity in first_segment
                return {
                    "found": True,
                    "entity": entity,
                    "front_loaded": front_loaded,
                    "score": 7 if front_loaded else 3
                }

        return {"found": False, "front_loaded": False, "score": 0}

    @staticmethod
    def _analyze_brackets(title: str) -> Dict:
        """Analyze bracket usage for emphasis."""
        has_brackets = '【' in title and '】' in title

        return {
            "found": has_brackets,
            "score": 2 if has_brackets else 0
        }

    @staticmethod
    def _analyze_specificity(title: str) -> Dict:
        """Analyze specificity (dates, versions, numbers)."""
        elements = []

        # Check for dates (MM/DD, YYYY年, etc.)
        if re.search(r'\d{1,2}/\d{1,2}|\d{4}年', title):
            elements.append("日付")

        # Check for versions
        if re.search(r'v?\d+\.\d+|ver\.?\s*\d+', title, re.IGNORECASE):
            elements.append("バージョン")

        # Check for percentages
        if re.search(r'\d+%|割', title):
            elements.append("割合")

        return {
            "found": len(elements) > 0,
            "elements": elements,
            "score": min(3, len(elements) * 2)
        }

    @staticmethod
    def generate_optimized_variants(
        base_title: str,
        named_entities: List[str] = None
    ) -> List[Dict]:
        """
        Generate optimized title variants.

        Args:
            base_title: Base title to optimize
            named_entities: Important named entities

        Returns:
            List of optimized title variants with analysis
        """
        named_entities = named_entities or []
        variants = []

        # Original
        variants.append({
            "variant": "original",
            "title": base_title,
            "analysis": TitleCTROptimizer.analyze_title(base_title, named_entities)
        })

        # Variant 1: Add emotional trigger
        if named_entities:
            var1 = f"【最新】{named_entities[0]} {base_title}"
            variants.append({
                "variant": "with_trigger",
                "title": var1,
                "analysis": TitleCTROptimizer.analyze_title(var1, named_entities)
            })

        # Variant 2: Question format
        var2 = f"{base_title}とは？"
        variants.append({
            "variant": "question",
            "title": var2,
            "analysis": TitleCTROptimizer.analyze_title(var2, named_entities)
        })

        # Variant 3: With number
        var3 = f"【5分で解説】{base_title}"
        variants.append({
            "variant": "with_number",
            "title": var3,
            "analysis": TitleCTROptimizer.analyze_title(var3, named_entities)
        })

        # Sort by CTR score
        variants.sort(key=lambda x: x["analysis"]["ctr_score"], reverse=True)

        return variants


if __name__ == "__main__":
    # Test
    optimizer = TitleCTROptimizer()

    test_titles = [
        "OpenAI 最新情報総まとめ",
        "【衝撃】OpenAI GPT-5 発表の裏側",
        "なぜOpenAIは世界を変えたのか？5つの理由",
        "12/19 OpenAI最新ニュース速報"
    ]

    print("Title CTR Analysis\n")

    for title in test_titles:
        print(f"Title: {title}")
        analysis = optimizer.analyze_title(title, ["OpenAI"])
        print(f"  CTR Score: {analysis['ctr_score']}/100 (Grade: {analysis['grade']})")
        print(f"  Strengths: {', '.join(analysis['strengths'][:3])}")
        if analysis['recommendations']:
            print(f"  Recommendations: {analysis['recommendations'][0]}")
        print()

    # Test variant generation
    print("\nGenerating optimized variants:")
    base = "AI最新ニュース"
    variants = optimizer.generate_optimized_variants(base, ["OpenAI", "Google"])

    for i, var in enumerate(variants[:3], 1):
        print(f"{i}. {var['title']}")
        print(f"   Score: {var['analysis']['ctr_score']}/100")
