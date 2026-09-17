import os
import io
import json
import re
from pathlib import Path
from functools import wraps
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq
import pdfplumber
from gtts import gTTS

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-key-change-me")

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ===== Security Headers =====

@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


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


# ===== Tool Definitions =====

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current local time for a given city. Use when the user asks about time in a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name, e.g., 'Istanbul', 'London', 'Tokyo'"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_map",
            "description": "Generate a map link for a location. Use when the user asks about a place, city, or directions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location name to show on a map"
                    }
                },
                "required": ["location"]
            }
        }
    }
]


def execute_tool(tool_name, arguments):
    """Execute a tool and return its result as a string."""
    if tool_name == "get_time":
        city = arguments.get("city", "Unknown")
        timezones = {
            "istanbul": 3, "ankara": 3, "izmir": 3,
            "london": 0, "paris": 1, "berlin": 1,
            "moscow": 3, "dubai": 4, "tokyo": 9,
            "new york": -5, "los angeles": -8,
            "beijing": 8, "singapore": 8,
        }
        city_key = city.lower().strip()
        offset = timezones.get(city_key, 0)
        tz = timezone(timedelta(hours=offset))
        now = datetime.now(tz)
        return f"The current time in {city} is {now.strftime('%H:%M')} (UTC{offset:+d})."

    elif tool_name == "show_map":
        location = arguments.get("location", "")
        encoded = location.replace(" ", "+")
        return f"[📍 View {location} on map](https://www.openstreetmap.org/search?query={encoded})"

    return f"Unknown tool: {tool_name}"


# ===== Auth Routes =====

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per minute")
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
@limiter.limit("5 per minute")
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


# ===== PDF Upload Route =====

@app.route("/upload-pdf", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def upload_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "No PDF file"}), 400

    file = request.files["pdf"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files allowed"}), 400

    try:
        text = ""
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

        if len(text) > 20000:
            text = text[:20000] + "\n\n[... text truncated ...]"

        if not text.strip():
            return jsonify({"error": "Could not extract text from PDF (maybe scanned image?)"}), 400

        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": f"PDF error: {str(e)}"}), 500


# ===== Text-to-Speech Route =====

@app.route("/speak", methods=["POST"])
@login_required
@limiter.limit("15 per minute")
def speak():
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Clean markdown
    clean_text = re.sub(r'```[\s\S]*?```', '', text)
    clean_text = re.sub(r'[#*`_~]', '', clean_text)
    clean_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_text)
    clean_text = re.sub(r'\n+', ' ', clean_text).strip()

    if not clean_text:
        return jsonify({"error": "No text to speak"}), 400

    has_turkish = bool(re.search(r'[ğüşıöçĞÜŞİÖÇ]', clean_text))
    lang = "tr" if has_turkish else "en"

    try:
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        return send_file(
            audio_buffer,
            mimetype="audio/mpeg",
            as_attachment=False
        )
    except Exception as e:
        return jsonify({"error": f"TTS error: {str(e)}"}), 500


# ===== Speech-to-Text Route =====

