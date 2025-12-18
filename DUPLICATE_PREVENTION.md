# 重複トピック防止機能

## 概要

同じニュース記事を複数回動画化することを防ぐために、トピック履歴管理システムを実装しました。

## 機能

### 1. トピック履歴の記録

動画生成が成功するたびに、以下の情報を `outputs/history/used_topics.json` に記録します：

- トピックタイトル
- メインURL
- ソースURL一覧
- 生成日時

### 2. 重複チェック

新しいトピックを選択する際、以下の条件で重複をチェックします：

**URLベースのチェック:**
- 過去に使用したURLと完全一致する場合は重複と判定

**タイトル類似度チェック:**
- タイトルのキーワード（4文字以上）を抽出
- 70%以上のキーワードが重複している場合は重複と判定

### 3. 自動クリーンアップ

- 30日以上前のトピック履歴は自動的に削除されます
- ストレージの節約と関連性の維持

## 実装ファイル

### `topic_history.py`

トピック履歴管理の中核モジュール：

```python
# 主要関数
load_topic_history()           # 履歴をロード
save_topic_history(history)    # 履歴を保存
clean_old_history(history)     # 古い履歴を削除
is_duplicate_topic(url, title, history)  # 重複チェック
filter_duplicate_topics(topics, history) # リストから重複を除外
add_topic_to_history(title, url, source_urls)  # 履歴に追加
```

### `web_search.py`

検索結果のフィルタリング：

```python
def search_latest_ai_news(max_results: int = 15):
    # ... 検索実行 ...

    # 重複フィルタリング
    history = load_topic_history()
    history = clean_old_history(history)
    filtered_results = filter_duplicate_topics(results, history)

    return filtered_results
```

### `advanced_video_pipeline.py`

動画生成成功時に履歴に追加：

```python
# 動画生成完了後
add_topic_to_history(
    title=topic_title,
    url=topic_url,
    source_urls=source_urls
)
```

## 履歴ファイル構造

`outputs/history/used_topics.json`:

```json
{
  "topics": [
    {
      "title": "【AI覇権争奪戦】OpenAI vs Google激化！ディズニーも参戦",
      "url": "https://apnews.com/article/disney-openai-sora-ai...",
      "source_urls": [
        "https://www.nytimes.com/2025/12/11/technology/...",
        "https://www.bloomberg.com/news/articles/2025-12-11/..."
      ],
      "date": "2025-12-13T20:30:00.123456"
    }
  ]
}
```

## 動作フロー

1. **Web検索実行** (`search_latest_ai_news()`)
   - Serper APIで最新AIニュースを取得
   - 10-15件のニュース記事を取得

2. **重複チェック** (`filter_duplicate_topics()`)
   - 過去30日間の履歴をロード
   - URLとタイトルで重複を判定
   - 重複記事を除外

3. **トピック選択** (`select_topic_with_claude()`)
   - フィルタリング済みのリストから最適なトピックを選択

4. **動画生成** (`generate_single_video()`)
   - スクリプト生成、動画作成、YouTubeアップロード

5. **履歴に追加** (`add_topic_to_history()`)
   - 生成成功時に自動的に履歴に追加
   - 次回以降の重複を防止

## 例：重複検出

### ケース1: URL完全一致

```
過去: https://apnews.com/article/disney-openai-sora-...
新規: https://apnews.com/article/disney-openai-sora-...
→ 重複と判定、除外
```

### ケース2: タイトル類似度70%以上

```
過去: 「OpenAI vs Google激化！ディズニーも参戦」
新規: 「ディズニーがOpenAIに参戦！Google vs OpenAI戦争」
共通キーワード: OpenAI, Google, ディズニー, 参戦
類似度: 4/4 = 100% → 重複と判定、除外
```

### ケース3: 異なるトピック

```
過去: 「OpenAI vs Google激化！ディズニーも参戦」
新規: 「Meta、新AI チップ発表で市場席巻」
共通キーワード: なし
類似度: 0% → 重複なし、選択可能
```

## テスト

### 履歴の確認

```bash
# 履歴ファイルの内容を表示
cat outputs/history/used_topics.json

# Python モジュールのテスト実行
docker compose run --rm ai-video-bot python topic_history.py
```

### 手動テスト

```python
from topic_history import *

# 履歴をロード
history = load_topic_history()
print(f"記録されているトピック数: {len(history['topics'])}")

# 使用済みURLを表示
urls = get_used_urls(history)
for url in list(urls)[:5]:
    print(f"  - {url}")

# 重複チェック
is_dup = is_duplicate_topic(
    "https://apnews.com/article/disney-openai-sora-...",
    "ディズニーがOpenAIに投資",
    history
)
print(f"重複: {is_dup}")
```

## トラブルシューティング

### 履歴ファイルが見つからない

初回実行時は自動的に作成されます。問題ありません。

### 重複が検出されない

1. 履歴ファイルの確認:
   ```bash
   cat outputs/history/used_topics.json
   ```

2. タイトル正規化の確認:
   - 短いキーワード（3文字以下）は無視されます
   - 大文字小文字は区別されません

### 誤検出（重複でないのに除外される）

タイトル類似度の閾値（現在70%）を調整:

```python
# topic_history.py の is_duplicate_topic() 関数内
if similarity > 0.7:  # ← この値を調整（0.7 = 70%）
    return True
```

## メンテナンス

### 履歴の手動削除

```bash
# 全履歴を削除
rm outputs/history/used_topics.json

# 特定のトピックを削除
# used_topics.json を編集して該当のトピックを削除
```

### 履歴保存期間の変更

```python
# topic_history.py
HISTORY_DAYS = 30  # ← デフォルト30日、任意の日数に変更可能
```

## 今後の改善案

1. **類似度アルゴリズムの改善**
   - TF-IDFやコサイン類似度の導入
   - より高精度な重複検出

2. **カテゴリ別管理**
   - ai_news, technology, economicsなど、カテゴリごとに履歴を管理

3. **手動除外リスト**
   - 特定のキーワードやソースを手動で除外

4. **統計情報の表示**
   - 重複除外率のレポート
   - 人気トピックの分析
