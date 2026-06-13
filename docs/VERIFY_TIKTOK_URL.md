# TikTok URL 所有確認手順

「This URL is not verified」は **エラーではなく、まだ確認作業が必要** という意味です。

## 重要：1回の確認で3URLすべてOK

次の **親URLを1回だけ** 確認すれば、Terms / Privacy / Web URL すべてがカバーされます。

```
https://wakame1123.github.io/Tiktok_auot/
```

※末尾の `/` を付ける

---

## 手順

### 1. TikTok Developer Portal を開く

1. https://developers.tiktok.com/ → **Manage apps** → `movie_app`
2. 画面上部の **「URL properties」** ボタンをクリック

### 2. URL prefix で確認（Domain は選ばない）

| 選ぶもの | 理由 |
|----------|------|
| ✅ **URL prefix** | GitHub Pages 向け。ファイルを置くだけでOK |
| ❌ Domain | `github.io` の DNS は自分で変更できない |

### 3. URL を入力

```
https://wakame1123.github.io/Tiktok_auot/
```

**Verify** をクリック → **署名ファイル（.txt）をダウンロード**

ファイル名の例: `tiktok_developer_xxxxxxxx.txt`（アプリごとに異なる）

### 4. GitHub にファイルを配置

ダウンロードしたファイルを **リネームせず** この場所に置く:

```
docs/ダウンロードしたファイル名.txt
```

例:
```
docs/tiktok_developer_abc123.txt
```

### 5. GitHub に push

```powershell
cd g:\project\Tiktok_auot
git add docs/ダウンロードしたファイル名.txt
git commit -m "Add TikTok URL verification file"
git push
```

### 6. ファイルが公開されているか確認

ブラウザで直接開く（ファイル名は自分のものに置き換え）:

```
https://wakame1123.github.io/Tiktok_auot/ダウンロードしたファイル名.txt
```

中身がテキストで表示されればOK。

### 7. TikTok Portal で Verify

1. URL properties 画面に戻る
2. **Verify** をクリック
3. 成功すると緑のチェックが付く

---

## Portal への入力（確認後）

| 項目 | URL |
|------|-----|
| Terms of Service URL | `https://wakame1123.github.io/Tiktok_auot/terms/` |
| Privacy Policy URL | `https://wakame1123.github.io/Tiktok_auot/privacy/` |
| Web/Desktop URL | `https://wakame1123.github.io/Tiktok_auot/` |

親 prefix を確認済みなら、3つとも **verified** になります。

---

## うまくいかない場合

| 症状 | 対処 |
|------|------|
| Verify が失敗 | push 後 **2〜5分** 待ってから再試行 |
| 404 になる | ファイル名・配置場所（`docs/` 直下）を確認 |
| リダイレクトされる | GitHub Pages の URL をそのまま使う（http 不可） |
| Domain しか選べない | **URL prefix** タブを選び直す |

`docs/.nojekyll` は Jekyll が検証ファイルを無視しないための設定です（配置済み）。
