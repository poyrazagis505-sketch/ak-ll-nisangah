"""Şarjör Kimlik & Sayaç Takip Simülasyonu (laboratuvar test paneli)
Tamamen yazılım simülasyonu: temsili şarjör kimlikleri + sanal olaylar.
Veri: yerel SQLite (sarjor.db) -> program kapanıp açılınca korunur.
"""
import re
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

DB = "sarjor.db"
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,16}$")


# ---------- Veri katmanı ----------
def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS magazines(
                id TEXT PRIMARY KEY,
                capacity INTEGER NOT NULL,
                count INTEGER NOT NULL,
                uncertain INTEGER NOT NULL DEFAULT 0,
                created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                mag_id TEXT,
                type TEXT NOT NULL,
                delta INTEGER NOT NULL DEFAULT 0,
                note TEXT);
            CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, value TEXT);
            """
        )


def now():
    return datetime.now().isoformat(timespec="seconds")


def log(c, mag_id, typ, delta=0, note=""):
    c.execute(
        "INSERT INTO events(ts,mag_id,type,delta,note) VALUES(?,?,?,?,?)",
        (now(), mag_id, typ, delta, note),
    )


def get_active(c):
    r = c.execute("SELECT value FROM state WHERE key='active'").fetchone()
    return r["value"] if r and r["value"] else None


def set_active(c, mag_id):
    c.execute("INSERT OR REPLACE INTO state(key,value) VALUES('active',?)", (mag_id or "",))


def get_mag(c, mag_id):
    return c.execute("SELECT * FROM magazines WHERE id=?", (mag_id,)).fetchone()


# ---------- İşlemler (callback) ----------
def msg(kind, text):
    st.session_state["msg"] = (kind, text)


def do_register():
    mid = st.session_state.get("f_id", "").strip()
    cap = int(st.session_state.get("f_cap", 15))
    cnt = int(st.session_state.get("f_cnt", 15))
    if not ID_RE.match(mid):
        return msg("error", "Kimlik 1-16 karakter olmalı (harf, rakam, - veya _).")
    if not (1 <= cap <= 100):
        return msg("error", "Kapasite 1-100 arasında olmalı.")
    if not (0 <= cnt <= cap):
        return msg("error", "Başlangıç değeri 0 ile kapasite arasında olmalı.")
    with conn() as c:
        if get_mag(c, mid):
            return msg("error", f"{mid} zaten kayıtlı.")
        c.execute(
            "INSERT INTO magazines(id,capacity,count,uncertain,created) VALUES(?,?,?,0,?)",
            (mid, cap, cnt, now()),
        )
        log(c, mid, "KAYIT", 0, f"kapasite={cap}, başlangıç={cnt}")
    msg("success", f"{mid} kaydedildi.")


def do_insert(mid):
    mid = mid.strip()
    with conn() as c:
        if not get_mag(c, mid):
            log(c, mid, "BİLİNMEYEN_KİMLİK", 0, "kayıtsız kimlik okundu, reddedildi")
            return msg("error", f"Bilinmeyen kimlik: {mid} (kayıt değişmedi).")
        prev = get_active(c)
        if prev and prev != mid:
            log(c, prev, "ÇIKARMA", 0, "yeni şarjör takıldığı için")
        set_active(c, mid)
        log(c, mid, "TAKMA", 0, "")
    msg("success", f"{mid} takıldı.")


def do_remove():
    with conn() as c:
        act = get_active(c)
        if not act:
            return msg("warning", "Takılı şarjör yok.")
        set_active(c, None)
        log(c, act, "ÇIKARMA", 0, "")
    msg("info", f"{act} çıkarıldı.")


def do_motion(kind):
    with conn() as c:
        act = get_active(c)
        if not act:
            log(c, None, "OLAY_ŞARJÖRSÜZ", 0, f"{kind} olay, takılı şarjör yok")
            return msg("warning", "Takılı şarjör yok; olay kayda alındı ama sayı değişmedi.")
        m = get_mag(c, act)
        if kind == "doğrulanmış":
            if m["count"] <= 0:
                log(c, act, "ANOMALİ", 0, "sayı 0 iken doğrulanmış olay geldi")
                return msg("warning", "Anomali: sayı zaten 0. Değişiklik yapılmadı.")
            c.execute("UPDATE magazines SET count=count-1 WHERE id=?", (act,))
            log(c, act, "OLAY_DOĞRULANMIŞ", -1, "")
            msg("success", f"{act}: sayı {m['count'] - 1}")
        else:
            c.execute("UPDATE magazines SET uncertain=uncertain+1 WHERE id=?", (act,))
            log(c, act, "OLAY_BELİRSİZ", 0, "sayı otomatik değiştirilmedi")
            msg("warning", f"{act}: belirsiz olay kaydedildi, sayı DEĞİŞMEDİ.")


def do_manual_set(mid):
    val = int(st.session_state.get("f_set", 0))
    with conn() as c:
        m = get_mag(c, mid)
        if not m:
            return msg("error", "Şarjör bulunamadı.")
        if not (0 <= val <= m["capacity"]):
            return msg("error", "Değer 0 ile kapasite arasında olmalı.")
        c.execute("UPDATE magazines SET count=?, uncertain=0 WHERE id=?", (val, mid))
        log(c, mid, "MANUEL_DÜZELTME", val - m["count"], f"{m['count']} -> {val}")
    msg("success", "Sayı düzeltildi, belirsiz sayacı sıfırlandı.")


def do_reset():
    with conn() as c:
        c.executescript("DELETE FROM magazines; DELETE FROM events; DELETE FROM state;")
    msg("info", "Tüm test verisi silindi.")


# ---------- Arayüz ----------
st.set_page_config(page_title="Şarjör Takip Simülasyonu", layout="wide")
init()
st.title("🧪 Şarjör Kimlik & Sayaç Simülasyonu")
st.caption("Laboratuvar test paneli — temsili kimlikler ve sanal olaylar")

if "msg" in st.session_state:
    kind, text = st.session_state.pop("msg")
    getattr(st, kind)(text)

with st.sidebar:
    st.header("Yeni şarjör kaydı")
    st.text_input("Kimlik (örn. A01)", key="f_id")
    st.number_input("Kapasite", 1, 100, 15, key="f_cap")
    st.number_input("Başlangıç değeri", 0, 100, 15, key="f_cnt")
    st.button("Kaydet", on_click=do_register, use_container_width=True)
    st.divider()
    st.button("⚠️ Tüm veriyi sil", on_click=do_reset, use_container_width=True)

with conn() as c:
    mags = pd.read_sql_query("SELECT * FROM magazines ORDER BY id", c)
    active = get_active(c)
    events = pd.read_sql_query("SELECT * FROM events ORDER BY id DESC", c)

# Gösterge (küçük ekran simülasyonu)
st.subheader("Gösterge")
if active:
    m = mags[mags["id"] == active].iloc[0]
    unc = int(m["uncertain"])
    cols = st.columns(3)
    cols[0].metric("Takılı şarjör", active)
    cols[1].metric("Kayıtlı sayı", f"{m['count']} / {m['capacity']}")
    cols[2].metric("Belirsiz olay", unc)
    if unc:
        st.warning(f"Sayı doğrulanmamış olabilir ({unc} belirsiz olay). Manuel kontrol önerilir.")
else:
    st.info("Şarjör takılı değil.")

# Simülasyon kontrolleri
st.subheader("Simülasyon kontrolleri")
c1, c2 = st.columns(2)
with c1:
    ids = list(mags["id"]) if not mags.empty else []
    sel = st.selectbox("Şarjör seç", ids + ["(kayıtsız test: X99)"])
    b1, b2 = st.columns(2)
    b1.button("Tak", on_click=do_insert, args=("X99" if sel.startswith("(") else sel,),
              use_container_width=True)
    b2.button("Çıkar", on_click=do_remove, use_container_width=True)
with c2:
    b3, b4 = st.columns(2)
    b3.button("Doğrulanmış olay (-1)", on_click=do_motion, args=("doğrulanmış",),
              use_container_width=True)
    b4.button("Belirsiz olay (sayı değişmez)", on_click=do_motion, args=("belirsiz",),
              use_container_width=True)
    if active:
        st.number_input("Manuel düzeltme değeri", 0, 100, 0, key="f_set")
        st.button("Sayıyı düzelt", on_click=do_manual_set, args=(active,))

st.subheader("Şarjör tablosu")
st.dataframe(mags, use_container_width=True, hide_index=True)

st.subheader("Olay geçmişi")
if not events.empty:
    types = st.multiselect("Filtre", sorted(events["type"].unique()))
    view = events[events["type"].isin(types)] if types else events
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.download_button("CSV indir", events.to_csv(index=False).encode("utf-8-sig"),
                       "olay_gecmisi.csv", "text/csv")
else:
    st.caption("Henüz olay yok.")
