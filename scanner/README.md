# scanner: 本番スキャナーコード

## 目的

各出入口のRaspberry Pi Zero 2 WH で動作するBLEスキャナー。
Step2（動作確認）・Step3（本番運用）で共通利用する。

## 構成

- スキャナー: Raspberry Pi Zero 2 WH
- ビーコン: MM-BLEBC8N（担当者が携帯）

## ファイル構成

```
scanner/
├── scanner.py      # メインスキャナースクリプト（実装予定）
├── config.ini      # スキャナーID等の設定ファイル（実装予定）
└── person_map.csv  # UUID↔担当者名のマッピング（運用前に作成）
```

## 設定ファイル（config.ini）

各Raspberry Piに設置場所に応じたスキャナーIDを設定する。

```ini
[scanner]
scanner_id = 2F-A   # 例: 2F-A / 2F-B / 2F-C / 3F-A / 3F-B / 3F-C
```

## 実行方法

```bash
cd scanner
python scanner.py
```

## 出力

通過イベントが `events.csv` に追記される。

```
timestamp,scanner_id,uuid,rssi
2026-02-27 10:05:32,2F-A,xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx,-62
```
