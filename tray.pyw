"""DELUX M800 Ultra 任务栏托盘电量指示器。

双击 启动托盘.vbs 运行（无控制台窗口）。右键托盘图标可刷新、改刷新间隔、开关开机自启。
"""

import os
import shutil
import sys
import threading
import time

from PIL import Image, ImageDraw, ImageFont
import pystray

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mouse_battery import read_battery  # noqa: E402

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LAUNCHER = os.path.join(APP_DIR, "启动托盘.vbs")
STARTUP_DIR = os.path.join(
    os.environ.get("APPDATA", ""),
    r"Microsoft\Windows\Start Menu\Programs\Startup",
)
STARTUP_LINK = os.path.join(STARTUP_DIR, "DELUX鼠标电量.vbs")

# 原生崩溃（非 Python 异常）也留个现场
try:
    import faulthandler

    _fault_fh = open(os.path.join(APP_DIR, "run.log"), "a", buffering=1, encoding="utf-8")
    faulthandler.enable(_fault_fh)
except Exception:
    pass

GREEN = (46, 160, 67)
AMBER = (220, 145, 20)
RED = (200, 55, 50)
BLUE = (30, 120, 210)
GREY = (128, 128, 128)

INTERVALS = [(30, "30 秒"), (60, "1 分钟"), (300, "5 分钟")]

state = {"level": None, "charging": False, "online": False, "last": None}
interval = {"sec": 60}
stop_flag = threading.Event()


def _font(size):
    for name in ("segoeuib.ttf", "arialbd.ttf", "seguisb.ttf"):
        try:
            return ImageFont.truetype(os.path.join(os.environ["WINDIR"], "Fonts", name), size)
        except Exception:
            continue
    return ImageFont.load_default()


def _color():
    if not state["online"]:
        return GREY
    if state["charging"]:
        return BLUE
    lv = state["level"]
    if lv is None:
        return GREY
    if lv <= 20:
        return RED
    if lv <= 50:
        return AMBER
    return GREEN


def make_icon():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 2, 61, 61), radius=15, fill=_color())

    if state["online"] and state["level"] is not None:
        text = str(state["level"])
    else:
        text = "--"

    size = 46 if len(text) <= 2 else 34
    font = _font(size)
    box = d.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text((32 - w / 2 - box[0], 30 - h / 2 - box[1]), text, font=font, fill="white")

    if state["charging"]:
        # 底部一条闪电状的亮条，表示正在充电
        d.rectangle((20, 52, 44, 56), fill="white")
    return img


def tooltip():
    if not state["online"]:
        return "DELUX M800 Ultra · 未连接（鼠标关机或接收器未插）"
    tag = "充电中" if state["charging"] else "放电中"
    return f"DELUX M800 Ultra · {state['level']}% · {tag}"


def refresh(icon=None):
    data = read_battery()
    changed = (data["level"], data["charging"], data["online"]) != (
        state["level"],
        state["charging"],
        state["online"],
    )
    state.update(data)
    state["last"] = time.strftime("%H:%M:%S")
    if icon is not None and changed:
        icon.icon = make_icon()
        icon.title = tooltip()


last_warn = {"t": 0.0}


def loop(icon):
    while not stop_flag.is_set():
        try:
            refresh(icon)
            lv = state["level"]
            if (
                state["online"]
                and lv is not None
                and lv <= 15
                and not state["charging"]
                and time.time() - last_warn["t"] > 3600
            ):
                last_warn["t"] = time.time()
                icon.notify(f"鼠标电量仅剩 {lv}%，建议充电", "DELUX M800 Ultra")
        except Exception:
            import traceback

            _log("loop error: " + traceback.format_exc())
        _log(f"刷新完成 online={state['online']} level={state['level']}")
        stop_flag.wait(interval["sec"])


def set_interval(sec):
    def _inner(icon, item):
        interval["sec"] = sec
        return True

    return _inner


def autostart_enabled():
    return os.path.exists(STARTUP_LINK)


def toggle_autostart(icon, item):
    try:
        if autostart_enabled():
            os.remove(STARTUP_LINK)
        else:
            os.makedirs(STARTUP_DIR, exist_ok=True)
            shutil.copy2(LAUNCHER, STARTUP_LINK)
    except Exception:
        pass
    return autostart_enabled()


def quit_app(icon, item):
    stop_flag.set()
    icon.stop()


LOG_PATH = os.path.join(APP_DIR, "run.log")


def _log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} [{os.getpid()}] {msg}\n")
    except Exception:
        pass


def main():
    _log("启动 (pythonw=%s)" % sys.executable.endswith("pythonw.exe"))
    refresh()
    _log(f"首次读取: online={state['online']} level={state['level']}")
    icon = pystray.Icon(
        "delux_m800_battery",
        make_icon(),
        tooltip(),
        pystray.Menu(
            pystray.MenuItem(lambda i: tooltip(), None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("立即刷新", lambda i, it: refresh(i), default=True),
            pystray.MenuItem(
                "刷新间隔",
                pystray.Menu(
                    *[
                        pystray.MenuItem(
                            label,
                            set_interval(sec),
                            checked=(lambda s=sec: interval["sec"] == s),
                            radio=True,
                        )
                        for sec, label in INTERVALS
                    ]
                ),
            ),
            pystray.MenuItem("开机自启", toggle_autostart, checked=lambda i: autostart_enabled()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", quit_app),
        ),
    )
    _log("托盘图标已创建")
    threading.Thread(target=loop, args=(icon,), daemon=True).start()
    icon.run()
    _log("icon.run() 返回，进程退出")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        _log("fatal: " + traceback.format_exc())
