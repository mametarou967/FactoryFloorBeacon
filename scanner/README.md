# scanner: 本番スキャナーコード

## 目的

各出入口の Raspberry Pi Zero 2 WH で動作する BLE スキャナー。
Step2（動作確認）・Step3（本番運用）で共通利用する。

## 構成

- スキャナー: Raspberry Pi Zero 2 WH
- ビーコン: MM-BLEBC8N（担当者が携帯）

## ファイル構成

```
scanner/
├── scanner.py                 # メインスキャナースクリプト
├── config.ini                 # スキャナーID設定ファイル
├── person_map.csv             # UUID↔担当者名マッピング（レポート生成時のみ使用）
└── factoryfloorbeacon.service # systemd サービスファイル
```

## Zero 2 WH への導入手順

### 1. ファイル転送

Pi5（開発機）から SCP で転送する。

```bash
# Pi5 上で実行（<IP> は Zero 2 WH の IP アドレス）
scp -r ~/Desktop/FactoryFloorBeacon/scanner pi@<IP>:~/scanner
```

または USB メモリや SD カードで直接コピーしてもよい。

### 2. 依存パッケージのインストール

Zero 2 WH 上で実行する。

```bash
pip3 install bleak
```

### 3. スキャナーID の設定

`config.ini` を設置場所に合わせて編集する。

```bash
nano ~/scanner/config.ini
```

```ini
[scanner]
scanner_id = 2F-A   # 設置場所に応じて変更: 2F-A / 2F-B / 2F-C / 3F-A / 3F-B / 3F-C
```

### 4. 動作確認（手動実行）

```bash
cd ~/scanner
sudo python3 scanner.py
```

ビーコンを近づけて検知ログが表示されること、10秒後に通過イベントが `events.csv` に記録されることを確認する。

### 5. systemd サービスの登録（自動起動設定）

```bash
# サービスファイルをコピー
sudo cp ~/scanner/factoryfloorbeacon.service /etc/systemd/system/

# サービスを有効化・起動
sudo systemctl daemon-reload
sudo systemctl enable factoryfloorbeacon
sudo systemctl start factoryfloorbeacon

# 状態確認
sudo systemctl status factoryfloorbeacon
```

### 6. ログの確認

```bash
# リアルタイムでログを確認
journalctl -u factoryfloorbeacon -f
```

## 実行方法（手動）

```bash
cd ~/scanner
sudo python3 scanner.py
```

## 出力

通過イベントが `~/scanner/events.csv` に追記される。

```
timestamp,scanner_id,uuid,rssi
2026-02-27 10:05:32,2F-A,ffb00000-0000-0000-0000-000000000001,-62
```
