# Flask vs Django — Learning Notes

A daily log of what I built, what I learned, how it compares to Django, and where I needed help.
Project: **Flask AI Chat** — a full-stack AI chat app with streaming responses.

---

## Day 1 — First Route & Project Setup

### What I built
- Flask app with a single `/` route
- Rendered an HTML template
- Set up the project structure (venv, .gitignore, .env)

### What I learned
- `Flask(__name__)` creates the app
- `@app.route("/")` binds a URL to a view function
- `render_template()` returns HTML from `templates/`
- `app.run(debug=True)` starts the dev server

### Django comparison
| Flask | Django |
|-------|--------|
| `Flask(__name__)` | `django-admin startproject` |
| `@app.route("/")` + view | `urls.py` + `views.py` (separate) |
| `app.run(debug=True)` | `python manage.py runserver` |

### Where I needed help
- Understanding why `venv` was needed
- How `pip` installs into the venv (Anaconda conflicts)
- Fixing the `ModuleNotFoundError: No module named 'flask'`

### Honest note
Django felt more "structured" but Flask showed me what's actually happening under the hood.

---

## Day 2 — Template Inheritance & Static Files

### What I built
- `base.html` as the main layout
- `index.html` inheriting from base
- Custom CSS and JS in `static/`

### What I learned
- `{% extends "base.html" %}` = template inheritance
- `{% block content %}` = fillable placeholder
- `url_for('static', filename='...')` generates static URLs

### Django comparison
| Flask | Django |
|-------|--------|
| `{% extends %}` + `{% block %}` | Same syntax |
| `url_for('static', filename='...')` | `{% static '...' %}` |
| `url_for('index')` | `{% url 'index' %}` |

### Where I needed help
- Understanding the difference between `base.html` and `index.html`
- Why `{% extends %}` must be the first line
- Fixing the missing CSS (because `{% extends %}` was missing)

### Honest note
Template inheritance is **identical** in both. Only static/URL syntax differs.

---

## Day 3 — Form Handling & Validation

### What I built
- `POST /chat` endpoint
- Manual validation (empty? too long?)
- JSON response with `jsonify()`
- Frontend POST with `fetch()`

### What I learned
- `methods=["POST"]` restricts HTTP methods
- `request.get_json()` parses JSON body
- `jsonify()` returns JSON response
- `return ..., 400` sends HTTP status codes

### Django comparison
| Flask | Django |
|-------|--------|
| `methods=["POST"]` in decorator | `if request.method == "POST"` inside view |
| `request.get_json()` | `json.loads(request.body)` |
| `jsonify()` | `JsonResponse()` |
| Manual validation | `forms.py` auto-validates |

### Where I needed help
- Understanding `try/except` indentation in Python
- Why `return` was "outside function" (indentation error)
- Debugging the `fetch` frontend connection

### Honest note
**Django's forms are a huge time-saver.** Flask forces you to write validation manually, which is good for learning but slow for real projects.

---

## Day 4 — Session & Chat History

### What I built
- Session-based chat history with Flask `session`
- `/history` GET and DELETE endpoints
- Frontend loads history on page load
- Clear button resets both UI and session

### What I learned
- `session["key"] = value` stores data per-user
- `session.get("key", default)` reads safely
- `session.pop("key", None)` deletes
- `app.secret_key` is **required** for session
- macOS AirPlay uses port 5000 → Flask runs on 5001

### Django comparison
| Flask | Django |
|-------|--------|
| `session["key"]` | `request.session["key"]` |
| Cookie-based (signed) | DB-backed by default |
| `app.secret_key` | `SECRET_KEY` in settings |

### Where I needed help
- Why session wasn't working (missing `app.secret_key`)
- Fixing port conflict (AirPlay vs Flask)
- Understanding cookie vs DB sessions

### Honest note
Flask sessions are **cookie-based** (limited to ~4KB). Django's DB-backed sessions scale better. For chat history, DB is the right choice long-term — that's why Day 11 (SQLite) matters.

---

## Day 5 — Groq AI Integration + UI Polish

