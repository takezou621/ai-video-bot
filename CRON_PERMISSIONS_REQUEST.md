# cron権限問題の解決依頼

## 問題の概要

毎朝7:00にAIニュース動画を自動生成するためにcronを設定しようとしたところ、権限の問題で設定できませんでした。

## 問題の詳細

```bash
$ crontab -l
/var/spool/cron/: mkstemp: Permission denied

/var/spool/cron/: Permission denied
```

現在の権限:
- `/var/spool/cron/` の所有者: `100000:100000`（Dockerコンテナのroot？）
- `/var/spool/cron/crontabs/` の所有者: `root:crontab`

## 解決に必要なコマンド

以下のコマンドを管理者(root権限)が実していただけますか？

```bash
# 権限修正スクリプトの実行
sudo bash /home/kawai/dev/ai-video-bot/fix-cron-permissions.sh
```

または、手動で以下を実行：

```bash
# 1. ディレクトリの確認
sudo ls -ld /var/spool/cron/

# 2. 権限の修正
sudo mkdir -p /var/spool/cron/crontabs
sudo chmod 755 /var/spool/cron
sudo chmod 1733 /var/spool/cron/crontabs

# 3. 所有者の設定
sudo chown root:crontab /var/spool/cron /var/spool/cron/crontabs

# 4. ユーザー用crontabファイルの作成
sudo touch /var/spool/cron/crontabs/kawai
sudo chmod 600 /var/spool/cron/crontabs/kawai
sudo chown kawai:crontab /var/spool/cron/crontabs/kawai

# 5. 確認
ls -ld /var/spool/cron/
ls -ld /var/spool/cron/crontabs/
ls -l /var/spool/cron/crontabs/kawai
```

## 実行後の確認

権限修正後、以下のコマンドでcrontabを設定できます：

```bash
# crontabの設定
(crontab -l 2>/dev/null; echo '# 毎朝7:00にAIニュース動画を生成してYouTubeに公開'; echo '0 7 * * * cd /home/kawai/dev/ai-video-bot && ./cron-job.sh >> logs/cron.log 2>&1') | crontab -

# 設定の確認
crontab -l
```

## 原因

Dockerコンテナ内からcronを操作した際、所有者が`100000:100000`（DockerのUID/GID）になってしまった可能性があります。

## 回避策（権限修正が難しい場合）

権限修正が難しい場合は、以下の代替案があります：

1. **systemd Timerを使う**（ユーザー権限で可能）
2. **GitHub Actionsを使う**（リモート実行）
3. **一時的に手動実行**（毎朝7:00に手動で実行）

詳細は `ALTERNATIVE_SETUP.md` を参照してください。

## 連絡先

- ユーザー: kawai
- プロジェクト: ai-video-bot
- 場所: `/home/kawai/dev/ai-video-bot`
