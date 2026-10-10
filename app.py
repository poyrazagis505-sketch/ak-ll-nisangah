import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mühimmat Takip Sistemi", layout="wide")

if "magazines" not in st.session_state:
    st.session_state.magazines = {}

if "events" not in st.session_state:
    st.session_state.events = []

def add_magazine(nfc_id, name, rounds):
    if nfc_id in st.session_state.magazines:
        return False, "Bu NFC ID zaten kayıtlı."
    st.session_state.magazines[nfc_id] = {
        "name": name,
        "initial": rounds,
        "current": rounds,
        "fired": 0
    }
    st.session_state.events.insert(0, f"✅ {name} ({nfc_id}) eklendi.")
    return True, "Şarjör eklendi."

def fire_magazine(nfc_id):
    if nfc_id not in st.session_state.magazines:
        return False, "Şarjör bulunamadı."
    mag = st.session_state.magazines[nfc_id]
    if mag["current"] <= 0:
        st.session_state.events.insert(0, f"⚠️ {mag['name']} boş şarjör.")
        return False, "Şarjör boş."
    mag["current"] -= 1
    mag["fired"] += 1
    st.session_state.events.insert(0, f"💥 {mag['name']} ateş edildi. Kalan: {mag['current']}")
    return True, "Atış başarılı."

def reload_magazine(nfc_id):
    if nfc_id not in st.session_state.magazines:
        return False, "Şarjör bulunamadı."
    mag = st.session_state.magazines[nfc_id]
    mag["current"] = mag["initial"]
    mag["fired"] = 0
    st.session_state.events.insert(0, f"🔄 {mag['name']} dolduruldu.")
    return True, "Şarjör dolduruldu."

st.title("📦 Elektronik Mühimmat Takip Sistemi")
st.caption("Sandbox simülasyonu — şarjör kimliği, fişek takibi, olay geçmişi")

with st.sidebar:
    st.header("⚙️ Kontrol Paneli")

    with st.form("add_form"):
        nfc_id = st.text_input("NFC ID", "NFC_001")
        name = st.text_input("Şarjör Adı", "A01")
        rounds = st.number_input("Fişek sayısı", min_value=1, max_value=100, value=30)
        submitted = st.form_submit_button("Şarjör Ekle")

        if submitted:
            ok, msg = add_magazine(nfc_id, name, int(rounds))
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    st.divider()

    mags = st.session_state.magazines
    if mags:
        selected = st.selectbox("Şarjör seç", list(mags.keys()))
        if st.button("Ateş Et"):
            ok, msg = fire_magazine(selected)
            if ok:
                st.success(msg)
            else:
                st.warning(msg)
        if st.button("Doldur"):
            ok, msg = reload_magazine(selected)
            if ok:
                st.success(msg)
            else:
                st.warning(msg)

stats = []
for nfc_id, mag in st.session_state.magazines.items():
    stats.append({
        "NFC ID": nfc_id,
        "Şarjör": mag["name"],
        "Kalan": mag["current"],
        "Toplam": mag["initial"],
        "Atılan": mag["fired"]
    })

if stats:
    st.subheader("📋 Şarjör listesi")
    st.dataframe(pd.DataFrame(stats), use_container_width=True)
else:
    st.info("Henüz şarjör eklenmedi. Sol taraftan ekleyin.")

st.subheader("📝 Olay geçmişi")
if st.session_state.events:
    for e in st.session_state.events[:20]:
        st.write(e)
else:
    st.write("Henüz olay yok.")