### What I built
- Integrated Groq API (`openai/gpt-oss-120b`)
- System prompt for AI identity
- Background video from Pexels
- Google Fonts (Inter + Space Grotesk)
- Glassmorphism UI
- Custom logo

### What I learned
- Groq is OpenAI-compatible → easy migration
- `chat.completions.create(messages=..., model=...)` pattern
- System prompt controls AI behavior
- System prompt goes first in messages array
- **System prompt is NOT stored in session** (re-sent every request)

### Django comparison
| Flask | Django |
|-------|--------|
| Same Groq SDK | Same Groq SDK |
| Only endpoint differs | Only view differs |
| Framework-agnostic AI calls | Framework-agnostic AI calls |

### Where I needed help
- **Gemini failed** with 403 (school account blocked)
- Switching to Groq as alternative
- Finding current Groq model (`llama-3.3-70b-versatile` deprecated)
- Fixing `.env` loading with `Path(__file__).resolve().parent`
- Finding my API key was named wrong (`_API_KEY` instead of `GROQ_API_KEY`)
- Indentation errors in `try/except`

### Honest note
**This was the most frustrating and most educational day.**
- Learned that **alternatives matter** (Gemini → Groq)
- Learned to **read error messages carefully**
- Learned that **engineering is problem-solving**, not memorizing APIs
- Real-world development: try → fail → debug → adapt → succeed

---

## Day 6 — Streaming Responses + Markdown Rendering

### What I built
- Streaming AI responses (word-by-word)
- Markdown rendering (tables, code blocks, headings)
- Local `marked.js` (no CDN dependency)

### What I learned
- `stream=True` in Groq API call
- Python generators: `def generate(): yield ...`
- `app.response_class(generate(), mimetype="text/plain")`
- Frontend: `response.body.getReader()` + `TextDecoder`
- `marked.parse()` converts Markdown → HTML
- Local files are more reliable than CDN

### Django comparison
| Flask | Django |
|-------|--------|
| `app.response_class()` | `StreamingHttpResponse()` |
| Same generator pattern | Same generator pattern |
| Same frontend code | Same frontend code |

### Where I needed help
- Understanding generators and `yield`
- Debugging why streaming didn't work at first
- CDN issues with `marked.js` (`typeof marked` → `undefined`)
- Solution: download `marked.min.js` locally
- Finding the correct CDN URL

### Honest note
**Streaming + Markdown = ChatGPT-level experience.**
- Most tutorials stop at basic chat — streaming is what makes it feel modern
- Debugging CDN issues taught me: **local > remote for reliability**
- This day made the project feel **real**, not just a tutorial clone

---

## Overall Reflections

### What I learned about myself
- I learn best by **building real things**, not watching tutorials
- I need to **see the "why"**, not just the "how"
- I debug better when I **read error messages carefully**
- I progress fastest when I **compare to something I know** (Django)

### What I learned about AI APIs
- **Framework-agnostic**: same SDK works in Flask and Django
- **Always have a backup**: Gemini failed → Groq worked
- **System prompts are essential**: define AI identity
- **Model names change**: keep up with deprecations

### What I learned about Flask vs Django
- **Flask**: minimal, explicit, great for learning
- **Django**: opinionated, batteries-included, great for production
- **Flask taught me** what Django does for me automatically
- **Both are valid** — the right choice depends on the project

### Honest admission
- I used AI assistance (ChatGPT/Claude) heavily throughout this project
- I did **not** memorize every line — I understood the logic
- I made **many mistakes** (indentation, env files, port conflicts)
- **This is normal.** Real engineers do this every day.

### What's next
- Day 7+: UI polish, database, deployment
- After this project: build something bigger
- Long-term goal: strong GitHub portfolio by graduation

---

## Technical Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask (Python) |
| AI | Groq API (`openai/gpt-oss-120b`) |
| Frontend | Vanilla JS + HTML + CSS |
| Markdown | marked.js (local) |
| Fonts | Google Fonts (Inter, Space Grotesk) |
| Media | Pexels (background video) |
| Version control | Git + GitHub |

---

## Port Note
On macOS, AirPlay uses port 5000. Flask runs on 5001.
URL: `http://127.0.0.1:5001`