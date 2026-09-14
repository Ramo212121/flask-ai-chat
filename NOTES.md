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
