import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from magazine_manager import MagazineManager

st.set_page_config(
    page_title="📦 Mühimmat Takip Sistemi",
    page_icon="🔫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Tema
st.markdown(
    """
    <style>
    .main { padding: 0.5rem 1rem; }
    .stMetric { background: #f3f4f6; border-radius: 12px; padding: 12px; }
    [data-testid="stSidebar"] { background-color: #0f172a; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state
if "magazine_manager" not in st.session_state:
    st.session_state.magazine_manager = MagazineManager()

mm = st.session_state.magazine_manager

st.title("📦 Elektronik Mühimmat Takip Sistemi")
st.caption("Sandbox simülasyonu — şarjör kimliği, fişek takibi ve olay kaydı")
st.divider()

with st.sidebar:
    st.markdown("## ⚙️ Kontrol Paneli")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["➕ Şarjör Ekle", "🗑️ Yönet", "📊 İstatistik"])

    with tab1:
        st.subheader("Yeni Şarjör Ekle")
        with st.form("add_magazine_form"):
            nfc_id = st.text_input("NFC ID", placeholder="NFC_001")
            mag_name = st.text_input("Şarjör Adı", placeholder="A01")
            initial_rounds = st.number_input("İlk Fişek Sayısı", min_value=1, max_value=1000, value=30)
            submitted = st.form_submit_button("✅ Şarjörü Ekle", use_container_width=True)

            if submitted:
                if not nfc_id or not mag_name:
                    st.error("NFC ID ve şarjör adı gereklidir.")
                else:
                    result = mm.add_magazine(nfc_id, mag_name, initial_rounds)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])

    with tab2:
        st.subheader("Şarjör Yönetimi")
        all_mags = mm.get_all_magazines()

        if all_mags:
            selected_mag = st.selectbox(
                "Şarjör Seç",
                options=list(all_mags.keys()),
                format_func=lambda x: f"{all_mags[x]['name']} ({x})",
            )

            mag = all_mags[selected_mag]
            st.metric("Mevcut Fişek", mag["current_rounds"], f"/ {mag['initial_rounds']}")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔄 Doldur", use_container_width=True):
                    result = mm.reload_magazine(selected_mag)
                    st.success(result["message"])
                    st.rerun()
            with col_b:
                if st.button("🗑️ Kaldır", use_container_width=True):
                    result = mm.remove_magazine(selected_mag)
                    st.warning(result["message"])
                    st.rerun()
        else:
            st.info("Henüz şarjör eklenmedi.")

    with tab3:
        stats = mm.get_statistics()
        st.metric("Toplam Şarjör", stats["total_magazines"])
        st.metric("Toplam Fişek", stats["total_rounds_initial"])
        st.metric("Atılan Fişek", stats["total_rounds_fired"])
        st.metric("Kalan Fişek", stats["total_rounds_remaining"])

        if st.button("🧹 Tüm Verileri Sil", use_container_width=True):
            mm.clear_all_data()
            st.warning("Tüm veriler silindi.")
            st.rerun()

# Ana panel
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Şarjör Tablosu")
    all_mags = mm.get_all_magazines()
    if all_mags:
        rows = []
        for nfc_id, mag in all_mags.items():
            rows.append(
                {
                    "NFC ID": nfc_id,
                    "Şarjör Adı": mag["name"],
                    "Fişek": f"{mag['current_rounds']}/{mag['initial_rounds']}",
                    "Atılan": mag["fired_rounds"],
                    "Eklenme": mag["created_at"][:10],
                    "Son Kullanım": mag["last_used"][:10] if mag["last_used"] else "-",
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Henüz şarjör eklenmedi. Sol taraftan yeni şarjör ekleyin.")

with col2:
    st.subheader("📊 Hızlı İstatistik")
    stats = mm.get_statistics()
    st.metric("Toplam Şarjör", stats["total_magazines"])
    st.metric("Toplam Fişek", stats["total_rounds_initial"])
    st.metric("Atılan Fişek", stats["total_rounds_fired"])
    st.metric("Kalan Fişek", stats["total_rounds_remaining"])
    if stats["uncertain_events"] > 0:
        st.metric("⚠️ Belirsiz Olay", stats["uncertain_events"])

st.divider()

st.subheader("🎯 Ateş Simülasyonu")
all_mags = mm.get_all_magazines()
if all_mags:
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        selected_mag_for_fire = st.selectbox(
            "Şarjör Seç",
            options=list(all_mags.keys()),
            format_func=lambda x: f"{all_mags[x]['name']} ({all_mags[x]['current_rounds']}/{all_mags[x]['initial_rounds']})",
        )
    with col_b:
        num_rounds = st.number_input("Atış Adedi", min_value=1, max_value=10, value=1)
    with col_c:
        if st.button("💥 Ateş Et", use_container_width=True, type="primary"):
            for _ in range(num_rounds):
                result = mm.fire_round(selected_mag_for_fire)
                if result["success"]:
                    st.success(result["message"])
                else:
                    if result.get("is_uncertain"):
                        st.warning(result["message"])
                    else:
                        st.error(result["message"])
            st.rerun()
else:
    st.info("Ateş etmek için önce bir şarjör ekleyin.")

st.divider()

st.subheader("📈 Grafikler")
if all_mags:
    labels = [m["name"] for m in all_mags.values()]
    values = [m["current_rounds"] for m in all_mags.values()]

    pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.45)])
    pie.update_layout(title="Şarjör Kalan Fişek Dağılımı", height=400)
    st.plotly_chart(pie, use_container_width=True)

    bar_data = [{"Şarjör": m["name"], "Atılan": m["fired_rounds"], "Kalan": m["current_rounds"]} for m in all_mags.values()]
    df_bar = pd.DataFrame(bar_data)
    bar = go.Figure(data=[
        go.Bar(name="Atılan", x=df_bar["Şarjör"], y=df_bar["Atılan"], marker_color="#ef4444"),
        go.Bar(name="Kalan", x=df_bar["Şarjör"], y=df_bar["Kalan"], marker_color="#22c55e"),
    ])
    bar.update_layout(barmode="stack", title="Şarjör Durumu", height=400)
    st.plotly_chart(bar, use_container_width=True)

st.divider()

st.subheader("📝 Olay Geçmişi")
filter_type = st.selectbox(
    "Filtre",
    ["Tümü", "Başarılı Atışlar", "Boş Şarjör", "Belirsiz Olaylar", "Şarjör İşlemleri"],
)
event_limit = st.number_input("Gösterilecek Olay Sayısı", min_value=10, max_value=500, value=50)

events = mm.get_events(limit=event_limit)
if events:
    filtered = events
    if filter_type == "Başarılı Atışlar":
        filtered = [e for e in events if e["type"] == "FIRE_SUCCESS"]
    elif filter_type == "Boş Şarjör":
        filtered = [e for e in events if e["type"] == "FIRE_FAILED_EMPTY"]
    elif filter_type == "Belirsiz Olaylar":
        filtered = [e for e in events if e.get("is_uncertain")]
    elif filter_type == "Şarjör İşlemleri":
        filtered = [e for e in events if "MAGAZINE" in e["type"]]

    table_rows = []
    for e in filtered:
        table_rows.append(
            {
                "Zaman": e["timestamp"][5:16],
                "NFC ID": e["nfc_id"],
                "Olay": e["type"],
                "Açıklama": e["description"],
                "Belirsiz": "Evet" if e.get("is_uncertain") else "Hayır",
            }
        )
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
else:
    st.info("Henüz olay kaydı yok.")

st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 12px; margin-top: 30px;'>
        TÜBİTAK 2209-A/B | Elektronik Mühimmat Takip ve Gösterge Sistemi<br>
        Sandbox Simülasyon Prototipi v1.0
    </div>
    """,
    unsafe_allow_html=True,
)
