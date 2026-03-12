# まとめ速報

2chまとめサイトのRSSを自動収集して表示するページです。  
GitHub Actionsが30分ごとに自動更新します。

## セットアップ手順

### 1. このリポジトリをGitHubに作成する

1. GitHub (https://github.com) にログイン
2. 右上の「+」→「New repository」をクリック
3. Repository name: `matome` と入力
4. **Public** を選択（GitHub Pagesの無料利用に必要）
5. 「Create repository」をクリック

### 2. ファイルをアップロードする

Macのターミナルで以下を実行（`あなたのユーザー名` を自分のGitHubユーザー名に変更）:

```bash
cd ~/Downloads/matome        # このフォルダに移動
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/あなたのユーザー名/matome.git
git push -u origin main
```

### 3. GitHub Pages を有効にする

1. GitHubのリポジトリページを開く
2. 「Settings」タブ → 左メニュー「Pages」
3. Source: **Deploy from a branch**
4. Branch: **gh-pages** / **/ (root)**
5. 「Save」をクリック

### 4. Actionsを有効にする

1. 「Actions」タブを開く
2. 「I understand my workflows, go ahead and enable them」をクリック
3. 左メニュー「Update Matome」→「Run workflow」で初回実行

### 5. 完成！

数分後にこのURLでアクセスできます:  
`https://あなたのユーザー名.github.io/matome/`

iPhoneのSafariでこのURLをホーム画面に追加すれば、アプリのように使えます。

## 自動更新について

- 30分ごとにGitHub Actionsが自動でRSSを取得してページを更新します
- 無料枠内で動作します（月2,000分まで無料）
