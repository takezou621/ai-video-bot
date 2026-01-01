"""
Automated Metadata Generator
Generates complete YouTube metadata using templates
Enhanced with CTR optimization for better click-through rates
"""
import re
from typing import Dict, Any, List, Optional
from content_templates import ContentTemplates
from title_ctr_optimizer import TitleCTROptimizer


def generate_complete_metadata(
    script: Dict[str, Any],
    timing_data: List[Dict],
    video_duration_seconds: float,
    claude_metadata: Dict[str, Any] = None,
    verified_source_urls: List[str] = None
) -> Dict[str, Any]:
    """
    Generate complete YouTube metadata with templates

    Args:
        script: Generated script
        timing_data: Subtitle timing data
        video_duration_seconds: Video duration
        claude_metadata: Optional AI-generated metadata (from Gemini)
        verified_source_urls: Optional list of verified source URLs (prioritized over script URLs)

    Returns:
        Complete metadata package
    """
    title = script.get("title", "")
    description = script.get("description", "")
    key_points = []
    named_entities = script.get("named_entities", [])
    primary_entity = _get_primary_entity(named_entities)

    # Extract labels from named entities for CTR analysis
    named_entity_labels = [entity.get("label") for entity in named_entities if entity.get("label")]

    # Extract key points from dialogues
    dialogues = script.get("dialogues", [])
    for i, dialogue in enumerate(dialogues):
        if i % 10 == 0 and i < 50:  # Sample every 10th dialogue
            text = dialogue.get("text", "")
            if len(text) > 20:
                key_points.append(text[:80] + "..." if len(text) > 80 else text)

    # Generate timestamps
    timestamps = ContentTemplates.generate_timestamps(script, timing_data)

    # Generate comprehensive description
    full_description = ContentTemplates.generate_description(
        title=title,
        topic=title,
        key_points=key_points[:5],
        timestamps=timestamps,
        angle="わかりやすく",
        target_audiences=[
            "経済・ビジネスに興味がある方",
            "最新トピックをキャッチアップしたい方",
            "短時間で理解を深めたい方"
        ],
        next_topic="関連する経済トピック",
        hashtags=claude_metadata.get("hashtags", []) if claude_metadata else ["#経済", "#ビジネス", "#解説"]
    )

    # Append source URLs for credibility
    # Prioritize verified URLs passed directly, then fallback to script-generated ones
    source_urls = verified_source_urls if verified_source_urls else script.get("source_urls", [])
    
    if source_urls:
        full_description += "\n\n## 引用元・ソース\n"
        for url in source_urls:
            # Simple validation to ensure it's a URL
            if url and url.startswith("http"):
                full_description += f"- {url}\n"

    # Combine AI metadata with template metadata
    youtube_title = claude_metadata.get("youtube_title", title) if claude_metadata else title
    youtube_title = _enforce_named_entity_prefix(youtube_title, primary_entity)

    # Optimize title for CTR (blog's SEO approach)
    title_optimizer = TitleCTROptimizer()
    title_analysis = title_optimizer.analyze_title(youtube_title, named_entity_labels)

    # If CTR score is low, try to improve
    if title_analysis["ctr_score"] < 60:
        print(f"  [CTR] Title score low ({title_analysis['ctr_score']}/100), generating optimized variants...")
        variants = title_optimizer.generate_optimized_variants(youtube_title, named_entity_labels)

        # Use best variant if significantly better
        best_variant = variants[0]
        if best_variant["analysis"]["ctr_score"] > title_analysis["ctr_score"] + 15:
            print(f"  [CTR] Using optimized variant (score: {best_variant['analysis']['ctr_score']}/100)")
            youtube_title = best_variant["title"]
            title_analysis = best_variant["analysis"]
        else:
            print(f"  [CTR] Keeping original title (score: {title_analysis['ctr_score']}/100)")
    else:
        print(f"  [CTR] Title score good ({title_analysis['ctr_score']}/100, grade: {title_analysis['grade']})")

    metadata = {
        "youtube_title": youtube_title,
        "youtube_description": full_description,
        "tags": claude_metadata.get("tags", script.get("tags", [])) if claude_metadata else script.get("tags", []),
        "category": claude_metadata.get("category", "Education") if claude_metadata else "Education",
        "hashtags": claude_metadata.get("hashtags", []) if claude_metadata else ["#経済", "#ビジネス"],
        "timestamps": timestamps,
        "duration_formatted": _format_duration(video_duration_seconds),
        "named_entities": named_entities,
        "title_ctr_analysis": title_analysis,  # Add CTR analysis to metadata
    }

    return metadata


