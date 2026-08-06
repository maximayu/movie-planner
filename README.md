# Movie Planner v1.0

2作品を続けて観られる上映プランを検索するStreamlitアプリです。

## 現在の対応

- 池袋HUMAXシネマズ
- 公式上映ページから選択日の上映回を取得
- 2作品のハシゴ候補を検索
- 一覧の手動修正と再検索
- 料金は現在手入力

## 起動

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## ファイル

- `app.py`：画面
- `scraper.py`：公式ページ取得・HUMAX解析
- `planner.py`：ハシゴ判定
- `config.py`：映画館URLと許可ドメイン
