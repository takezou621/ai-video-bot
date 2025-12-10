"""
Content Templates System
Automates content structure, scenario building, and metadata generation
Based on successful YouTube video patterns
"""
from typing import Dict, Any, List
import json


class ContentTemplates:
    """
    Comprehensive template system for YouTube video content
    """

    # Script Structure Templates
    SCRIPT_STRUCTURES = {
        "standard": {
            "name": "標準構造",
            "sections": [
                {
                    "type": "hook",
                    "duration_percent": 5,
                    "purpose": "最初の15秒で視聴者を引き込む",
                    "templates": [
                        "【衝撃】実は、{topic}について、みんなが知らない事実があるんです...",
                        "これを知らないと損する！{topic}の真実とは？",
                        "今日は{topic}について、目からウロコの話をします",
                        "ちょっと待って！{topic}、実はこんなことになってるって知ってました？"
                    ]
                },
                {
                    "type": "intro",
                    "duration_percent": 10,
                    "purpose": "トピックの紹介と視聴者への価値提示",
                    "templates": [
                        "今日は{topic}について、わかりやすく解説していきます",
                        "この動画では{key_points}について詳しくお話しします",
                        "最後まで見ると、{benefit}がわかります"
                    ]
                },
                {
                    "type": "problem",
                    "duration_percent": 15,
                    "purpose": "問題提起・現状の課題",
                    "templates": [
                        "実は、{topic}にはこんな問題があります",
                        "多くの人が{misconception}と誤解していますが...",
                        "{topic}で失敗する人の共通点とは？"
                    ]
                },
                {
                    "type": "explanation",
                    "duration_percent": 40,
                    "purpose": "メインコンテンツ・詳細解説",
                    "key_elements": [
                        "具体例を3つ以上",
                        "数字・データを使用",
                        "比喩やストーリーで説明",
                        "視聴者の「なぜ？」に答える"
                    ]
                },
                {
                    "type": "solution",
                    "duration_percent": 20,
                    "purpose": "解決策・アクションプラン",
                    "templates": [
                        "では、具体的にどうすればいいのか？",
                        "ここからが重要です。{action_steps}",
                        "明日から使える実践的な方法をご紹介します"
                    ]
                },
                {
                    "type": "summary",
                    "duration_percent": 8,
                    "purpose": "まとめ・重要ポイントの再確認",
                    "templates": [
                        "今日のポイントをまとめると...",
                        "覚えておいてほしいのは、この3つです",
                        "最後にもう一度、重要なポイントを振り返ります"
                    ]
                },
                {
                    "type": "cta",
                    "duration_percent": 2,
                    "purpose": "チャンネル登録促進",
                    "templates": [
                        "この動画が役に立ったら、ぜひチャンネル登録と高評価をお願いします！",
                        "次回は{next_topic}について解説するので、お楽しみに！",
                        "コメント欄で、あなたの意見も聞かせてください！"
                    ]
                }
            ]
        },
        "problem_solution": {
            "name": "問題解決型",
            "sections": [
                {"type": "hook", "duration_percent": 5},
                {"type": "problem_deep_dive", "duration_percent": 25},
                {"type": "root_cause", "duration_percent": 20},
                {"type": "solution_steps", "duration_percent": 35},
                {"type": "results", "duration_percent": 10},
                {"type": "cta", "duration_percent": 5}
            ]
        },
        "comparison": {
            "name": "比較・対比型",
            "sections": [
                {"type": "hook", "duration_percent": 5},
                {"type": "intro_options", "duration_percent": 10},
                {"type": "option_a", "duration_percent": 25},
                {"type": "option_b", "duration_percent": 25},
                {"type": "comparison", "duration_percent": 25},
                {"type": "recommendation", "duration_percent": 8},
                {"type": "cta", "duration_percent": 2}
            ]
        },
        "story_based": {
            "name": "ストーリー型",
            "sections": [
                {"type": "hook", "duration_percent": 5},
                {"type": "story_intro", "duration_percent": 10},
                {"type": "conflict", "duration_percent": 20},
                {"type": "turning_point", "duration_percent": 20},
                {"type": "resolution", "duration_percent": 25},
                {"type": "lesson", "duration_percent": 15},
                {"type": "cta", "duration_percent": 5}
            ]
        }
    }

    # Title Templates
    TITLE_TEMPLATES = {
        "shock": [
            "【衝撃】{topic}の真実｜{key_point}",
            "知らないと損！{topic}の{surprising_fact}",
            "まさか...{topic}が{unexpected_result}だった件"
        ],
        "named_entity_focus": [
            "{entity}が{action}！{impact}",
            "{entity}最新{topic}で業界激変",
            "【速報】{entity}が{announcement}",
            "{entity} vs {rival}｜{hook}",
        ],
        "question": [
            "なぜ{topic}は{outcome}なのか？｜{expert}が解説",
            "{topic}で成功する人・失敗する人の違いとは？",
            "どうして{misconception}と思われているのか？"
        ],
        "number": [
            "{topic}で失敗する人の{number}つの共通点",
            "{topic}を{number}分で理解する方法",
            "{expert}が教える{topic}の{number}つの秘訣"
        ],
        "comparison": [
            "{option_a} vs {option_b}｜どっちが正解？",
            "{topic}を比較してわかった驚きの結果",
            "結局どっち？{topic}の選び方を徹底解説"
        ],
        "how_to": [
            "{topic}の正しいやり方｜{minutes}分で完全理解",
            "初心者でもできる{topic}の始め方",
            "{goal}を実現する{topic}の実践テクニック"
        ],
        "warning": [
            "要注意！{topic}でやってはいけない{number}つのこと",
            "これだけは避けて！{topic}の落とし穴",
            "{topic}で失敗したくない人へ｜{expert}からの警告"
        ]
    }

    # Description Templates
    DESCRIPTION_STRUCTURE = {
        "opening": [
            "この動画では、{topic}について{angle}で詳しく解説します。",
            "{topic}に興味がある方、{concern}で悩んでいる方は必見です！",
            "今回は{expert_perspective}から{topic}を分析していきます。"
        ],
        "what_you_learn": [
            "\n📚 この動画で学べること：",
            "✅ {point_1}",
            "✅ {point_2}",
            "✅ {point_3}",
            "✅ {point_4}",
            "✅ {point_5}"
        ],
        "timestamps": [
            "\n⏱️ タイムスタンプ：",
            "{timestamps}"
        ],
        "who_should_watch": [
            "\n👥 こんな人におすすめ：",
            "・{target_audience_1}",
            "・{target_audience_2}",
            "・{target_audience_3}"
        ],
        "call_to_action": [
            "\n🔔 チャンネル登録がまだの方は、ぜひ登録をお願いします！",
            "👍 この動画が役に立ったら、高評価とコメントをいただけると嬉しいです。",
            "📢 次回は{next_topic}について解説予定です！"
        ],
        "related_content": [
            "\n📌 関連動画：",
            "▶︎ {related_video_1}",
            "▶︎ {related_video_2}"
        ],
        "hashtags": [
            "\n{hashtags}"
        ],
        "disclaimer": [
            "\n⚠️ 免責事項：",
            "この動画の内容は情報提供を目的としており、{disclaimer_text}"
        ]
    }

    # Comment Templates (for seeding engagement)
    COMMENT_TEMPLATES = {
        "insightful": [
            "この視点は見落としがちだけど、実は{insight}なんですよね。{related_point}も考えると面白いです。",
            "{timestamp}の説明、めちゃくちゃ分かりやすかった！{personal_experience}",
            "実はこれ、{related_field}とも関連してて、{connection}という研究結果もあります。"
        ],
        "emotional": [
            "まさに今これで悩んでました...！{specific_problem}",
            "え、知らなかった...{surprising_element}だったんですね。衝撃です。",
            "これ、もっと早く知りたかった...😭 {what_would_change}"
        ],
        "experience": [
            "うちの会社でもまさにこの状況で、{specific_situation}。{outcome}でした。",
            "去年これやって{result}した経験あります。{lesson_learned}",
            "実際に{action}してみたら、{unexpected_result}でびっくりしました。"
        ],
        "question": [
            "じゃあ{different_scenario}の場合はどうなんですか？{specific_question}",
            "これって{related_topic}にも適用できますか？{follow_up_question}",
            "{detail}についてもっと詳しく知りたいです！次回取り上げてくれませんか？"
        ],
        "appreciation": [
            "この説明分かりやすすぎて草。{specific_praise}",
            "なんで学校でこれ教えてくれないの😂 {value_statement}",
            "毎回クオリティ高すぎる...{specific_element}が特に良かったです！"
        ]
    }

    # Dialogue Exchange Patterns
    DIALOGUE_PATTERNS = {
        "introduction": [
            {
                "speaker": "A",
                "pattern": "今日は{topic}について話していきますね。",
                "variations": [
                    "今回のテーマは{topic}です。",
                    "さて、今日は{topic}を深掘りしていきます。"
                ]
            },
            {
                "speaker": "B",
                "pattern": "お、これは気になるテーマですね！",
                "variations": [
                    "おぉ、ちょうど知りたかったやつだ！",
                    "これ、タイムリーな話題ですね。"
                ]
            }
        ],
        "surprise": [
            {
                "speaker": "A",
                "pattern": "実は、{surprising_fact}なんです。"
            },
            {
                "speaker": "B",
                "pattern": "え、マジですか！？それは知らなかった...",
                "variations": [
                    "そうなんですか！？意外すぎる...",
                    "えー！それは驚きですね。"
                ]
            }
        ],
        "explanation": [
            {
                "speaker": "A",
                "pattern": "具体的には、{explanation}ということです。"
            },
            {
                "speaker": "B",
                "pattern": "なるほど...つまり{rephrasing}ってことですね？",
                "variations": [
                    "ああ、そういうことか！{understanding}",
                    "理解しました。{clarification}"
                ]
            }
        ],
        "transition": [
            {
                "speaker": "B",
                "pattern": "じゃあ、{next_question}はどうなんですか？"
            },
            {
                "speaker": "A",
                "pattern": "いい質問ですね。それについては..."
            }
        ],
        "concern": [
            {
                "speaker": "B",
                "pattern": "でも、{concern}ということはないんですか？"
            },
            {
                "speaker": "A",
                "pattern": "確かにその懸念はありますよね。ただ、{counter_point}"
            }
        ]
    }

    @staticmethod
    def generate_script_structure(
        topic: str,
        duration_minutes: int,
        structure_type: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate a structured script outline

        Args:
            topic: Video topic
            duration_minutes: Target duration
            structure_type: Type of structure to use

        Returns:
            Structured script outline
        """
        structure = ContentTemplates.SCRIPT_STRUCTURES.get(
            structure_type,
            ContentTemplates.SCRIPT_STRUCTURES["standard"]
        )

        sections = []
        for section in structure["sections"]:
            duration_seconds = (duration_minutes * 60) * (section["duration_percent"] / 100)
            sections.append({
                "type": section["type"],
                "duration_seconds": duration_seconds,
                "purpose": section.get("purpose", ""),
                "templates": section.get("templates", []),
                "key_elements": section.get("key_elements", [])
            })

        return {
            "structure_name": structure["name"],
            "total_duration": duration_minutes * 60,
            "sections": sections
        }

    @staticmethod
    def generate_title(
        topic: str,
        template_type: str = "shock",
        **kwargs
    ) -> str:
        """
        Generate engaging title from template

        Args:
            topic: Video topic
            template_type: Type of title template
            **kwargs: Template variables

        Returns:
            Generated title
        """
        import random

        templates = ContentTemplates.TITLE_TEMPLATES.get(
            template_type,
            ContentTemplates.TITLE_TEMPLATES["shock"]
        )

        template = random.choice(templates)

        # Fill in template
        variables = {"topic": topic, **kwargs}
        try:
            title = template.format(**variables)
        except KeyError:
            # If template variables are missing, use simple format
            title = f"{topic}について解説"

        return title

    @staticmethod
    def generate_description(
        title: str,
        topic: str,
        key_points: List[str],
        timestamps: List[Dict],
        **kwargs
    ) -> str:
        """
        Generate comprehensive video description

        Args:
            title: Video title
            topic: Video topic
            key_points: Main points covered
            timestamps: List of timestamps
            **kwargs: Additional template variables

        Returns:
            Generated description
        """
        import random

        desc_parts = []

        # Opening
        opening_template = random.choice(
            ContentTemplates.DESCRIPTION_STRUCTURE["opening"]
        )
        desc_parts.append(opening_template.format(
            topic=topic,
            angle=kwargs.get("angle", "分かりやすく"),
            concern=kwargs.get("concern", "この問題"),
            expert_perspective=kwargs.get("expert_perspective", "専門家の視点")
        ))

        # What you learn
        desc_parts.append(
            ContentTemplates.DESCRIPTION_STRUCTURE["what_you_learn"][0]
        )
        for i, point in enumerate(key_points[:5], 1):
            desc_parts.append(f"✅ {point}")

        # Timestamps
        if timestamps:
            desc_parts.append(
                ContentTemplates.DESCRIPTION_STRUCTURE["timestamps"][0]
            )
            for ts in timestamps:
                time_str = _format_timestamp(ts["time"])
                desc_parts.append(f"{time_str} {ts['label']}")

        # Who should watch
        if "target_audiences" in kwargs:
            desc_parts.append(
                ContentTemplates.DESCRIPTION_STRUCTURE["who_should_watch"][0]
            )
            for audience in kwargs["target_audiences"]:
                desc_parts.append(f"・{audience}")

        # Call to action
        desc_parts.extend([
            ContentTemplates.DESCRIPTION_STRUCTURE["call_to_action"][0],
            ContentTemplates.DESCRIPTION_STRUCTURE["call_to_action"][1],
            ContentTemplates.DESCRIPTION_STRUCTURE["call_to_action"][2].format(
                next_topic=kwargs.get("next_topic", "関連トピック")
            )
        ])

        # Hashtags
        if "hashtags" in kwargs:
            hashtags = " ".join(kwargs["hashtags"])
            desc_parts.append(f"\n{hashtags}")

        return "\n".join(desc_parts)

    @staticmethod
    def generate_timestamps(
        script: Dict[str, Any],
        timing_data: List[Dict]
    ) -> List[Dict]:
        """
        Generate timestamps from script timing

        Args:
            script: Script with dialogues
            timing_data: Timing information

        Returns:
            List of timestamps with labels
        """
        timestamps = []

        # Analyze dialogue to detect section changes
        dialogues = script.get("dialogues", [])

        # Opening
        timestamps.append({
            "time": 0,
            "label": "オープニング"
        })

        # Try to detect sections based on content
        current_time = 0
        section_markers = [
            ("問題提起", ["問題", "課題", "悩み"]),
            ("詳しく解説", ["具体的", "詳しく", "例えば"]),
            ("解決策", ["方法", "やり方", "どうすれば"]),
            ("まとめ", ["まとめ", "ポイント", "重要"])
        ]

        for i, dialogue in enumerate(dialogues):
            text = dialogue.get("text", "")

            for label, keywords in section_markers:
                if any(kw in text for kw in keywords):
                    # Find timing for this dialogue
                    if i < len(timing_data):
                        timestamps.append({
                            "time": timing_data[i]["start"],
                            "label": label
                        })
                    break

        return timestamps


def _format_timestamp(seconds: float) -> str:
    """Format seconds to MM:SS or HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    # Test
    templates = ContentTemplates()

    # Test script structure
    structure = templates.generate_script_structure(
        topic="円安の影響",
        duration_minutes=10
    )
    print("Script Structure:")
    print(json.dumps(structure, ensure_ascii=False, indent=2))

    # Test title generation
    title = templates.generate_title(
        topic="円安",
        template_type="number",
        number="5",
        expert="経済学者"
    )
    print(f"\nGenerated Title: {title}")

    # Test description
    description = templates.generate_description(
        title=title,
        topic="円安の影響",
        key_points=[
            "円安のメカニズム",
            "輸出企業への影響",
            "私たちの生活への影響"
        ],
        timestamps=[
            {"time": 0, "label": "オープニング"},
            {"time": 60, "label": "円安とは？"},
            {"time": 180, "label": "メリット・デメリット"}
        ]
    )
    print(f"\nGenerated Description:\n{description}")
