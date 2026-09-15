import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session
from google import genai


app = Flask(__name__)

load_dotenv()
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
@app.route("/chat", methods=["POST"])
def chat():
    # 1. Get incoming data
    data = request.get_json()
    message = data.get("message", "").strip()
    
    # 2. Validation
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400
    
    if len(message) > 1000:
        return jsonify({"error": "Message cannot exceed 1000 characters"}), 400
    
    # 3. Get history from session (or start empty)
    history = session.get("history", [])
    
    # 4. Add user message to history
    history.append({"role": "user", "content": message})
    
try:
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=message
    )
    reply = response.text
except Exception as e:
    return jsonify({"error": f"AI error: {str(e)}"}), 500
    
    # 6. Add AI response to history
    history.append({"role": "assistant", "content": reply})
    
    # 7. Save back to session
    session["history"] = history
    
    # 8. Return JSON
    return jsonify({"reply": reply, "history_length": len(history)})

@app.route("/history", methods=["GET"])
def get_history():
    history = session.get("history", [])
    return jsonify({"history": history})

@app.route("/history", methods=["DELETE"])
def clear_history():
    session.pop("history", None)
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True, port=5001)