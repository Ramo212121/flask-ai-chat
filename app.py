from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

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
    
    # 3. Fake response for now (real AI comes on Day 5-6)
    reply = f"You said: '{message}'. AI integration coming soon!"
    
    # 4. Return as JSON
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)