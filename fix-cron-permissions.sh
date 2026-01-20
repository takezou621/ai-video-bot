#!/bin/bash
# cronの権限問題を解決するためのスクリプト
# 管理者(root権限)が実行する必要があります

echo "=== cronの権限問題を解決 ==="
echo ""
echo "このスクリプトはroot権限で実行する必要があります。"
echo ""
echo "問題の分析:"
echo "  /var/spool/cron/ ディレクトリへの書き込み権限がない"
echo "  /var/spool/cron/crontabs/kawai/ ディレクトリへの書き込み権限がない"
echo ""
echo "解決方法:"
echo "  1. crontabsディレクトリの権限を修正"
echo "  2. 所有者を適切に設定"
echo ""

# 現在の権限を確認
echo "現在の権限:"
ls -ld /var/spool/cron/ 2>/dev/null || echo "  /var/spool/cron/ が見つかりません"
ls -ld /var/spool/cron/crontabs/ 2>/dev/null || echo "  /var/spool/cron/crontabs/ が見つかりません"
echo ""

# 管理者に実行してほしいコマンドを表示
echo "管理者に実行してほしいコマンド:"
echo "-----------------------------------"
echo "# crontabsディレクトリが存在することを確認"
echo "sudo ls -ld /var/spool/cron/"
echo ""
echo "# 権限を修正（crontabsディレクトリを作成）"
echo "sudo mkdir -p /var/spool/cron/crontabs"
echo "sudo chmod 755 /var/spool/cron"
echo "sudo chmod 1733 /var/spool/cron/crontabs"
echo ""
echo "# 所有者を設定（必要な場合）"
echo "sudo chown root:crontab /var/spool/cron /var/spool/cron/crontabs"
echo ""
echo "# ユーザー用のcrontabファイルを作成"
echo "sudo touch /var/spool/cron/crontabs/kawai"
echo "sudo chmod 600 /var/spool/cron/crontabs/kawai"
echo "sudo chown kawai:crontab /var/spool/cron/crontabs/kawai"
echo "-----------------------------------"
echo ""

# 簡易的なテスト
echo "権限のテスト:"
if [ -w /var/spool/cron/ ]; then
    echo "  ✅ /var/spool/cron/ に書き込み可能"
else
    echo "  ❌ /var/spool/cron/ に書き込み不可（管理者に権限修正が必要）"
fi

if [ -w /var/spool/cron/crontabs/ ]; then
    echo "  ✅ /var/spool/cron/crontabs/ に書き込み可能"
else
    echo "  ❌ /var/spool/cron/crontabs/ に書き込み不可（管理者に権限修正が必要）"
fi
echo ""

# crontabコマンドのテスト
echo "crontabコマンドのテスト:"
if crontab -l >/dev/null 2>&1; then
    echo "  ✅ crontabコマンドが正常に動作します"
else
    echo "  ❌ crontabコマンドが失敗します（管理者に権限修正が必要）"
fi
echo ""

# 一時的な回避策の提案
echo "回避策（権限問題が解決するまで）:"
echo "  1. systemd Timerを使う（Linux標準、ユーザー権限で可能）"
echo "  2. GitHub Actionsを使う（リモート実行）"
echo "  3. 手動実行（毎朝7:00に手動でスクリプトを実行）"
echo ""

# 権限修正のリクエストを作成
cat > /tmp/fix_cron_permissions.sh << 'EOF'
#!/bin/bash
# 管理者用：cron権限修正スクリプト

echo "cron権限の修正を開始します..."

# ディレクトリの作成
sudo mkdir -p /var/spool/cron/crontabs

# 権限の設定
sudo chmod 755 /var/spool/cron
sudo chmod 1733 /var/spool/cron/crontabs

# 所有者の設定
sudo chown root:crontab /var/spool/cron /var/spool/cron/crontabs

# ユーザー用crontabファイルの作成
sudo touch /var/spool/cron/crontabs/kawai
sudo chmod 600 /var/spool/cron/crontabs/kawai
sudo chown kawai:crontab /var/spool/cron/crontabs/kawai

echo "完了！"
echo ""
echo "確認:"
ls -ld /var/spool/cron/
ls -ld /var/spool/cron/crontabs/
ls -l /var/spool/cron/crontabs/kawai

echo ""
echo "ユーザーに権限を付与する場合は:"
echo "  sudo usermod -a -G crontab kawai"
EOF

echo ""
echo "管理者用スクリプトを作成しました: /tmp/fix_cron_permissions.sh"
echo "このスクリプトを管理者に送って、実行してもらってください:"
echo "  sudo bash /tmp/fix_cron_permissions.sh"
