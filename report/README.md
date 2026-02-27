# report: レポート生成コード

## 目的

各Raspberry Piから回収したCSVデータを統合し、HTMLレポート・CSV・PNGを生成する。
Step3（本番運用）終了後、作業用PCで実行する。

## 実行前の準備

`data/` フォルダに各Piから回収したCSVを配置する。（→ 集計手順書参照）

```
data/
├── 2F-A_events.csv
├── 2F-B_events.csv
├── 2F-C_events.csv
├── 3F-A_events.csv
├── 3F-B_events.csv
└── 3F-C_events.csv
```

## ファイル構成

```
report/
└── report.py       # レポート生成スクリプト（実装予定）
```

## 実行方法

```bash
cd report
python report.py
```

## 出力

```
output/
├── report.html              # メインレポート（ブラウザで閲覧）
├── report.csv               # 集計データ（Excelで開ける）
└── graphs/
    ├── floor_total.png      # フロア間往来の総数
    ├── floor_daily.png      # 日別推移
    ├── floor_hourly.png     # 時間帯別頻度
    ├── floor_weekly.png     # 曜日別パターン
    ├── individual_ranking.png   # 個人別往来回数ランキング
    └── individual_hourly.png    # 個人別時間帯パターン
```
