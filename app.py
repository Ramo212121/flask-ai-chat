import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from groq import Groq

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-key-change-me")

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ===== Models =====

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    chats = db.relationship("Chat", backref="user", cascade="all, delete-orphan")


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), default="New Chat")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    messages = db.relationship(
        "Message",
        backref="chat",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chat.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# ===== Routes =====

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    chat_id = data.get("chat_id")

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    if len(message) > 1000:
        return jsonify({"error": "Message cannot exceed 1000 characters"}), 400

    # Get or create chat
    if chat_id:
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
    else:
        title = message[:50] + ("..." if len(message) > 50 else "")
        chat = Chat(title=title)
        db.session.add(chat)
        db.session.commit()
        chat_id = chat.id

    # Save user message
    user_msg = Message(chat_id=chat_id, role="user", content=message)
    db.session.add(user_msg)
    db.session.commit()

    # Build history from DB
    history = [
        {"role": m.role, "content": m.content}
        for m in chat.messages
    ]

    system_prompt = {
        "role": "system",
        "content": (
            "You are a friendly and helpful AI assistant in a Flask web application. "
            "Your name is 'Flask AI Chat'. "
            "Never claim to be ChatGPT, GPT-4, or any OpenAI product. "
            "Always reply in the same language the user writes in."
        )
    }

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

        # Save assistant message
        ai_msg = Message(chat_id=chat_id, role="assistant", content=full_reply)
        db.session.add(ai_msg)
        db.session.commit()

    return app.response_class(generate(), mimetype="text/plain")


@app.route("/chats", methods=["GET"])
def get_chats():
    chats = Chat.query.order_by(Chat.updated_at.desc()).all()
    return jsonify({
        "chats": [
            {
                "id": c.id,
                "title": c.title,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None
            }
            for c in chats
        ]
    })


@app.route("/chats", methods=["POST"])
def create_chat():
    chat = Chat(title="New Chat")
    db.session.add(chat)
    db.session.commit()
    return jsonify({"id": chat.id, "title": chat.title}), 201


@app.route("/chats/<int:chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    db.session.delete(chat)
    db.session.commit()
    return jsonify({"status": "deleted"})


@app.route("/history/<int:chat_id>", methods=["GET"])
def get_history(chat_id):
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    history = [
        {"role": m.role, "content": m.content}
        for m in chat.messages
    ]
    return jsonify({"history": history})


@app.route("/history/<int:chat_id>", methods=["DELETE"])
def clear_history(chat_id):
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    Message.query.filter_by(chat_id=chat_id).delete()
    db.session.commit()
    return jsonify({"status": "cleared"})


# ===== Init DB =====
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, port=5001)