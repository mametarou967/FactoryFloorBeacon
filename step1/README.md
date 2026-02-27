# step1: BLEスキャン動作確認（Raspberry Pi 5）

## 目的

Raspberry Pi 5 + MM-BLEBC8N × 2 の構成で、BLEスキャンの基本動作を確認する。

## 構成

- スキャナー: Raspberry Pi 5 × 1（開発機）
- ビーコン: MM-BLEBC8N × 2

## 確認内容

- `bleak` ライブラリでiBeaconのUUID・RSSIが取得できること
- 近づく・遠ざかるとRSSIが変化することを確認
- RSSIピーク検出ロジックの動作確認

## ファイル構成

```
step1/
└── test_scan.py    # BLEスキャン動作確認スクリプト（実装予定）
```

## 実行方法

```bash
cd step1
python test_scan.py
```
