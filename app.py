from flask import Flask, render_template, request, redirect, session
import pandas as pd

app = Flask(__name__)
app.secret_key = "joynesspanda05"

dosya = "joyness_stoktakibi.xlsx"

# 📦 GEÇİCİ LİSTELER (kategori & yayın ekleme için)
kategoriler_listesi = []
yayinlar_listesi = []


# VERİ YÜKLE
def yukle():
    try:
        df = pd.read_excel(dosya)

        df.columns = df.columns.str.strip().str.lower()

        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).str.strip()

        if "barkod" in df.columns:
            df["barkod"] = df["barkod"].astype(str).str.strip()

        if "yayin" in df.columns:
            df["yayin"] = df["yayin"].fillna("").astype(str).str.strip()

        if "id" not in df.columns:
            df["id"] = range(1, len(df) + 1)

        df["id"] = df["id"].fillna(0).astype(int)

        return df

    except:
        return pd.DataFrame(columns=[
            "barkod","kitap_adi","kategori","alt_kategori","yayin","stok","id"
        ])


# KAYDET
def kaydet(df):
    df.to_excel(dosya, index=False)


# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["sifre"] == "joynesspanda05":
            session["giris"] = True
            return redirect("/panel")
    return render_template("login.html")


# PANEL
@app.route("/panel")
def panel():
    if not session.get("giris"):
        return redirect("/")
    return render_template("panel.html")


# ÜRÜNLER
@app.route("/urunler")
def urunler():
    df = yukle()
    data = df.to_dict(orient="records")

    kategoriler = sorted(df["kategori"].dropna().unique()) if "kategori" in df.columns else []
    yayinlar = sorted(df["yayin"].dropna().unique()) if "yayin" in df.columns else []

    return render_template(
        "urunler.html",
        data=data,
        kategoriler=kategoriler,
        yayinlar=yayinlar
    )


# KATEGORİ FİLTRE
@app.route("/kategori/<kat>")
def kategori_filtre(kat):
    df = yukle()
    data = df[df["kategori"] == kat].to_dict(orient="records")

    kategoriler = sorted(df["kategori"].dropna().unique()) if "kategori" in df.columns else []
    yayinlar = sorted(df["yayin"].dropna().unique()) if "yayin" in df.columns else []

    return render_template(
        "urunler.html",
        data=data,
        kategoriler=kategoriler,
        yayinlar=yayinlar
    )


# ÜRÜN DETAY
@app.route("/urun/<barkod>")
def urun_detay(barkod):
    df = yukle()

    urun = df[df["barkod"] == str(barkod).strip()]

    if urun.empty:
        return "Ürün yok"

    u = urun.iloc[0].to_dict()

    return render_template("urun_detay.html", u=u)


# DÜZENLE
@app.route("/duzenle/<int:id>", methods=["GET","POST"])
def duzenle(id):
    df = yukle()

    if request.method == "POST":
        df.loc[df["id"] == id, "kitap_adi"] = request.form["isim"]
        df.loc[df["id"] == id, "kategori"] = request.form["kategori"]
        df.loc[df["id"] == id, "alt_kategori"] = request.form["alt_kategori"]
        df.loc[df["id"] == id, "yayin"] = request.form["yayin"]
        df.loc[df["id"] == id, "stok"] = int(request.form["stok"])

        kaydet(df)
        return redirect("/urunler")

    urun = df[df["id"] == id]

    if urun.empty:
        return "Ürün bulunamadı"

    u = urun.iloc[0].to_dict()

    return render_template("duzenle.html", u=u)


# EKLE
@app.route("/ekle", methods=["GET","POST"])
def ekle():
    if request.method == "POST":
        df = yukle()

        yeni = {
            "barkod": request.form["barkod"],
            "kitap_adi": request.form["isim"],
            "kategori": request.form["kategori"],
            "alt_kategori": request.form["alt_kategori"],
            "yayin": request.form["yayin"],
            "stok": int(request.form["stok"])
        }

        df = pd.concat([df, pd.DataFrame([yeni])], ignore_index=True)
        df["id"] = range(1, len(df) + 1)

        kaydet(df)
        return redirect("/urunler")

    return render_template(
        "ekle.html",
        kategoriler=kategoriler_listesi,
        yayinlar=yayinlar_listesi
    )


# ÇIKIŞ
@app.route("/cikis")
def cikis():
    session.clear()
    return redirect("/")


# ➕ STOK ARTTIR
@app.route("/stok-arttir/<int:id>")
def stok_arttir(id):
    df = yukle()
    df.loc[df["id"] == id, "stok"] = df.loc[df["id"] == id, "stok"] + 1
    kaydet(df)
    return redirect("/urunler")


# ➖ STOK AZALT
@app.route("/stok-azalt/<int:id>")
def stok_azalt(id):
    df = yukle()
    df.loc[df["id"] == id, "stok"] = df.loc[df["id"] == id, "stok"] - 1
    df.loc[df["stok"] < 0, "stok"] = 0
    kaydet(df)
    return redirect("/urunler")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
