from flask import Flask, render_template, request, redirect, session, jsonify
import pandas as pd

app = Flask(__name__)
app.secret_key = "joynesspanda05"

dosya = "joyness_stoktakibi.xlsx"


# ---------------- VERİ ----------------
def yukle():
    try:
        df = pd.read_excel(dosya)

        df.columns = df.columns.str.strip().str.lower()

        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).str.strip()

        if "barkod" in df.columns:
            df["barkod"] = df["barkod"].astype(str)

        if "id" not in df.columns:
            df["id"] = range(1, len(df) + 1)

        df["id"] = df["id"].fillna(0).astype(int)

        if "stok" not in df.columns:
            df["stok"] = 0

        df["stok"] = pd.to_numeric(df["stok"], errors="coerce").fillna(0).astype(int)

        return df

    except:
        return pd.DataFrame(columns=[
            "barkod","kitap_adi","kategori","alt_kategori","yayin","stok","id"
        ])


def kaydet(df):
    df.to_excel(dosya, index=False)


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["sifre"] == "joynesspanda05":
            session["giris"] = True
            return redirect("/panel")
    return render_template("login.html")


# ---------------- PANEL ----------------
@app.route("/panel")
def panel():
    if not session.get("giris"):
        return redirect("/")
    return render_template("panel.html")


# ---------------- ÜRÜNLER ----------------
@app.route("/urunler")
def urunler():
    if not session.get("giris"):
        return redirect("/")

    df = yukle()

    data = df.to_dict(orient="records")

    kategoriler = sorted(df["kategori"].dropna().unique()) if "kategori" in df else []
    yayinlar = sorted(df["yayin"].dropna().unique()) if "yayin" in df else []

    return render_template(
        "urunler.html",
        data=data,
        kategoriler=kategoriler,
        yayinlar=yayinlar
    )


# ---------------- ÜRÜN DETAY ----------------
@app.route("/urun/<barkod>")
def urun_detay(barkod):
    df = yukle()

    urun = df[df["barkod"] == str(barkod)]

    if urun.empty:
        return "Ürün yok"

    return render_template("urun_detay.html", u=urun.iloc[0])


# ---------------- DÜZENLE ----------------
@app.route("/duzenle/<int:id>", methods=["GET","POST"])
def duzenle(id):
    df = yukle()
    df["id"] = df["id"].astype(int)

    if request.method == "POST":
        try:
            if id not in df["id"].values:
                return "ID bulunamadı"

            df.loc[df["id"] == id, "kitap_adi"] = request.form.get("isim","")
            df.loc[df["id"] == id, "kategori"] = request.form.get("kategori","")
            df.loc[df["id"] == id, "alt_kategori"] = request.form.get("alt_kategori","")
            df.loc[df["id"] == id, "yayin"] = request.form.get("yayin","")

            try:
                stok = int(request.form.get("stok","0"))
            except:
                stok = 0

            df.loc[df["id"] == id, "stok"] = stok

            kaydet(df)

        except Exception as e:
            return f"HATA: {e}"

        return redirect("/urunler")

    urun = df[df["id"] == id]

    if urun.empty:
        return "Ürün bulunamadı"

    return render_template("duzenle.html", u=urun.iloc[0])


# ---------------- EKLE ----------------
@app.route("/ekle", methods=["GET","POST"])
def ekle():
    if request.method == "POST":
        df = yukle()

        try:
            stok = int(request.form.get("stok","0"))
        except:
            stok = 0

        yeni = {
            "barkod": request.form.get("barkod",""),
            "kitap_adi": request.form.get("isim",""),
            "kategori": request.form.get("kategori",""),
            "alt_kategori": request.form.get("alt_kategori",""),
            "yayin": request.form.get("yayin",""),
            "stok": stok
        }

        df = pd.concat([df, pd.DataFrame([yeni])], ignore_index=True)
        df["id"] = range(1, len(df) + 1)

        kaydet(df)

        return redirect("/urunler")

    return render_template("ekle.html")


# ---------------- STOK (ANINDA) ----------------
@app.route("/stok-guncelle", methods=["POST"])
def stok_guncelle():
    data = request.get_json()

    id = int(data["id"])
    degisim = int(data["degisim"])

    df = yukle()
    df["id"] = df["id"].astype(int)

    if id not in df["id"].values:
        return jsonify({"stok": 0})

    df.loc[df["id"] == id, "stok"] += degisim
    df.loc[df["stok"] < 0, "stok"] = 0

    stok = int(df.loc[df["id"] == id, "stok"].values[0])

    kaydet(df)

    return jsonify({"stok": stok})


# ---------------- KAMERA ----------------
@app.route("/kamera")
def kamera():
    return """
    <html>
    <head>
    <script src="https://unpkg.com/html5-qrcode"></script>
    </head>
    <body style="text-align:center;font-family:Arial;">
    <h2>Barkod Oku</h2>
    <div id="reader" style="width:300px;margin:auto;"></div>

    <script>
    function onScanSuccess(text) {
        window.location.href = "/urun/" + text;
    }

    new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 })
        .render(onScanSuccess);
    </script>
    </body>
    </html>
    """


# ---------------- ÇIKIŞ ----------------
@app.route("/cikis")
def cikis():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
