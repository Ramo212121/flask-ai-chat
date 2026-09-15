# Flask vs Django — Notlar

## Gün 1 — İlk Route

### Flask'ta nasıl yaptım?
- Flask(__name__) ile app oluşturdum
- @app.route("/") ile URL tanımladım
- render_template() ile HTML döndüm
- app.run(debug=True) ile çalıştırdım

### Django'da karşılığı?
- urls.py → path("", views.index)
- views.py → def index(request): return render(request, "index.html")
- manage.py runserver

### Fark?
- Flask: route + view aynı yerde, minimal
- Django: URL ve view ayrı, settings.py merkezli



## Gün 2 — Template Inheritance + Static

### Flask'ta nasıl yaptım?
- base.html oluşturdum (ana şablon)
- index.html → {% extends "base.html" %} ile miras aldı
- {% block content %} ile içerik doldurdum
- url_for('static', filename='...') ile CSS/JS bağladım

### Django'da karşılığı?
- Template inheritance aynı: {% extends %} + {% block %}
- Static için: {% load static %} + {% static 'css/style.css' %}
- URL için: {% url 'index' %} (Flask'ta url_for('index'))

### Fark?
- Flask: url_for('static', filename='css/style.css')
- Django: {% static 'css/style.css' %}