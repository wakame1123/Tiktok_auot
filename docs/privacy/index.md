---
title: Privacy Policy
---

# Privacy Policy

**Last updated:** June 13, 2026

This Privacy Policy describes how **movie_app** ("the App") handles information when you use our desktop tool.

## 1. Overview

The App runs locally on your computer. We do not operate a cloud server that collects your personal data. Data stays on your device unless you send it to TikTok through the official TikTok API.

## 2. Information We Process Locally

The App may store the following on your device only:

| Data | Purpose | Storage location |
|------|---------|------------------|
| TikTok OAuth access token & refresh token | Post videos on your behalf after you authorize | `data/tokens.json` |
| TikTok Client Key / Secret | Connect to your TikTok Developer app | `.env` (user-created) |
| Post job history (file path, status, caption) | Show upload history in dashboard | `data/jobs.db` |
| Video files | Source content for TikTok posts | User-configured watch folder |

We do not transmit this data to any third party except TikTok when you post content.

## 3. Information Sent to TikTok

When you log in or post a video, the App communicates with TikTok using their official APIs:

- **Login Kit:** OAuth authorization (scopes: `user.info.basic`, `video.publish`, `video.upload`)
- **Content Posting API:** Video files and captions you choose to publish

TikTok's handling of your data is governed by [TikTok's Privacy Policy](https://www.tiktok.com/legal/privacy-policy).

## 4. What We Do NOT Collect

- We do not collect analytics or usage telemetry
- We do not sell or share your data with advertisers
- We do not store your videos on our servers (there are no App-operated servers)

## 5. Data Retention & Deletion

- **Logout:** Removes OAuth tokens from `data/tokens.json`
- **Uninstall:** Delete the App folder to remove all local data
- **TikTok data:** Manage via TikTok account settings

## 6. Security

You are responsible for:

- Protecting your `.env` file and `data/tokens.json`
- Using the App on a secure device
- Not sharing your TikTok Developer credentials

## 7. Children

The App is not intended for users under 13 (or the minimum age required by TikTok in your region).

## 8. Changes

We may update this Privacy Policy. The "Last updated" date will reflect changes.

## 9. Contact

Privacy questions: [GitHub Issues](https://github.com/wakame1123/Tiktok_auot/issues)

---

# プライバシーポリシー（日本語）

**最終更新日:** 2026年6月13日

**movie_app** は、お使いの PC 上でローカル動作するアプリです。当方が運営するクラウドサーバーで個人データを収集することはありません。

## 1. ローカルに保存される情報

| データ | 用途 | 保存場所 |
|--------|------|----------|
| TikTok OAuth トークン | 認証後の投稿 | `data/tokens.json` |
| Client Key / Secret | TikTok API 接続 | `.env` |
| 投稿履歴 | ダッシュボード表示 | `data/jobs.db` |
| 動画ファイル | 投稿元 | 監視フォルダ |

## 2. TikTok へ送信される情報

- ログイン時: OAuth 認証情報
- 投稿時: 動画ファイル、キャプション

TikTok 側の取り扱いは [TikTok プライバシーポリシー](https://www.tiktok.com/legal/privacy-policy) に従います。

## 3. 収集しないもの

- 利用状況のトラッキング
- 広告目的の第三者提供
- 当方サーバーへの動画保存（サーバーは存在しません）

## 4. 削除方法

- ログアウト: トークン削除
- アプリフォルダ削除: すべてのローカルデータ削除

## 5. お問い合わせ

[GitHub Issues](https://github.com/wakame1123/Tiktok_auot/issues)
