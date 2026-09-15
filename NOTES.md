# Flask vs Django — Notes

## Day 1 — First Route

### How I did it in Flask?
- Created the app with Flask(__name__)
- Defined the URL with @app.route("/")
- Returned HTML with render_template()
- Ran it with app.run(debug=True)

### Django equivalent?
- urls.py → path("", views.index)
- views.py → def index(request): return render(request, "index.html")
- manage.py runserver

### Difference?
- Flask: route + view in the same place, minimal
- Django: URL and view are separate, settings.py-centric


## Day 2 — Template Inheritance + Static

### How I did it in Flask?
- Created base.html (main template)
- index.html inherits via {% extends "base.html" %}
- Filled content with {% block content %}
- Linked CSS/JS with url_for('static', filename='...')

### Django equivalent?
- Template inheritance is the same: {% extends %} + {% block %}
- For static: {% load static %} + {% static 'css/style.css' %}
- For URLs: {% url 'index' %} (in Flask: url_for('index'))

### Difference?
- Flask: url_for('static', filename='css/style.css')
- Django: {% static 'css/style.css' %}


## Day 3 — Form Handling + Validation

### How I did it in Flask?
- Wrote a POST endpoint at /chat
- Read JSON data with request.get_json()
- Manual validation: empty? longer than 1000 chars?
- Returned JSON with jsonify()
- Returned status 400 on error
- Sent POST from frontend with fetch

### Django equivalent?
- urls.py: path("chat/", views.chat)
- views.py: if request.method == "POST" check
- JsonResponse for JSON return
- Django Forms handles validation automatically (ModelForm)

### Difference?
- Flask: method check in decorator (@app.route(methods=))
- Django: method check inside view (if request.method ==)
- Flask: validation is manual
- Django: validation is automatic via Forms


## Day 4 — Session & Chat History

### How I did it in Flask?
- Used Flask session to store chat history
- Each message has role (user/assistant) and content
- On page load, frontend fetches /history to restore
- Clear button calls DELETE /history to reset
- Set app.secret_key for session encryption
- Changed port to 5001 (macOS AirPlay uses 5000)

### Django equivalent?
- request.session.get("history", [])
- Django sessions are DB-backed by default
- Flask sessions are cookie-based

### Difference?
- Flask: session["key"] = value (cookie-based, signed)
- Django: request.session["key"] = value (DB or cache)
- Both require a secret key


## Port Note
On macOS, AirPlay uses port 5000, so Flask runs on 5001.
URL: http://127.0.0.1:5001