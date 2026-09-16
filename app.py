import os
from pathlib import Path
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
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


# ===== Auth Decorator =====

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function


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


# ===== Auth Routes =====

@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        data = request.get_json()
        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not username or not email or not password:
            return jsonify({"error": "All fields are required"}), 400

        if len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters"}), 400

        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already taken"}), 409

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        session["username"] = user.username

        return jsonify({"status": "registered", "username": user.username}), 201

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"error": "All fields are required"}), 400

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid username or password"}), 401

        session["user_id"] = user.id
        session["username"] = user.username

        return jsonify({"status": "logged_in", "username": user.username}), 200

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    return jsonify({"status": "logged_out"}), 200


@app.route("/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"user": None}), 200
    return jsonify({
        "user": {
            "id": session["user_id"],
            "username": session["username"]
        }
    }), 200


# ===== Main Routes =====

@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    chat_id = data.get("chat_id")
    image_base64 = data.get("image")
    image_type = data.get("image_type")

    if not message and not image_base64:
        return jsonify({"error": "Message or image required"}), 400

    if len(message) > 1000:
        return jsonify({"error": "Message cannot exceed 1000 characters"}), 400

    # Get or create chat
    if chat_id:
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
        if chat.user_id != session["user_id"]:
            return jsonify({"error": "Forbidden"}), 403
    else:
        title_source = message if message else "Image chat"
        title = title_source[:50] + ("..." if len(title_source) > 50 else "")
        chat = Chat(title=title, user_id=session["user_id"])
        db.session.add(chat)
        db.session.commit()
        chat_id = chat.id

    # Save user message
    user_content = message if message else "[Image]"
    user_msg = Message(chat_id=chat_id, role="user", content=user_content)
    db.session.add(user_msg)
    db.session.commit()

    # Build history from DB (skip image-only placeholders)
    history = [
        {"role": m.role, "content": m.content}
        for m in chat.messages
        if not m.content.startswith("[Image]")
    ]

    # Build API messages
    if image_base64 and image_type:
        # Multimodal message
        user_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": message if message else "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image_type};base64,{image_base64}"
                    }
                }
            ]
        }
        model = "meta-llama/llama-4-scout-17b-16e-instruct"
    else:
        user_message = {"role": "user", "content": message}
        model = "openai/gpt-oss-120b"

    # Replace the last user message with multimodal version
    api_messages = history[:-1] + [user_message] if history else [user_message]

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
                messages=[system_prompt] + api_messages,
                model=model,
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

        ai_msg = Message(chat_id=chat_id, role="assistant", content=full_reply)
        db.session.add(ai_msg)
        db.session.commit()

    return app.response_class(generate(), mimetype="text/plain")


@app.route("/chats", methods=["GET"])
@login_required
def get_chats():
    chats = Chat.query.filter_by(user_id=session["user_id"]).order_by(Chat.updated_at.desc()).all()
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
@login_required
def create_chat():
    chat = Chat(title="New Chat", user_id=session["user_id"])
    db.session.add(chat)
    db.session.commit()
    return jsonify({"id": chat.id, "title": chat.title}), 201


@app.route("/chats/<int:chat_id>", methods=["DELETE"])
@login_required
def delete_chat(chat_id):
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    if chat.user_id != session["user_id"]:
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(chat)
    db.session.commit()
    return jsonify({"status": "deleted"})


@app.route("/history/<int:chat_id>", methods=["GET"])
@login_required
def get_history(chat_id):
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    if chat.user_id != session["user_id"]:
        return jsonify({"error": "Forbidden"}), 403

    history = [
        {"role": m.role, "content": m.content}
        for m in chat.messages
    ]
    return jsonify({"history": history})


@app.route("/history/<int:chat_id>", methods=["DELETE"])
@login_required
def clear_history(chat_id):
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    if chat.user_id != session["user_id"]:
        return jsonify({"error": "Forbidden"}), 403

    Message.query.filter_by(chat_id=chat_id).delete()
    db.session.commit()
    return jsonify({"status": "cleared"})


# ===== Init DB =====
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, port=5001)