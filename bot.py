#!/usr/bin/env python3
"""Бот «Задача дня по математике (ЕНТ)».
Каждый запуск публикует следующую задачу из tasks.json как квиз-опрос Telegram:
подписчик выбирает ответ и сразу видит правильный вариант и короткий разбор.
Только стандартная библиотека Python.

Запуск:  python bot.py          (опубликовать следующую задачу)
Проверка: python bot.py --check  (проверить tasks.json, ничего не отправляя)
"""
import os, sys, json, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")   # например @my_ent_math
TASKS = ROOT / "tasks.json"
STATE = ROOT / "state" / "state.json"

# Ограничения Telegram для квиз-опросов
MAX_QUESTION, MAX_OPTION, MAX_EXPLANATION = 300, 100, 200


def load_tasks():
    return json.loads(TASKS.read_text(encoding="utf-8"))


def check_task(i, t):
    errs = []
    opts = t.get("options", [])
    if not (2 <= len(opts) <= 10):
        errs.append("нужно от 2 до 10 вариантов")
    if not isinstance(t.get("correct"), int) or not (0 <= t.get("correct", -1) < len(opts)):
        errs.append("поле correct должно быть номером правильного варианта (с 0)")
    if len(f"📐 {t.get('subject', 'Математика')} · задача №{i + 1}\n{t.get('question', '')}") > MAX_QUESTION:
        errs.append(f"вопрос длиннее {MAX_QUESTION} символов")
    if any(len(o) > MAX_OPTION for o in opts):
        errs.append(f"вариант длиннее {MAX_OPTION} символов")
    if len(t.get("explanation", "")) > MAX_EXPLANATION:
        errs.append(f"разбор длиннее {MAX_EXPLANATION} символов")
    return errs


def check_all(tasks):
    bad = 0
    for i, t in enumerate(tasks):
        for e in check_task(i, t):
            print(f"[ошибка] задача №{i + 1}: {e}")
            bad += 1
    print(f"Задач: {len(tasks)}, ошибок: {bad}")
    return bad == 0


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"next": 0}


def send_quiz(number, t):
    payload = {
        "chat_id": CHANNEL_ID,
        "question": f"📐 {t.get('subject', 'Математика')} · задача №{number}\n{t['question']}",
        "options": t["options"],
        "type": "quiz",
        "correct_option_id": t["correct"],
        "explanation": t.get("explanation", ""),
        "is_anonymous": True,
    }
    if not (BOT_TOKEN and CHANNEL_ID):
        print("[dry-run]", json.dumps(payload, ensure_ascii=False))
        return True
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    req = urllib.request.Request(
        api, json.dumps(payload).encode(), {"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception as ex:
        print(f"[ошибка] telegram: {ex}")
        return False


def main():
    tasks = load_tasks()
    if "--check" in sys.argv:
        sys.exit(0 if check_all(tasks) else 1)
    if not check_all(tasks):
        sys.exit("Исправьте ошибки в tasks.json")
    state = load_state()
    i = state["next"]
    if i >= len(tasks):
        print("Задачи закончились: добавьте новые в tasks.json")
        return
    if send_quiz(i + 1, tasks[i]):
        state["next"] = i + 1
        STATE.parent.mkdir(exist_ok=True)
        STATE.write_text(json.dumps(state), encoding="utf-8")
        print(f"Опубликована задача №{i + 1}")


if __name__ == "__main__":
    main()