def generate_title_variations(
    topic: str,
    key_points: List[str] = None,
    named_entities: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, str]]:
    """
    Generate multiple title variations

    Args:
        topic: Video topic
        key_points: Key points from content

    Returns:
        List of title variations
    """
    variations = []
    primary_entity = _get_primary_entity(named_entities or [])
    top_key_point = (key_points[0] if key_points else "最新トレンド").replace("\n", "")

    if primary_entity:
        try:
            variations.append({
                "type": "named_entity_focus",
                "title": ContentTemplates.generate_title(
                    topic=topic,
                    template_type="named_entity_focus",
                    entity=primary_entity,
                    action="最新発表",
                    impact=f"{top_key_point[:18]}",
                    announcement=f"{top_key_point[:20]}",
                    rival="競合各社",
                    hook="何が変わる？"
                )
            })
        except Exception as e:
            print(f"Failed to generate named_entity_focus title: {e}")

    # Generate different types
    title_types = ["shock", "question", "number", "how_to"]

    for title_type in title_types:
        try:
            if title_type == "number":
                title = ContentTemplates.generate_title(
                    topic=topic,
                    template_type=title_type,
                    number="5",
                    expert="専門家"
                )
            elif title_type == "question":
                title = ContentTemplates.generate_title(
                    topic=topic,
                    template_type=title_type,
                    outcome="重要なのか",
                    expert="経済学者"
                )
            elif title_type == "how_to":
                title = ContentTemplates.generate_title(
                    topic=topic,
                    template_type=title_type,
                    minutes="10",
                    goal="理解を深める"
                )
            else:
                title = ContentTemplates.generate_title(
                    topic=topic,
                    template_type=title_type,
                    key_point=key_points[0] if key_points else "重要ポイント"
                )

            variations.append({
                "type": title_type,
                "title": title
            })
        except Exception as e:
            print(f"Failed to generate {title_type} title: {e}")

    return variations


def generate_engagement_comments(
    script: Dict[str, Any],
    count: int = 5
) -> List[str]:
    """
    Generate engagement comments using templates

    Args:
        script: Video script
        count: Number of comments to generate

    Returns:
        List of comments
    """
    import random

    title = script.get("title", "")
    dialogues = script.get("dialogues", [])

    comments = []
    comment_types = list(ContentTemplates.COMMENT_TEMPLATES.keys())

    for i in range(min(count, len(comment_types))):
        comment_type = comment_types[i]
        templates = ContentTemplates.COMMENT_TEMPLATES[comment_type]
        template = random.choice(templates)

        # Try to fill in template with context
        try:
            if comment_type == "insightful":
                comment = template.format(
                    insight="重要なポイント",
                    related_point="関連する視点",
                    timestamp="3:45",
                    personal_experience="自分も同じ経験があります"
                )
            elif comment_type == "emotional":
                comment = template.format(
                    specific_problem="この問題で困ってました",
                    surprising_element="この事実",
                    what_would_change="もっと早く対策できたのに"
                )
            elif comment_type == "experience":
                comment = template.format(
                    specific_situation="同じ状況になって",
                    outcome="良い結果が出ました",
                    result="成功",
                    lesson_learned="勉強になりました",
                    action="試してみた",
                    unexpected_result="予想以上の効果がありました"
                )
            elif comment_type == "question":
                comment = template.format(
                    different_scenario="別のケース",
                    specific_question="気になります",
                    related_topic="関連分野",
                    follow_up_question="教えてください",
                    detail="この部分"
                )
            else:  # appreciation
                comment = template.format(
                    specific_praise="めちゃくちゃ参考になりました",
                    value_statement="すごく役立つ情報です",
                    specific_element="説明の仕方"
                )

            comments.append(comment)
        except Exception as e:
            # Fallback to simple comment
            comments.append(f"{title}、とても勉強になりました！")

    return comments


def _format_duration(seconds: float) -> str:
    """Format duration to human-readable format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}分{secs}秒"


def _get_primary_entity(named_entities: List[Dict[str, Any]]) -> Optional[str]:
    for entity in named_entities:
        label = entity.get("label")
        if label:
            return label
    return None


def _enforce_named_entity_prefix(title: str, entity: Optional[str]) -> str:
    if not entity:
        return title or ""

    if not title:
        return f"{entity} 最新トピック"

    stripped = title.strip()
    if stripped.lower().startswith(entity.lower()):
        return stripped

    pattern = re.compile(re.escape(entity), re.IGNORECASE)
    stripped_without_entity = pattern.sub("", stripped, count=1).strip(" -|：:、")
    if stripped_without_entity:
        return f"{entity} {stripped_without_entity}"
    return entity


if __name__ == "__main__":
    # Test
    test_script = {
        "title": "円安の影響と今後の見通し",
        "description": "円安について解説",
        "dialogues": [
            {"speaker": "A", "text": "今日は円安について話します"},
            {"speaker": "B", "text": "お願いします"}
        ],
        "tags": ["経済", "為替", "円安"]
    }

    test_timing = [
        {"speaker": "A", "text": "test", "start": 0, "end": 5},
        {"speaker": "B", "text": "test", "start": 5, "end": 10}
    ]

    metadata = generate_complete_metadata(
        script=test_script,
        timing_data=test_timing,
        video_duration_seconds=600
    )

    print("Generated Metadata:")
    print(f"Title: {metadata['youtube_title']}")
    print(f"\nDescription:\n{metadata['youtube_description']}")
    print(f"\nTimestamps: {len(metadata['timestamps'])}")

    # Test title variations
    variations = generate_title_variations("円安の影響")
    print("\nTitle Variations:")
    for v in variations:
        print(f"  [{v['type']}] {v['title']}")
