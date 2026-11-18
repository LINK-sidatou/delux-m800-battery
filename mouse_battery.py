"""DELUX M800 Ultra 电量读取（2.4G 接收器私有 HID 协议）。

协议要点（逆向自官方驱动与接收器之间的报文）：
  report id 0x04，63 字节，结构  [crc16][cmd][block_len][block_off][data...]
  查询电量：cmd = 0x1a，其余字节全 0（接收器不校验 crc，填 0 即可）
  回包：   04 00 00 1a 00 00 00 ff | level | charging
  说明：   回包 index 8 = 电量百分比，index 9 = 充电标志（0x01 充电中）
"""

import time

VENDOR_ID = 0x320F
VENDOR_USAGE_PAGE = 0xFF1C
REPORT_ID = 4
CMD_BATTERY = 0x1A


class MouseNotFound(Exception):
    pass


def _find_path():
    import hid

    for d in hid.enumerate(VENDOR_ID):
        if d["usage_page"] >= 0xFF00:
            return d["path"]
    raise MouseNotFound("没找到 DELUX 接收器")


def read_battery(retries=4, timeout=0.35):
    """返回 dict(level, charging, online)。鼠标关机/未连接时 online=False。"""
    import hid

    dev = hid.device()
    try:
        dev.open_path(_find_path())
    except MouseNotFound:
        return {"online": False, "level": None, "charging": False}
    except OSError:
        return {"online": False, "level": None, "charging": False}

    try:
        dev.set_nonblocking(1)
        for _ in range(retries):
            buf = bytearray(63)
            buf[2] = CMD_BATTERY
            dev.write(bytes([REPORT_ID]) + bytes(buf))

            deadline = time.time() + timeout
            while time.time() < deadline:
                r = dev.read(64)
                if not r:
                    time.sleep(0.005)
                    continue
                # 驱动自己也在轮询，会混进 0xaa 保活帧，只认 0x1a 的应答
                if len(r) >= 10 and r[0] == REPORT_ID and r[3] == CMD_BATTERY:
                    level = r[8]
                    if 0 <= level <= 100:
                        return {
                            "online": True,
                            "level": level,
                            "charging": bool(r[9] & 0x01),
                        }
            time.sleep(0.1)
        return {"online": False, "level": None, "charging": False}
    finally:
        dev.close()


if __name__ == "__main__":
    print(read_battery())
