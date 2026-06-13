# GitHub Pages（TikTok Developer Portal 用）

このフォルダは TikTok Developer Portal の **Terms of Service URL** / **Privacy Policy URL** 用です。

## 公開 URL（リポジトリ名: `Tiktok_auot` の場合）

| 用途 | URL |
|------|-----|
| トップ | https://wakame1123.github.io/Tiktok_auot/ |
| 利用規約 | https://wakame1123.github.io/Tiktok_auot/terms/ |
| プライバシー | https://wakame1123.github.io/Tiktok_auot/privacy/ |

## GitHub Pages の有効化

1. GitHub リポジトリ → **Settings** → **Pages**
2. **Build and deployment** → Source: **Deploy from a branch**
3. Branch: **main** / Folder: **/docs**
4. **Save**

数分後に上記 URL でアクセスできます。

## TikTok URL 所有確認（「This URL is not verified」対策）

**詳細手順:** [VERIFY_TIKTOK_URL.md](./VERIFY_TIKTOK_URL.md)

要点:

1. Portal 上部 **URL properties** → **URL prefix** を選択
2. `https://wakame1123.github.io/Tiktok_auot/` を入力（末尾 `/` 必須）
3. ダウンロードした署名 `.txt` を **`docs/` 直下** に配置して push
4. Portal で **Verify** → Terms / Privacy / Web の3URLすべて verified になる

## TikTok Portal への入力例

- **Terms of Service URL:** `https://wakame1123.github.io/Tiktok_auot/terms/`
- **Privacy Policy URL:** `https://wakame1123.github.io/Tiktok_auot/privacy/`
- **Web / Desktop URL（Platforms）:** `https://wakame1123.github.io/Tiktok_auot/`
