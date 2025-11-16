import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path
import re

st.set_page_config(page_title="Análisis IMDB", layout="wide")

st.title("🎬 Dashboard de Películas IMDB")
st.markdown("Tendencias en películas desde el año 2000")

# Carga del archivo 
ruta_csv = Path(__file__).parent / "imdb_top_1000.csv"
df_original = pd.read_csv(ruta_csv, on_bad_lines="skip", encoding="utf-8", engine="python")
df = df_original.copy()

# Normalización
df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(r"[^a-z0-9]+", "_", regex=True)
)

df["year"] = df["released_year"].astype(str).str.extract(r"(\d{4})")[0].astype("Int64")
df["rating"] = pd.to_numeric(df["imdb_rating"], errors="coerce")
df["genre"] = df["genre"].astype(str).str.split(",").str[0].str.strip()
df["title"] = df["series_title"].astype(str).str.strip()

# Limpieza 
df = df.dropna(subset=["year", "rating", "genre", "title"])
df = df[df["year"] >= 2000]

# Filtrado
lista_generos = sorted(df["genre"].dropna().unique().tolist())
lista_generos = ["Todos"] + lista_generos
genero_elegido = st.sidebar.selectbox("Género", lista_generos, index=0)

year_min, year_max = int(df["year"].min()), int(df["year"].max())
year_desde, year_hasta = st.sidebar.slider(
    "Rango de años",
    min_value=year_min,
    max_value=year_max,
    value=(max(2000, year_min), year_max)
)

if genero_elegido == "Todos":
    df_filtrado = df[df["year"].between(year_desde, year_hasta)]
else:
    df_filtrado = df[
        df["year"].between(year_desde, year_hasta) &
        df["genre"].str.contains(re.escape(genero_elegido), case=False, na=False)
    ]

label_genero = "Todos los géneros" if genero_elegido == "Todos" else genero_elegido

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Películas filtradas", len(df_filtrado))
c2.metric("Rating promedio", f"{df_filtrado['rating'].mean():.2f}")
anio_mas_estrenos = int(df_filtrado["year"].value_counts().idxmax())
c3.metric("Año con más estrenos", anio_mas_estrenos)

# Exploración 
st.divider()
st.header("Exploración")

st.write("**Tamaño del dataset:**", df_filtrado.shape)
st.dataframe(df_filtrado[["title", "year", "genre", "rating"]].head(20), use_container_width=True)

st.write("**Estadísticas:**")
st.dataframe(df_filtrado.select_dtypes("number").describe().T, use_container_width=True)

# Visualización 
st.divider()
st.header("Visualización")

promedio_por_anio = (
    df_filtrado.groupby("year", as_index=False)["rating"]
    .mean()
    .rename(columns={"year": "Año", "rating": "Promedio Rating"})
)
fig1 = px.line(promedio_por_anio, x="Año", y="Promedio Rating", title=f"Promedio de rating por año ({label_genero})")
st.plotly_chart(fig1, use_container_width=True)

cantidad_por_anio = (
    df_filtrado["year"].value_counts()
    .rename_axis("Año")
    .reset_index(name="Cantidad")
    .sort_values("Año")
)
fig2 = px.bar(cantidad_por_anio, x="Año", y="Cantidad", title=f"Cantidad de estrenos por año ({label_genero})")
st.plotly_chart(fig2, use_container_width=True)

top10 = df_filtrado.sort_values(["rating", "title"], ascending=[False, True]).head(10)[["title", "rating"]]
fig3 = px.bar(top10, x="title", y="rating", title=f"Top 10 películas ({label_genero})")
fig3.update_layout(xaxis_title="Película", yaxis_title="Rating")
st.plotly_chart(fig3, use_container_width=True)

# Conclusiones 
puntaje_promedio = df_filtrado["rating"].mean()

prom_anual = df_filtrado.groupby("year")["rating"].mean()
mejor_year = int(prom_anual.idxmax())
puntaje_mejor_year = float(prom_anual.max())

idx_mejor = df_filtrado["rating"].idxmax()
mejor_peli = df_filtrado.at[idx_mejor, "title"]
year_mejor_peli = int(df_filtrado.at[idx_mejor, "year"])
rating_mejor_peli = float(df_filtrado.at[idx_mejor, "rating"])

idx_peor = df_filtrado["rating"].idxmin()
peor_peli = df_filtrado.at[idx_peor, "title"]
year_peor_peli = int(df_filtrado.at[idx_peor, "year"])
rating_peor_peli = float(df_filtrado.at[idx_peor, "rating"])

st.divider()
st.header("Conclusiones")

st.markdown(
    f"""
- **Producción:** el año con más estrenos dentro del filtro es **{anio_mas_estrenos}**.
- **Calidad promedio:** el rating promedio es **{puntaje_promedio:.2f}**.
- **Mejor año en promedio:** **{mejor_year}** con un rating medio de **{puntaje_mejor_year:.2f}**.
- **Película mejor valorada:** **{mejor_peli}** ({year_mejor_peli}) con **{rating_mejor_peli:.2f}**.
- **Película con menor rating:** **{peor_peli}** ({year_peor_peli}) con **{rating_peor_peli:.2f}**.
"""
)
