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

        # boş değerleri temizle
        df = df.fillna("")

        # string kolonlar
        for col in ["barkod", "kitap_adi", "kategori", "alt_kategori", "yayin"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # ID
        if "id" not in df.columns:
            df["id"] = range(1, len(df) + 1)

        df["id"] = d.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)

        # STOK (EN ÖNEMLİ FIX)
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

    return render_template(
        "urunler.html",
        data=df.to_dict("records"),
        kategoriler=df["kategori"].dropna().unique() if "kategori" in df else [],
        yayinlar=df["yayin"].dropna().unique() if "yayin" in df else []
    )


# ---------------- DÜZENLE ----------------
@app.route("/duzenle/<int:id>", methods=["GET","POST"])
def duzenle(id):
    df = yukle()

    if request.method == "POST":

        df.loc[df["id"] == id, "kitap_adi"] = request.form.get("isim","")
        df.loc[df["id"] == id, "kategori"] = request.form.get("kategori","")
        df.loc[df["id"] == id, "alt_kategori"] = request.form.get("alt_kategori","")
        df.loc[df["id"] == id, "yayin"] = request.form.get("yayin","")

        try:
            stok = int(request.form.get("stok",0))
        except:
            stok = 0

        df.loc[df["id"] == id, "stok"] = stok

        kaydet(df)
        return redirect("/urunler")

    urun = df[df["id"] == id]
    if urun.empty:
        return "Ürün yok"

    return render_template("duzenle.html", u=urun.iloc[0])


# ---------------- EKLE ----------------
@app.route("/ekle", methods=["GET","POST"])
def ekle():
    if request.method == "POST":
        df = yukle()

        yeni = {
            "barkod": request.form.get("barkod",""),
            "kitap_adi": request.form.get("isim",""),
            "kategori": request.form.get("kategori",""),
            "alt_kategori": request.form.get("alt_kategori",""),
            "yayin": request.form.get("yayin",""),
            "stok": int(request.form.get("stok",0))
        }

        df = pd.concat([df, pd.DataFrame([yeni])], ignore_index=True)
        df["id"] = range(1, len(df) + 1)

        kaydet(df)
        return redirect("/urunler")

    return render_template("ekle.html")


# ---------------- STOK ARTTIR ----------------
@app.route("/stok-arttir/<int:id>")
def stok_arttir(id):
    df = yukle()

    df.loc[df["id"] == id, "stok"] += 1

    kaydet(df)
    return redirect("/urunler")


# ---------------- STOK AZALT ----------------
@app.route("/stok-azalt/<int:id>")
def stok_azalt(id):
    df = yukle()

    df.loc[df["id"] == id, "stok"] -= 1
    df.loc[df["stok"] < 0, "stok"] = 0

    kaydet(df)
    return redirect("/urunler")


# ---------------- STOK AJAX (HIZLI) ----------------
@app.route("/stok-guncelle", methods=["POST"])
def stok_guncelle():
    data = request.get_json()

    id = int(data["id"])
    degisim = int(data["degisim"])

    df = yukle()

    # güvenlik: tip düzeltme
    df["id"] = df["id"].astype(int)
    df["stok"] = pd.to_numeric(df["stok"], errors="coerce").fillna(0).astype(int)

    # ürün var mı kontrol
    if id not in df["id"].values:
        return jsonify({"stok": 0})

    # stok güncelle
    df.loc[df["id"] == id, "stok"] += degisim

    # negatif olmasın
    df.loc[df["stok"] < 0, "stok"] = 0

    # yeni stok
    yeni_stok = int(df.loc[df["id"] == id, "stok"].values[0])

    kaydet(df)

    return 
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
