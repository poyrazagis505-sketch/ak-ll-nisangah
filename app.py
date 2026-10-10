from flask import Flask, request, render_template_string

app = Flask(__name__)

magazines = {
    "NFC_001": {"name": "A01", "rounds": 30},
    "NFC_002": {"name": "A02", "rounds": 28},
}

events = []

@app.route("/")
def index():
    return render_template_string("""
    <!doctype html>
    <html>
    <head>
        <title>Mühimmat Takip</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 30px; }
            .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,.08); margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            input, button { padding: 10px; margin: 5px 0; }
            button { background: #2563eb; color: white; border: none; border-radius: 8px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📦 Elektronik Mühimmat Takip Sistemi</h1>

            <form method="POST" action="/add">
                <input name="nfc_id" placeholder="NFC ID" value="NFC_003" />
                <input name="name" placeholder="Şarjör Adı" value="A03" />
                <input name="rounds" type="number" value="30" />
                <button type="submit">Şarjör Ekle</button>
            </form>
        </div>

        <div class="card">
            <h2>Şarjör Listesi</h2>
            <table>
                <tr><th>NFC</th><th>Ad</th><th>Kalan Fişek</th><th>Aksiyon</th></tr>
                {% for nfc, mag in magazines.items() %}
                <tr>
                    <td>{{ nfc }}</td>
                    <td>{{ mag['name'] }}</td>
                    <td>{{ mag['rounds'] }}</td>
                    <td><a href="/fire/{{ nfc }}">Ateş Et</a></td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div class="card">
            <h2>Olay Geçmişi</h2>
            <ul>
                {% for e in events %}
                    <li>{{ e }}</li>
                {% endfor %}
            </ul>
        </div>
    </body>
    </html>
    """, magazines=magazines, events=events)

@app.route("/add", methods=["POST"])
def add_magazine():
    nfc = request.form["nfc_id"]
    name = request.form["name"]
    rounds = int(request.form["rounds"])
    magazines[nfc] = {"name": name, "rounds": rounds}
    events.append(f"{nfc} şarjörü eklendi.")
    return index()

@app.route("/fire/<nfc_id>")
def fire(nfc_id):
    if nfc_id in magazines:
        if magazines[nfc_id]["rounds"] > 0:
            magazines[nfc_id]["rounds"] -= 1
            events.append(f"{nfc_id} ateş edildi. Kalan: {magazines[nfc_id]['rounds']}")
        else:
            events.append(f"{nfc_id} boş şarjör.")
    return index()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
