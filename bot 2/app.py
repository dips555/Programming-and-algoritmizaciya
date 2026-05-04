from flask import Flask, request, jsonify, render_template
import requests
import uuid
import json


app = Flask(__name__)
#api ключи
YANDEX_API_KEY = "AQVNxV1yiIs7ma0S6aL1TDfZNn8zNL8eJVGr8Kut"
FOLDER_ID = "b1g84619fq7bte1r2fvt"

YANDEX_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

sessions = {}

QUESTIONS = [
    ("engine_power_kw", "мощность двигателя в кВт"),
    ("exhaust_flow_kg_h", "объём выхлопных газов в кг/ч"),
    ("exhaust_temp_c", "температура выхлопных газов в °C"),
    ("flange_diameter_mm", "внутренний диаметр фланца в мм"),
    ("cooling_pump_flow_m3_h", "расход насоса охлаждения в м³/ч"),
    ("cooling_pump_head_m", "напор насоса охлаждения в м"),
    ("pipeline_length_m", "длину магистрали в метрах"),
    ("height_difference_m", "перепад высот в метрах")
]


# ---------------- GPT ----------------
def gpt_question(param_name, param_desc):
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
будь вежлив
тебе надо узнать у пользователя его имеющиеся характеристики 
Ты инженерный ассистент.
Сформулируй короткий понятный вопрос для пользователя.

Параметр: {param_desc}

Правила:
- 1 предложение
- без лишних слов
- технически точно
"""

    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "temperature": 0.5,
            "maxTokens": 100
        },
        "messages": [
            {"role": "system", "text": "Ты инженерный ассистент."},
            {"role": "user", "text": prompt}
        ]
    }

    r = requests.post(YANDEX_URL, json=data, headers=headers)

    if r.status_code != 200:
        return f"Введите {param_desc}"

    return r.json()["result"]["alternatives"][0]["message"]["text"]


# ---------------- utils ----------------
def new_session():
    return {"step": 0, "data": {}}


def is_number(v):
    try:
        float(v)
        return True
    except:
        return False


def save():
    with open("storage.json", "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=4)


# ---------------- routes ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id")

    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = new_session()

    session = sessions[session_id]
    step = session["step"]

    # сохраняем прошлый ответ
    if step > 0:
        key, _ = QUESTIONS[step - 1]

        if not is_number(message):
            return jsonify({
                "session_id": session_id,
                "reply": "Ошибка: нужно числовое значение"
            })

        session["data"][key] = float(message)

    # завершение
    if step >= len(QUESTIONS):
        save()
        return jsonify({
            "session_id": session_id,
            "reply": "Все параметры собраны ✔",
            "data": session["data"]
        })

    # GPT генерирует вопрос
    key, desc = QUESTIONS[step]
    session["step"] += 1

    question = gpt_question(key, desc)

    return jsonify({
        "session_id": session_id,
        "reply": question
    })


if __name__ == "__main__":
    app.run(debug=True)
