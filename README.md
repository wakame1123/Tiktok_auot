# TikTok 時間予告 自動投稿アプリ

指定フォルダに動画が保存されると、TikTok へ**時間予告（LIVE告知）動画**を自動投稿する Windows 向けアプリです。

## 機能

- **フォルダ監視**: `watch` フォルダに動画（`.mp4` / `.mov` / `.webm`）が追加されると自動検知
- **TikTok 自動投稿**: TikTok Content Posting API で動画をアップロード・公開
- **時間予告キャプション**: メタデータまたはファイル名から配信時刻を読み取り、キャプションに自動挿入
- **Web ダッシュボード**: 認証・監視状態・投稿履歴をブラウザで確認

## 必要なもの

1. **Python 3.10 以上**
2. **TikTok Developer アカウント** — [developers.tiktok.com](https://developers.tiktok.com/) でアプリを作成
3. アプリに **Content Posting API** を追加し、スコープ `video.publish`（即時投稿）または `video.upload`（下書き）を有効化
4. Redirect URI に `http://127.0.0.1:8765/callback` を登録

> **注意**: 未監査のアプリは投稿が「自分のみ公開」に制限されます。本番利用には TikTok のアプリ監査が必要です。

## セットアップ

```powershell
# 1. 依存関係
copy .env.example .env
copy config.yaml.example config.yaml

# 2. .env を編集 — Client Key / Secret を設定
# TIKTOK_CLIENT_KEY=...
# TIKTOK_CLIENT_SECRET=...

# 3. 起動（start.bat でも可）
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8765
```

ブラウザで http://127.0.0.1:8765 を開き、「TikTokでログイン」から OAuth 認証を完了してください。

## 使い方

### 基本的な流れ

1. 監視フォルダ（デフォルト: `./watch`）に動画ファイルを配置
2. アプリがファイルの書き込み完了を待ってから TikTok へ投稿
3. 成功したファイルは `watch/processed/`、失敗したファイルは `watch/failed/` へ移動

### メタデータ（任意）

動画と同じ名前の `.meta.json` を置くと、キャプションをカスタマイズできます。

**例**: `20250613_2100_告知.mp4` + `20250613_2100_告知.meta.json`

```json
{
  "title": "本日21時LIVE配信！",
  "live_time": "2025-06-13T21:00:00+09:00",
  "hashtags": ["TikTokLIVE", "ライブ告知", "時間予告"]
}
```

### ファイル名から時刻を自動解析

`YYYYMMDD_HHMM` 形式のファイル名（例: `20250613_2100_告知.mp4`）から配信時刻を推測し、キャプションに反映します。

## 設定

| ファイル | 内容 |
|---------|------|
| `.env` | TikTok API キー、監視フォルダ、投稿モード等 |
| `config.yaml` | キャプションテンプレート、拡張子、移動先フォルダ等 |

### 投稿モード

| モード | 説明 |
|--------|------|
| `direct`（デフォルト） | 即時公開投稿 |
| `draft` | TikTok 受信箱に下書き送信（アプリ側で LIVE ステッカー追加可能） |

`config.yaml` の `post_mode: "draft"` に変更すると、TikTok アプリの受信箱通知から最終編集・投稿できます。

## LIVE 告知ステッカーについて

TikTok の **LIVE 告知ステッカー**（ショート動画にカウントダウンを表示する機能）は、現時点で Content Posting API では設定できません。

本アプリでは以下の代替手段を提供しています:

- **direct モード**: キャプションに配信予定時刻を自動挿入して公開
- **draft モード**: 受信箱に下書きとして送り、TikTok アプリで LIVE ステッカーを手動追加

## プロジェクト構成

```
Tiktok_auot/
├── main.py              # FastAPI アプリ（Web UI + 監視起動）
├── start.bat            # Windows 起動スクリプト
├── config.yaml.example
├── .env.example
├── src/
│   ├── config.py        # 設定・キャプション生成
│   ├── watcher.py       # フォルダ監視
│   ├── processor.py     # 投稿処理・履歴
│   └── tiktok/
│       ├── auth.py      # OAuth 認証
│       └── client.py    # 動画アップロード API
├── templates/
│   └── index.html       # ダッシュボード
└── watch/               # 監視フォルダ（動画をここに置く）
```

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| 認証できない | Redirect URI が Developer Portal と `.env` で一致しているか確認 |
| 投稿が非公開になる | アプリが未監査の場合は `SELF_ONLY` 制限あり。監査申請を行う |
| ファイルが処理されない | コピー中の可能性 — `stable_wait_seconds` を増やす |
| トークン期限切れ | 自動リフレッシュされます。失敗時は再ログイン |

## ライセンス

MIT
