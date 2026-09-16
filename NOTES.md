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



## Day 7 — UI/UX + Sidebar

### What I built
- Sidebar layout (visual only, no data yet)
- New Chat button (placeholder)
- Mobile responsive with drawer
- Message timestamp
- Typing indicator (3-dot animation)
- Header split into left (logo) + right (user menu)

### What I learned
- Flexbox for two-column layout
- CSS media queries for mobile (768px, 480px)
- `position: fixed` + `transform` for drawer
- JavaScript `Date` API for timestamps
- CSS animations (`@keyframes`) for typing dots
- Event delegation for click-outside

### Django comparison
| Flask | Django |
|-------|--------|
| Plain HTML/CSS | Same, but Django templates |
| `{% extends %}` in templates | Same |
| No form helpers | Django has `{{ form.as_p }}` |

### Where I needed help
- CSS flexbox layout
- Responsive design breakpoints
- CSS animations
- Sidebar toggle logic
- Missing CSS when `{% extends %}` was missing

### Honest note
UI is where projects stand out. Most tutorials skip this. I'm building it step by step.




## Day 8 — Database (SQLite + SQLAlchemy)

### What I built
- SQLite database with SQLAlchemy ORM
- Three models: `User`, `Chat`, `Message`
- Relationships: User → Chat → Message (1-to-N, 1-to-N)
- Cascade delete (delete chat → delete its messages)
- Migrated from session-based history to DB-based storage
- New endpoints: `/chats` (GET, POST, DELETE)
- Updated `/history` to use `chat_id` instead of session

### What I learned
- ORM (Object-Relational Mapping) — write Python, not SQL
- `db.Column()` types: Integer, String, Text, DateTime
- Primary key (`id`) and Foreign key (`user_id`, `chat_id`)
- `db.relationship()` for 1-to-N relationships
- `cascade="all, delete-orphan"` for auto-delete
- `db.session.add()` + `db.session.commit()` to save
- `Model.query.get()` / `.filter_by().first()` to read
- `db.create_all()` inside `with app.app_context():`

### Django comparison
| Flask + SQLAlchemy | Django ORM |
|--------------------|------------|
| `db.Model` | `models.Model` |
| `db.Column(db.String(80))` | `models.CharField(max_length=80)` |
| `db.Column(db.Text)` | `models.TextField()` |
| `db.Column(db.DateTime)` | `models.DateTimeField()` |
| `db.ForeignKey("user.id")` | `models.ForeignKey(User, ...)` |
| `db.relationship()` | `related_name` |
| `db.create_all()` | `makemigrations` + `migrate` |
| `db.session.add()` + `commit()` | `Model.objects.create()` |
| `Model.query.get(id)` | `Model.objects.get(id=id)` |
| `Model.query.filter_by(...).all()` | `Model.objects.filter(...)` |

### Where I needed help
- Understanding ORM vs raw SQL
- Foreign key concept
- Cascade delete behavior
- Why `app_context()` is needed
- Why `db.session.commit()` is required
- `.gitignore` for `instance/` and `*.db`

### Honest note
Django's migrations are more robust (versioned, reversible). Flask's `create_all()` is simpler but less flexible. For a learning project, `create_all()` is enough. For production, migrations matter.

### Impact
- Session 4 KB limit is gone — now unlimited messages
- Data persists across server restarts
- Ready for multi-user (Day 9) and multi-chat (Day 10)


## Day 9 — Login / Register

### What I built
- User registration with validation (username, email, password)
- Login with password verification
- Password hashing with `werkzeug.security`
- Session-based authentication (`session["user_id"]`)
- `@login_required` decorator (custom)
- Logout endpoint
- `/me` endpoint (returns current user)
- Login + Register HTML pages
- Header user menu (username + Logout button)
- Protected routes: `/`, `/chat`, `/chats`, `/history`

### What I learned
- Never store plain passwords — always hash
- `generate_password_hash()` and `check_password_hash()`
- Session for auth: `session["user_id"] = user.id`
- Decorator pattern with `@wraps(f)`
- `redirect(url_for("login_page"))` for unauthenticated users
- Ownership check: `if chat.user_id != session["user_id"]` → 403
- HTTP status codes: 400 (bad request), 401 (unauthorized), 403 (forbidden), 409 (conflict)

### Django comparison
| Flask + Werkzeug | Django |
|------------------|--------|
| `generate_password_hash()` | `user.set_password()` |
| `check_password_hash()` | `user.check_password()` |
| `@login_required` (custom, ~8 lines) | `@login_required` (built-in) |
| `session["user_id"] = user.id` | `login(request, user)` |
| `session.pop("user_id")` | `logout(request)` |
| Custom User model | Built-in `User` model |
| Manual validation | Django Forms |
| No CSRF protection yet | CSRF enabled by default |

