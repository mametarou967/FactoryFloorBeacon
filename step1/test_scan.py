#!/usr/bin/env python3
"""
Step 1: BLEスキャン動作確認スクリプト

Raspberry Pi 5 + MM-BLEBC8N × 2 での基本動作確認用。
iBeacon の UUID・RSSI を取得し、RSSI ピーク検出で
通過イベントを events.csv に記録する。

使用方法:
    python test_scan.py
"""

import asyncio
import csv
import os
import struct
from datetime import datetime
from typing import Optional

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


# ===== 設定 =====

SCANNER_ID = "PI5-DEV"   # このスキャナーのID（本番では "2F-A" 等）
CSV_FILE = "events.csv"  # 出力先CSVファイル名

# ピーク検出パラメータ（Step1実測後に調整する）
MIN_RSSI = -80        # dBm: これより弱い信号は無視する
MIN_PEAK_RSSI = -70   # dBm: この値以上のピークのみイベントとして記録する
DROP_THRESHOLD = 10   # dBm: ピーク値からこれだけ下がったら通過と判定する
BEACON_TIMEOUT = 8.0  # sec: この時間検知されなければビーコンが去ったと判定する


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
    apple_data = manufacturer_data.get(0x004C)  # Apple Company ID
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
    write_header = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "scanner_id", "uuid", "rssi"])
        writer.writerow([timestamp, scanner_id, uuid, rssi])
    print(f"[EVENT] {timestamp}  {uuid}  RSSI_peak={rssi}dBm")


# ===== RSSI ピーク検出 =====

class BeaconTracker:
    """
    UUID ごとに RSSI を追跡し、通過イベント（ピーク検出）を発火する。

    検出ロジック:
      1. ピーク後に DROP_THRESHOLD dBm 以上下降 → 通過イベント
      2. または BEACON_TIMEOUT 秒間検知なし   → 通過イベント（素通りケース）
    """

    def __init__(self):
        # uuid -> {"peak": int, "last_seen": datetime, "fired": bool}
        self._states: dict = {}

    def update(self, uuid: str, rssi: int, now: datetime) -> Optional[int]:
        """
        RSSI を更新する。
        通過イベントが発火した場合はピーク RSSI を返す。それ以外は None。
        """
        if uuid not in self._states:
            self._states[uuid] = {
                "peak": rssi,
                "last_seen": now,
                "fired": False,
            }
            return None

        s = self._states[uuid]
        s["last_seen"] = now

        # ピーク更新
        if rssi > s["peak"]:
            s["peak"] = rssi
            s["fired"] = False  # 新たなピークが来たのでリセット

        # ピーク後に DROP_THRESHOLD dBm 下降 → イベント発火
        if (
            not s["fired"]
            and s["peak"] >= MIN_PEAK_RSSI
            and rssi <= s["peak"] - DROP_THRESHOLD
        ):
            peak = s["peak"]
            s["fired"] = True
            s["peak"] = rssi  # 次回通過に備えてリセット
            return peak

        return None

    def flush_timeouts(self, now: datetime) -> list:
        """
        タイムアウトしたビーコンをチェックする。
        ピークに達したまま圏外になったケース（素通りなど）も
        イベントとして返す。
        戻り値: [(uuid, peak_rssi), ...]
        """
        events = []
        to_delete = []

        for uuid, s in self._states.items():
            elapsed = (now - s["last_seen"]).total_seconds()
            if elapsed >= BEACON_TIMEOUT:
                if not s["fired"] and s["peak"] >= MIN_PEAK_RSSI:
                    events.append((uuid, s["peak"]))
                to_delete.append(uuid)

        for uuid in to_delete:
            del self._states[uuid]

        return events


# ===== メインスキャンループ =====

async def main() -> None:
    print("=" * 50)
    print("BLEスキャン開始")
    print(f"  スキャナーID  : {SCANNER_ID}")
    print(f"  出力ファイル  : {CSV_FILE}")
    print(f"  MIN_RSSI      : {MIN_RSSI} dBm")
    print(f"  MIN_PEAK_RSSI : {MIN_PEAK_RSSI} dBm")
    print(f"  DROP_THRESHOLD: {DROP_THRESHOLD} dBm")
    print(f"  BEACON_TIMEOUT: {BEACON_TIMEOUT} s")
    print("Ctrl+C で終了")
    print("=" * 50)

    tracker = BeaconTracker()

    def on_detection(device: BLEDevice, adv: AdvertisementData) -> None:
        if not adv.manufacturer_data:
            return

        beacon = parse_ibeacon(adv.manufacturer_data)
        if beacon is None:
            return

        rssi = adv.rssi
        if rssi < MIN_RSSI:
            return

        uuid = beacon["uuid"]
        now = datetime.now()

        print(f"  検知 {uuid[:8]}...  RSSI={rssi:4d}dBm")

        peak = tracker.update(uuid, rssi, now)
        if peak is not None:
            ts = now.strftime("%Y-%m-%d %H:%M:%S")
            record_event(ts, SCANNER_ID, uuid, peak)

    scanner = BleakScanner(detection_callback=on_detection)

    try:
        await scanner.start()
        while True:
            await asyncio.sleep(1.0)
            # タイムアウトチェック（1秒ごと）
            now = datetime.now()
            for uuid, peak in tracker.flush_timeouts(now):
                ts = now.strftime("%Y-%m-%d %H:%M:%S")
                record_event(ts, SCANNER_ID, uuid, peak)

    except KeyboardInterrupt:
        print("\nスキャン停止")
    finally:
        await scanner.stop()


if __name__ == "__main__":
    asyncio.run(main())
