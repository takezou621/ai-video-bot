# Competitive YouTube Research (2025-12-10)

## Objectives
- Identify AI/テック解説ジャンルで高成長中または規模が大きいチャンネルの成功要因
- どのようなコンテンツ設計・制作ワークフローが再生数や登録者を押し上げているかを整理
- 本リポジトリの動画品質改善タスクへ落とし込むためのエビデンスを準備

## Key Findings
- **ストーリードリブン + 時事性**: ColdFusionやAI Explainedは、最新ニュースや企業動向をドキュメンタリー調で語り、15分前後の長尺で65万回以上の平均再生を確保。
- **固有名詞フック**: NVIDIA、OpenAI、Apple、Grokなど特定ブランドをタイトル・サムネ先頭に置くことでCTRを押し上げている（AI Explained / Two Minute Papers）。
- **冒頭15秒の価値約束**: Matt Wolfeの長編やAI Andyのデイリー配信では、冒頭で視聴者メリットを即提示し視聴維持率50%前後を狙う構成になっている。
- **章立て＆タイムスタンプ文化**: AI Andyは毎日4〜5章構成のニュースを同じ型で提供し、説明欄にも章リンクを掲載。視聴習慣とリピート率が向上。
- **ショートとの役割分担**: 長編で深い洞察、Shortsで露出拡大というハイブリッド投稿がMatt Wolfeなどで機能。Shortsは再生単価は低いがアルゴリズムへのシグナルになる。
- **視覚演出の差別化**: ColdFusionはB-roll、図版、テロップが多層構成で、単調な生成動画との差額を作っている。視聴者は「AI slop」と呼ばれるテンプレ動画を避ける傾向。一次ソースを明記することが信頼構築に直結。

## Channel Benchmarks
| Channel | Subscribers (2025-12-10) | Avg Views / Recent Long-form | Cadence | Notable Formats |
| --- | --- | --- | --- | --- |
| ColdFusion | 5.11M | ~655K (15-18分) | 週1–2本 | ドキュメンタリー調、B-roll＋図解、企業ヒストリー特化 |
| Matt Wolfe | 855K | 113K (長編28本直近) | 週3本 + Shorts | 最新AIツールの「◯◯でできる27のこと」型、ライブ配信あり |
| AI Explained | 383K | 160–190K (8–10分) | 週2–3本 | 緊急性を強調したタイトル、固有名詞フック |
| Two Minute Papers | 1.75M | 200K+ (5–8分) | 週1–2本 | 研究速報、感情的ナレーション、「What a time to be alive!」サインオフ |
| AI Andy | 211K | 155K/日 (ニュースまとめ) | デイリー | 章立てニュース、視聴者ナビゲーション強化 |

*ソース: 公開チャンネル統計 (SocialBlade / YT Studio 公開情報) を2025-12-10に手動採取。

## Format Insights
### ドキュメンタリー風ストーリーテリング (ColdFusion系)
- 章立て: 背景 → 問題 → 決定的瞬間 → 未来予測
- 映像: B-roll, ロゴアニメ, グラフ画像の多層合成
- 音声: ローキーなナレーション＋BGMを章ごとに切替

### ニュース速達 + 章ステッキ (AI Andy系)
- フック: 「今日の3つのAIニュースで〇〇が変わる」
- 章タイトルを画面下に常時表示し、説明欄でもリンク化
- テキストオーバーレイはブランドカラー固定で安心感を演出

### 専門分解 + 固有名詞フック (AI Explained / Two Minute Papers)
- 固有名詞をタイトルの最初に配置（例: “NVIDIA Just Solved…”）
- 台本は「ニュース→実験内容→市場インパクト→行動提案」構成
- グラフィック: Figure引用 + ハイライト枠で要点を示す

### ハイブリッド投稿 (Matt Wolfe)
- 長編: 12–18分、深掘り＋ツール一覧
- Shorts: 長編から切り出した“1ツール1Tips”を縦型で再レンダリング
- 週次ライブでコミュニティ活性 & 質問を次動画へ反映

## Recommended Tasks for ai-video-bot
1. **トピック優先度スコアリング**
   - `web_search.py`のトピック抽出結果に固有名詞タグと最新性スコアを付与。
   - 例: `score = interest_weight * keyword_priority + freshness_weight * hours_since_news`。
2. **冒頭フック用テンプレート拡張**
   - `content_templates.py`に「問題提起→データ→約束」の3文テンプレを追加し、全スクリプトの冒頭に強制挿入。
3. **章立てメタデータのリッチ化**
   - `metadata_generator.py`でタイムスタンプ生成時に章タイトル＋洞察コメントを生成し、説明欄と固定コメントの双方に書き出す。
4. **B-roll/図版レイヤーの自動挿入**
   - `video_maker_moviepy.py`にB-rollトラックを追加し、`assets/`以下のストック映像または自動生成サムネをインサートできるようにする。
   - 章タイトルごとのカラー定義を`assets/style.json`等で管理。
5. **Shorts自動派生ジョブ**
   - 長編生成後に、`outputs/.../script.json`からハイライト区間を抽出して縦型レイアウトで再レンダリングするスクリプトを新設。
6. **一次ソースリンクの自動添付**
   - `web_search.py`で取得したニュースURLを`metadata_generator.py`へ渡し、説明欄末尾に“Sources”セクションを必ず挿入。
7. **視聴維持率トラッキング設計**
   - `tracking.py`へYouTube Analytics APIを連携し、章ごとのドロップオフをCSV/シートに蓄積。テンプレ改善にフィードバック。

## Next Steps
- 優先度: (1)トピックスコア → (2)冒頭フック → (3)章立てメタ → (4)B-roll → (5)Shorts派生。
- それぞれをチケット化して工数・依存関係を明示。
- 週次で改善結果をダッシュボード化し、視聴維持率とCTRを追う。

## References
- ColdFusion, Matt Wolfe, AI Explained, Two Minute Papers, AI Andy 各チャンネル (YouTube / SocialBlade) Accessed 2025-12-10.
- 視聴者の「AI slop」批判に関する報道 (The Verge, 2024-11)。
