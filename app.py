import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session
from groq import Groq

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-key-change-me")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    if len(message) > 1000:
        return jsonify({"error": "Message cannot exceed 1000 characters"}), 400

    history = session.get("history", [])
    history.append({"role": "user", "content": message})

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=history,
            model="openai/gpt-oss-120b",
        )
        reply = chat_completion.choices[0].message.content
    except Exception as e:
        return jsonify({"error": f"AI error: {str(e)}"}), 500

    history.append({"role": "assistant", "content": reply})
    session["history"] = history

    return jsonify({"reply": reply, "history_length": len(history)})


@app.route("/history", methods=["GET"])
def get_history():
    return jsonify({"history": session.get("history", [])})


@app.route("/history", methods=["DELETE"])
def clear_history():
    session.pop("history", None)
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True, port=5001)