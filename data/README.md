# data: 回収データ置き場

各Raspberry Piから回収した `events.csv` をここに配置する。

## ファイル命名規則

スキャナーIDをファイル名に含めること。

```
2F-A_events.csv
2F-B_events.csv
2F-C_events.csv
3F-A_events.csv
3F-B_events.csv
3F-C_events.csv
```

## CSVのフォーマット

```
timestamp,scanner_id,uuid,rssi
2026-02-27 10:05:32,2F-A,xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx,-62
```

> ⚠️ このフォルダのCSVファイルはgit管理対象外（個人情報を含むため）
