#!/usr/bin/env python3
"""
本番スキャナースクリプト

Raspberry Pi Zero 2 WH の各出入口で動作する BLE スキャナー。
iBeacon の UUID・RSSI を取得し、タイムアウト方式で通過イベントを
events.csv に記録する。

使用方法:
    python scanner.py

設定:
    config.ini の scanner_id をこの Pi の設置場所に合わせて変更すること。
    例: 2F-A / 2F-B / 2F-C / 3F-A / 3F-B / 3F-C
"""

import asyncio
import configparser
import csv
import os
import struct
from datetime import datetime
from pathlib import Path
from typing import Optional

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


# ===== 設定読み込み =====

_HERE = Path(__file__).parent
_CONFIG_FILE = _HERE / "config.ini"

config = configparser.ConfigParser()
if not _CONFIG_FILE.exists():
    raise FileNotFoundError(f"設定ファイルが見つかりません: {_CONFIG_FILE}")
config.read(_CONFIG_FILE, encoding="utf-8")

SCANNER_ID = config.get("scanner", "scanner_id")
CSV_FILE   = _HERE / "events.csv"

# 検知対象UUIDのプレフィックス（これ以外のBLEデバイスは無視する）
UUID_PREFIX = "ffb00000"

# 検知パラメータ
MIN_RSSI       = -85   # dBm: これより弱い信号は無視する（ポケット減衰を考慮）
MIN_PEAK_RSSI  = -80   # dBm: この値以上のピークのみイベントとして記録する
BEACON_TIMEOUT = 10.0  # sec: この時間検知されなければビーコンが去ったと判定する
#   500msアドバタイズで10秒 = 20パケット連続ロスト → ほぼ確実に圏外


# ===== iBeacon パース =====

def parse_ibeacon(manufacturer_data: dict) -> Optional[dict]:
    """
    manufacturer_data から iBeacon 情報を取得する。
    iBeacon でなければ None を返す。

    iBeacon フォーマット:
      Company ID : 0x004C (Apple)
      Type       : 0x02 0x15
      UUID       : 16 bytes
      Major      : 2 bytes
      Minor      : 2 bytes
      TX Power   : 1 byte
    """
    apple_data = manufacturer_data.get(0x004C)
    if apple_data is None or len(apple_data) < 23:
        return None
    if apple_data[0] != 0x02 or apple_data[1] != 0x15:
        return None

    uuid_b = apple_data[2:18]
    uuid = (
        f"{uuid_b[0:4].hex()}-"
        f"{uuid_b[4:6].hex()}-"
        f"{uuid_b[6:8].hex()}-"
        f"{uuid_b[8:10].hex()}-"
        f"{uuid_b[10:16].hex()}"
    )
    major = struct.unpack(">H", apple_data[18:20])[0]
    minor = struct.unpack(">H", apple_data[20:22])[0]

    return {"uuid": uuid, "major": major, "minor": minor}


# ===== イベント記録 =====

def record_event(timestamp: str, scanner_id: str, uuid: str, rssi: int) -> None:
    """通過イベントを CSV に追記する。"""
    write_header = not CSV_FILE.exists()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "scanner_id", "uuid", "rssi"])
        writer.writerow([timestamp, scanner_id, uuid, rssi])
    print(f"[EVENT] {timestamp}  {uuid}  RSSI_peak={rssi}dBm", flush=True)


# ===== ビーコン追跡 =====

class BeaconTracker:
    """
    UUID ごとに RSSI を追跡し、タイムアウト方式で通過イベントを発火する。

    検出ロジック:
      BEACON_TIMEOUT 秒間検知なし → 通過イベント（圏外判定）
    """

    def __init__(self):
        # uuid -> {"peak": int, "last_seen": datetime}
        self._states: dict = {}

    def update(self, uuid: str, rssi: int, now: datetime) -> None:
        """RSSI を更新する。"""
        if uuid not in self._states:
            self._states[uuid] = {"peak": rssi, "last_seen": now}
            return

        s = self._states[uuid]
        s["last_seen"] = now
        if rssi > s["peak"]:
            s["peak"] = rssi

    def flush_timeouts(self, now: datetime) -> list:
        """
        タイムアウトしたビーコンを圏外と判定してイベントとして返す。
        戻り値: [(uuid, peak_rssi), ...]
        """
        events = []
        to_delete = []

        for uuid, s in self._states.items():
            elapsed = (now - s["last_seen"]).total_seconds()
            if elapsed >= BEACON_TIMEOUT:
                events.append((uuid, s["peak"]))
                to_delete.append(uuid)

        for uuid in to_delete:
            del self._states[uuid]

        return events


# ===== メインスキャンループ =====

async def main() -> None:
    print("=" * 50, flush=True)
    print("BLEスキャン開始", flush=True)
    print(f"  スキャナーID  : {SCANNER_ID}", flush=True)
    print(f"  出力ファイル  : {CSV_FILE}", flush=True)
    print(f"  MIN_RSSI      : {MIN_RSSI} dBm", flush=True)
    print(f"  MIN_PEAK_RSSI : {MIN_PEAK_RSSI} dBm", flush=True)
    print(f"  BEACON_TIMEOUT: {BEACON_TIMEOUT} s", flush=True)
    print("Ctrl+C で終了", flush=True)
    print("=" * 50, flush=True)

    tracker = BeaconTracker()
    event_count = 0

    def on_detection(device: BLEDevice, adv: AdvertisementData) -> None:
        nonlocal event_count
        if not adv.manufacturer_data:
            return

        beacon = parse_ibeacon(adv.manufacturer_data)
        if beacon is None:
            return

        rssi = adv.rssi
        if rssi < MIN_RSSI:
            return

        uuid = beacon["uuid"]
        if not uuid.lower().startswith(UUID_PREFIX):
            return

        now = datetime.now()
        print(f"  検知 {uuid[:8]}...{uuid[-5:]}  RSSI={rssi:4d}dBm", flush=True)
        tracker.update(uuid, rssi, now)

    scanner = BleakScanner(detection_callback=on_detection)

    try:
        await scanner.start()
        while True:
            await asyncio.sleep(1.0)
            now = datetime.now()

            for uuid, peak in tracker.flush_timeouts(now):
                if peak < MIN_PEAK_RSSI:
                    continue
                ts = now.strftime("%Y-%m-%d %H:%M:%S")
                record_event(ts, SCANNER_ID, uuid, peak)
                event_count += 1
                print(f"  [通過イベント 累計{event_count}回]", flush=True)

    except KeyboardInterrupt:
        print("\nスキャン停止（手動）", flush=True)
    finally:
        await scanner.stop()


if __name__ == "__main__":
    asyncio.run(main())
