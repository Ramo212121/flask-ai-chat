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

    system_prompt = {
        "role": "system",
        "content": (
            "You are a friendly and helpful AI assistant in a Flask web application. "
            "You are powered by an open-source language model running on Groq. "
            "Your name is 'Flask AI Chat'. "
            "Never claim to be ChatGPT, GPT-4, or any OpenAI product. "
            "Keep answers concise and clear. "
            "Always reply in the same language the user writes in."
        )
    }

    history = session.get("history", [])
    history.append({"role": "user", "content": message})

    def generate():
        full_reply = ""
        try:
            stream = groq_client.chat.completions.create(
                messages=[system_prompt] + history,
                model="openai/gpt-oss-120b",
                stream=True,
            )
            for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    full_reply += token
                    yield token
        except Exception as e:
            yield f"\n[Error: {str(e)}]"
            return

        # Save to session after streaming completes
        history.append({"role": "assistant", "content": full_reply})
        session["history"] = history

    return app.response_class(generate(), mimetype="text/plain")

@app.route("/history", methods=["GET"])
def get_history():
    return jsonify({"history": session.get("history", [])})


@app.route("/history", methods=["DELETE"])
def clear_history():
    session.pop("history", None)
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True, port=5001)