### Where I needed help
- `@wraps(f)` — why it's needed in decorators
- Difference between authentication and authorization
- Session vs DB storage for "who is logged in"
- Why password hashing is not optional
- Redirect logic with `url_for`
- Checking ownership (user_id) before allowing access

### Honest note
Django's auth system is **much** more complete — user model, permissions, groups, password reset, CSRF, session security all built-in. Building it manually in Flask taught me **what Django does for me automatically**.

This is exactly why I'm learning Flask first — to understand the underlying mechanisms.

### Security considerations (current state)
- ✅ Passwords are hashed
- ✅ Session-based auth
- ✅ Ownership checks on chats
- ⚠️ No CSRF protection yet (Day 20)
- ⚠️ No rate limiting (Day 20)
- ⚠️ No email verification
- ⚠️ No "forgot password" flow
- ⚠️ Session cookie not `Secure` / `HttpOnly` yet

### Impact
- Multi-user support
- Each user has their own chats
- Data privacy per user
- Ready for functional multi-chat sidebar (Day 10)





## Day 10 — Functional Sidebar + Multi-Chat

### What I built
- Sidebar loaded from DB (`/chats` GET)
- New Chat button (creates chat via `/chats` POST)
- Chat list with titles
- Click to open chat (`/history/<id>` GET)
- Delete chat (`/chats/<id>` DELETE)
- Active chat highlighting
- Auto-load chat history per chat
- Mobile: sidebar closes after selection

### What I learned
- Fetching and rendering dynamic lists
- Event delegation (delete button inside chat item)
- `e.stopPropagation()` — prevent click bubbling
- Active state management (CSS class toggle)
- Confirmation before destructive actions
- Auto-reload after mutations (create/delete)
- Selecting elements with `querySelectorAll`

### Django comparison
| Flask | Django |
|-------|--------|
| Manual DOM rendering | Django admin provides this |
| Custom `/chats` endpoint | Django CBV/DRF viewset |
| Manual click handlers | Same |
| `fetch` from frontend | Same, but could use Django templates |

### Where I needed help
- Event bubbling and `stopPropagation`
- Managing `currentChatId` state
- Reloading after mutations
- Active class toggling
- Mobile sidebar auto-close

### Honest note
This is where the project starts to **feel like a real app**. ChatGPT-style sidebar with multiple chats. Most tutorials never go this far.

### Impact
- User can have multiple conversations
- Each chat has its own history
- Sidebar acts like ChatGPT's
- Data persists across sessions (DB)


## Day 11 — Image Upload (Multimodal AI)

### What I built
- 📎 attach button in chat form (next to input)
- Image preview before sending (with × remove button)
- Base64 encoding in browser (FileReader API)
- Sent image + text to Groq
- Switched to Llama 4 Scout model for vision
- Rendered user's image inside chat bubble
- Remove image button
- 5 MB file size limit
- DB stores `[Image]` placeholder for image-only messages

### What I learned
- `FileReader` API for reading files in browser
- `readAsDataURL()` → base64 encoding
- Stripping `data:image/...;base64,` prefix
- Multimodal message format:
  ```python
  {
    "role": "user",
    "content": [
      {"type": "text", "text": "What's this?"},
      {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
    ]
  }
  

## Day 13 — Syntax Highlighting (highlight.js)

### What I built
- Added highlight.js for syntax highlighting
- Two themes: light (github) + dark (github-dark)
- Auto-switching themes based on dark mode toggle
- Highlight applied before copy button
- Language detection from markdown code blocks

### What I learned
- `hljs.highlightElement(el)` — apply highlight to DOM element
- `data-highlighted` attribute prevents re-highlighting
- Link tag with `disabled` attribute for inactive theme
- CDN download for local use
- Syntax highlighting works automatically based on `language-xxx` class
- Overriding highlight.js default styles

### Django comparison
| Flask | Django |
|-------|--------|
| Same JS library | Same |
| Same CSS themes | Same |
| No django-specific code | Same |

### Where I needed help
- Understanding how highlight.js detects language
- Preventing double highlighting
- Theme switching for highlight CSS
- Overriding default background colors
- `dataset` attribute for state tracking

### Honest note
Highlight.js is **dead simple** to add — just 2 files (JS + CSS). Result is beautiful: code blocks look professional (like GitHub or VS Code).

The tricky part was making it work with **dark mode**. Solution: load both themes, enable/disable via `link.disabled`.

### Impact
- Code blocks look professional
- Python, JS, HTML, etc. all supported
- Follows dark/light mode automatically
- Copy button still works
- Project feels like a real IDE