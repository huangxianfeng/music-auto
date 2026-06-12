from flask import Flask, render_template, request, jsonify
import os
import threading

from core.utils import setup_logging
from core.browser import BrowserDriver, DouyinMusicConsole
from core.creator import build_full_workflow

app = Flask(__name__, template_folder="templates", static_folder="static")
setup_logging()

RUNNING = {"busy": False, "message": "空闲"}


def _auto_task(theme: str, mood: str, lines: int):
    global RUNNING
    RUNNING["busy"] = True
    RUNNING["message"] = "正在生成歌词..."
    try:
        result = build_full_workflow(theme=theme, mood=mood, lines=lines)
        RUNNING["message"] = f"已生成: {result['title']}，正在打开浏览器..."
        bd = BrowserDriver(headless=False)
        driver = bd.start()
        console = DouyinMusicConsole(driver)
        console.open()
        if console.require_login():
            console.auto_create_music(prompt=result["prompt"], lyrics=result["lyrics"])
            RUNNING["message"] = f"已完成，请在浏览器中确认"
        else:
            RUNNING["message"] = "登录超时，请重试"
        bd.quit()
    except Exception as e:
        RUNNING["message"] = f"错误: {e}"
    finally:
        RUNNING["busy"] = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    return jsonify({"busy": RUNNING["busy"], "message": RUNNING["message"]})


@app.route("/api/create", methods=["POST"])
def create():
    if RUNNING["busy"]:
        return jsonify({"ok": False, "message": "任务执行中，请稍候"}), 409
    data = request.get_json() or {}
    theme = data.get("theme", "励志")
    mood = data.get("mood", "轻快")
    lines = int(data.get("lines", 8))
    threading.Thread(target=_auto_task, args=(theme, mood, lines), daemon=True).start()
    return jsonify({"ok": True, "message": "任务已启动，请稍候查看浏览器"})


@app.route("/api/open-console", methods=["POST"])
def open_console():
    if RUNNING["busy"]:
        return jsonify({"ok": False, "message": "任务执行中，请稍候"}), 409

    def _task():
        global RUNNING
        RUNNING["busy"] = True
        RUNNING["message"] = "正在打开控制台..."
        bd = BrowserDriver(headless=False)
        driver = bd.start()
        console = DouyinMusicConsole(driver)
        console.open()
        console.require_login()
        RUNNING["message"] = "空闲"
        RUNNING["busy"] = False

    threading.Thread(target=_task, daemon=True).start()
    return jsonify({"ok": True, "message": "浏览器已启动，请完成登录"})


def main():
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()
