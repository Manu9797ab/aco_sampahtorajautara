
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from utils import load_graph_data, save_convergence_plot, estimate_fuel_cost
from aco_multi import AntColonyMulti
import matplotlib.pyplot as plt
from io import BytesIO
import time
import os

st.set_page_config(page_title="Optimasi Rute Sampah", layout="wide")
st.title("♻️ Sistem Optimasi Rute Pengangkutan Sampah")

csv_file = "data/titik_lokasi.csv"

# Sidebar – Input Parameter dan Penambahan Titik
with st.sidebar:
    st.header("🚛 Parameter ACO")
    n_ants = st.slider("Jumlah Semut", 5, 100, 20)
    n_iter = st.slider("Jumlah Iterasi", 10, 300, 100)
    alpha = st.slider("Alpha (pheromone)", 0.1, 3.0, 1.0)
    beta = st.slider("Beta (heuristik)", 0.1, 5.0, 2.0)
    decay = st.slider("Tingkat Evaporasi", 0.1, 1.0, 0.5)
    n_vehicles = st.slider("Jumlah Truk", 1, 20, 6)

    st.header("⛽ Biaya")
    fuel_price = st.number_input("Harga Bensin (per liter)", min_value=0.0, value=10000.0, step=100.0)
    cost_other = st.number_input("Biaya Lain (Rp)", min_value=0.0, value=50000.0, step=1000.0)

    st.header("➕ Tambah Titik Manual")
    nama_baru = st.text_input("Nama Titik")
    lat_baru = st.number_input("Latitude", format="%.6f")
    lon_baru = st.number_input("Longitude", format="%.6f")
    if st.button("Tambah Titik"):
        new_row = pd.DataFrame({'name': [nama_baru], 'lat': [lat_baru], 'lon': [lon_baru]})
        df_existing = pd.read_csv(csv_file)
        df_combined = pd.concat([df_existing, new_row], ignore_index=True)
        df_combined.to_csv(csv_file, index=False)
        st.success(f"Titik '{nama_baru}' berhasil ditambahkan! Silakan jalankan ulang ACO.")

df, distance_matrix, names = load_graph_data(csv_file)
center = df[['lat', 'lon']].mean().values

# Peta
map_base = folium.Map(location=center, zoom_start=13)
for _, row in df.iterrows():
    folium.Marker([row['lat'], row['lon']], tooltip=row['name']).add_to(map_base)
st.subheader("📍 Peta Lokasi Titik Pengangkutan")
st_folium(map_base, height=400)

# ACO Proses
st.info("🔁 Optimasi sedang diproses...")
progress = st.progress(0)

@st.cache_data
def run_aco(distance_matrix, n_ants, n_iter, alpha, beta, decay, n_vehicles):
    aco = AntColonyMulti(distance_matrix, n_ants, n_iter, alpha, beta, decay, n_vehicles)
    return aco.run()

best_routes, best_distance, history = run_aco(distance_matrix, n_ants, n_iter, alpha, beta, decay, n_vehicles)
for i in range(100):
    progress.progress(i + 1)
    time.sleep(0.002)
progress.empty()

# Hasil ACO
save_convergence_plot(history)
fuel_used, total_cost = estimate_fuel_cost(best_distance, fuel_price, cost_other)

st.subheader("📊 Hasil Optimasi")
col1, col2, col3 = st.columns(3)
col1.metric("Total Jarak", f"{int(best_distance)} meter")
col2.metric("Estimasi BBM", f"{fuel_used} liter")
col3.metric("Total Biaya", f"Rp{int(total_cost):,}")

st.subheader("📈 Grafik Konvergensi ACO")
fig, ax = plt.subplots()
ax.plot(history, marker='o')
ax.set_title("Perkembangan Nilai Jarak Terbaik")
ax.set_xlabel("Iterasi")
ax.set_ylabel("Jarak Terbaik")
ax.grid(True)
st.pyplot(fig)

st.subheader("📋 Tabel Rute Semua Truk")
data_rute = []
for i, route in enumerate(best_routes):
    rute_nama = " → ".join([names[idx] for idx in route])
    jarak = sum(distance_matrix[route[j]][route[j + 1]] for j in range(len(route) - 1))
    data_rute.append({
        "Truk": f"Truk #{i+1}",
        "Jumlah Titik": len(route)-2,
        "Jarak Total (m)": int(jarak),
        "Rute": rute_nama
    })
df_rute = pd.DataFrame(data_rute)
st.dataframe(df_rute, use_container_width=True)

buffer = BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    df_rute.to_excel(writer, sheet_name='Rute', index=False)
st.download_button(
    label="💾 Unduh Tabel Rute ke Excel",
    data=buffer.getvalue(),
    file_name="rute_truk.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# 📍 Pilih Truk → tampilkan rute detail dan peta
st.subheader("🧭 Pilih Truk untuk Lihat Detail Rute")
selected_truck = st.selectbox("Pilih Truk", df_rute["Truk"].tolist())
truck_index = int(selected_truck.split("#")[1]) - 1
route = best_routes[truck_index]

st.markdown(f"### 🚛 {selected_truck}")
st.write("**Rute:**", " → ".join([names[idx] for idx in route]))
jarak = sum(distance_matrix[route[j]][route[j + 1]] for j in range(len(route) - 1))
st.write("**Jarak Total:**", f"{int(jarak)} meter")

# Peta per truk
r_map = folium.Map(location=center, zoom_start=13)
for idx in route:
    folium.Marker([df.iloc[idx]['lat'], df.iloc[idx]['lon']], tooltip=names[idx]).add_to(r_map)
for j in range(len(route) - 1):
    folium.PolyLine([(df.iloc[route[j]]['lat'], df.iloc[route[j]]['lon']),
                     (df.iloc[route[j+1]]['lat'], df.iloc[route[j+1]]['lon'])],
                    color="blue", weight=4).add_to(r_map)
st_folium(r_map, height=400)
