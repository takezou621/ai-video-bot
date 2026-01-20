# systemd Timerのlinger設定依頼

## 目的

毎朝7:00にAIニュース動画を自動生成するsystemd Timerを設定しましたが、ログアウト後も実行されるようにlingerを有効にする必要があります。

## 依頼内容

以下のコマンドを管理者(root権限)が実していただけますか？

```bash
sudo loginctl enable-linger kawai
```

## 確認コマンド

実行後、以下のコマンドで確認できます：

```bash
loginctl show-user kawai
```

`Linger=yes` になっていれば成功です。

## lingerとは

lingerを有効にすると、ユーザーがログアウトした後もsystemdユーザーセッションが維持され、バックグラウンドのサービスやタイマーが実行され続けます。

## 現在の状況

- ✅ systemd Timerは設定済み
- ✅ スケジュール: 毎日22:00 UTC（日本時間翌朝7:00）
- ⚠️ linger: 未設定（管理者権限が必要）

## 代替案

lingerを有効にできない場合は、以下の対応があります：

1. **常にログインしたままにする**（screen/tmuxを使用）
2. **GitHub Actionsに切り替える**（リモート実行）
3. **手動実行**（毎朝7:00に手動でスクリプトを実行）

## 連絡先

- ユーザー: kawai
- サービス: daily-video.timer
- ファイル: ~/.config/systemd/user/daily-video.timer
