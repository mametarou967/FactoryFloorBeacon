# 運用開始手順書

> **対象者**: システム設置・運用開始担当者
> **所要時間**: 約XX時間（設置台数6台）
> ⚠️ 本手順書は実装完了後に詳細を追記予定です。

---

## 事前に用意するもの

| 品目 | 数量 | 備考 |
|------|------|------|
| Raspberry Pi Zero 2 WH | 6台 | 各出入口に1台 |
| microSDカード（16GB以上） | 6枚 | OSインストール済みのもの |
| USB電源アダプター + ケーブル | 6式 | 各出入口のコンセントに接続 |
| MM-BLEBC8N（BLEビーコン） | 担当者人数分（約30個） | 事前にUUID設定済みであること |
| Android端末（SSS-825アプリ導入済み） | 1台 | ビーコンのUUID設定用 |
| 作業用PC | 1台 | Raspberry Pi の初期設定用 |

---

## ステップ 1: ビーコンのUUID設定

担当者ごとに固有のUUIDをビーコンに設定します。

1. Android端末で **SSS-825** アプリを起動する
2. ビーコンを1個ずつアプリに接続し、以下の2項目を設定する

   | 設定項目 | 設定値 |
   |----------|--------|
   | UUID | 担当者ごとに異なる値（下記推奨フォーマット参照） |
   | RF POWER | **レベル6（-4dBm）** |

3. 設定したUUIDと担当者名の対応を記録しておく（次のステップで使用）

> 💡 **推奨UUIDフォーマット**: `FFB00000-0000-0000-0000-000000000001`（末尾の番号を担当者ごとに連番にする）
> 出荷時のデフォルトUUIDは全台同じ値のため、必ず変更すること。

---

## ステップ 2: person_map.csv の作成

担当者とUUIDの対応表を作成します。

1. 作業用PCで以下の形式のCSVファイルを作成する

```
uuid,name
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx,山田太郎
yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy,鈴木花子
...
```

2. ファイル名を `person_map.csv` として保存する（レポート生成時に参照するため、PCに保管しておく。各Raspberry Pi への配置は不要）

---

## ステップ 3: Raspberry Pi のセットアップ

各Raspberry Piにスキャナーソフトウェアをインストールします。

### 3-1. ファイルの転送

作業用PCからSCPで転送します（PCとPiが同じネットワークにある場合）。

```bash
# 作業用PC上で実行（<IP> は対象 Pi の IP アドレス）
scp -r /path/to/FactoryFloorBeacon/scanner pi@<IP>:~/scanner
```

または USB メモリや SD カードで直接コピーしても構いません。

### 3-2. 依存パッケージのインストール

Pi 上で実行します。

```bash
pip3 install -r ~/scanner/requirements.txt
```

---

## ステップ 4: スキャナーIDの設定

各Raspberry Piに「どのフロアのどの出入口か」を設定します。

| 設置場所 | スキャナーID |
|----------|-------------|
| 2階 出入口A | `2F-A` |
| 2階 出入口B | `2F-B` |
| 2階 出入口C | `2F-C` |
| 3階 出入口A | `3F-A` |
| 3階 出入口B | `3F-B` |
| 3階 出入口C | `3F-C` |

Pi 上で `config.ini` を編集し、設置場所に合わせて `scanner_id` を変更します。

```bash
nano ~/scanner/config.ini
```

```ini
[scanner]
scanner_id = 2F-A   # 設置場所に応じて変更
```

---

## ステップ 5: 自動起動の設定（systemd）

Pi 起動時にスキャナーが自動で立ち上がるよう設定します。

```bash
# サービスファイルをコピー
sudo cp ~/scanner/factoryfloorbeacon.service /etc/systemd/system/

# サービスを有効化・起動
sudo systemctl daemon-reload
sudo systemctl enable factoryfloorbeacon
sudo systemctl start factoryfloorbeacon

# 状態確認（Active: active (running) と表示されれば OK）
sudo systemctl status factoryfloorbeacon
```

起動後、自動的にBLEスキャンが開始され、通過イベントが `~/scanner/events.csv` に記録されます。

---

## ステップ 6: 動作確認

1. テスト用ビーコンを持って各出入口を通過する
2. `~/scanner/events.csv` に記録が追記されていることを確認する

```bash
# リアルタイムのスキャンログを確認
journalctl -u factoryfloorbeacon -f

# events.csv の最新行を確認
tail ~/scanner/events.csv
```

---

## ステップ 7: 本番運用開始

全6台の動作確認が取れたら運用開始です。

- Raspberry Pi は電源を入れておくだけで自動的にスキャンを継続します
- 約3ヶ月後にデータを回収します（→ 集計手順書 参照）

---

## トラブルシューティング

| 症状 | 確認事項 |
|------|----------|
| events.csv に記録されない | ビーコンのUUID設定・電源・Piの起動状態を確認 |
| 特定の担当者が記録されない | ビーコンの電源・UUID設定を確認（スキャナーはUUIDをそのまま記録するため、person_map.csv は関係しない） |
| Raspberry Pi が起動しない | 電源・SDカードを確認 |