@app.route("/transcribe", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file"}), 400

    audio_file = request.files["audio"]

    if audio_file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        transcription = groq_client.audio.transcriptions.create(
            file=(audio_file.filename, audio_file.read()),
            model="whisper-large-v3-turbo",
            response_format="text",
        )

        text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()

        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": f"Transcription error: {str(e)}"}), 500


# ===== Main Routes =====

@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    chat_id = data.get("chat_id")
    image_base64 = data.get("image")
    image_type = data.get("image_type")
    only_emoji = data.get("only_emoji", False)
    pdf_text = data.get("pdf_text", "").strip()

    if not message and not image_base64 and not pdf_text:
        return jsonify({"error": "Message, image, or PDF required"}), 400

    # Stronger validation
    if len(message) > 1000:
        return jsonify({"error": "Message too long (max 1000 chars)"}), 400

    if any(ord(c) < 32 and c not in "\n\t\r" for c in message):
        return jsonify({"error": "Invalid characters in message"}), 400

    message = message.replace("\x00", "").strip()

    # Get or create chat
    if chat_id:
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
        if chat.user_id != session["user_id"]:
            return jsonify({"error": "Forbidden"}), 403
    else:
        if message:
            title_source = message
        elif pdf_text:
            title_source = "PDF chat"
        else:
            title_source = "Image chat"
        title = title_source[:50] + ("..." if len(title_source) > 50 else "")
        chat = Chat(title=title, user_id=session["user_id"])
        db.session.add(chat)
        db.session.commit()
        chat_id = chat.id

    # Save user message
    if message:
        user_content = message
    elif pdf_text:
        user_content = "[PDF]"
    else:
        user_content = "[Image]"

    user_msg = Message(chat_id=chat_id, role="user", content=user_content)
    db.session.add(user_msg)
    db.session.commit()

    # Build history from DB
    history = [
        {"role": m.role, "content": m.content}
        for m in chat.messages
        if not m.content.startswith("[Image]") and not m.content.startswith("[PDF]")
    ]

    # Model selection
    requested_model = data.get("model", "openai/gpt-oss-120b")

    ALLOWED_MODELS = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",   # ← DOĞRU
    ]

    if requested_model not in ALLOWED_MODELS:
        requested_model = "openai/gpt-oss-120b"

    # Build user message
    if pdf_text:
        combined_message = (
            f"Here is the content of a PDF document:\n\n{pdf_text}\n\n"
            f"---\n\nUser question: {message if message else 'Please summarize this document.'}"
        )
        user_message = {"role": "user", "content": combined_message}
    elif image_base64 and image_type:
        if "qwen" not in requested_model:
            requested_model = "qwen/qwen3.8-27b" 

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
    else:
        user_message = {"role": "user", "content": message}

    model = requested_model

    api_messages = history[:-1] + [user_message] if history else [user_message]

    system_prompt = {
        "role": "system",
        "content": (
            "You are a friendly, helpful AI companion. "
            "Your name is 'Flask AI Chat'. "
            "Be warm and casual, but still helpful and clear. "
            "Match the user's tone — if they're casual, be casual; "
            "if they're formal, be formal. "
            "Avoid robotic phrases like 'How may I assist you?' "
            "Never claim to be ChatGPT, GPT-4, or any OpenAI product. "
            "Always reply in the same language the user writes in. "
            "If the user sends only emojis or non-text content, reply in English."
        )
    }

    def generate():
        full_reply = ""
        try:
            use_tools = not image_base64 and not only_emoji and not pdf_text

            if use_tools:
                response = groq_client.chat.completions.create(
                    messages=[system_prompt] + api_messages,
                    model=model,
                    tools=TOOLS,
                    tool_choice="auto",
                    stream=False,
                )
                msg = response.choices[0].message

                if msg.tool_calls:
                    api_messages.append(msg)

                    for tool_call in msg.tool_calls:
                        args = json.loads(tool_call.function.arguments)
                        result = execute_tool(tool_call.function.name, args)

                        api_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        })

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
                else:
                    if msg.content:
                        full_reply = msg.content
                        yield full_reply
            else:
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


# ===== Error Handlers =====

@app.errorhandler(400)
def bad_request(e):
    if request.is_json:
        return jsonify({"error": "Bad request"}), 400
    return render_template("errors/400.html"), 400


@app.errorhandler(401)
def unauthorized(e):
    if request.is_json:
        return jsonify({"error": "Unauthorized"}), 401
    return redirect(url_for("login_page"))


@app.errorhandler(403)
def forbidden(e):
    if request.is_json:
        return jsonify({"error": "Forbidden"}), 403
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def not_found(e):
    if request.is_json:
        return jsonify({"error": "Not found"}), 404
    return render_template("errors/404.html"), 404


@app.errorhandler(429)
def rate_limit_exceeded(e):
    if request.is_json:
        return jsonify({"error": "Too many requests. Please slow down."}), 429
    return render_template("errors/429.html"), 429


@app.errorhandler(500)
def server_error(e):
    if request.is_json:
        return jsonify({"error": "Server error"}), 500
    return render_template("errors/500.html"), 500


# ===== Init DB =====
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, port=5001)