import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análisis de Gastos", layout="wide")
st.title("💰 Análisis de Gastos")

df = pd.read_csv("gastos.csv")
df['Fecha'] = pd.to_datetime(df['Fecha'])

st.header("➕ Agregar Nuevo Gasto")

with st.form("form_gasto"):
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha")
        categoria = st.selectbox("Categoria", df['Categoria'].unique())
    with col2:
        monto = st.number_input("Monto", min_value=0)
        descripcion = st.text_input("Descripción")
    
    submitted = st.form_submit_button("Guardar Gasto")
    if submitted:
        nuevo_gasto = pd.DataFrame([[fecha, categoria, monto, descripcion]], columns=df.columns)
        df = pd.concat([df, nuevo_gasto], ignore_index=True)
        df.to_csv("gastos.csv", index=False)
        st.success("Gasto agregado!")
        st.rerun()

st.divider()

# FILTROS
st.sidebar.header("Filtros")

# NUEVO: Toggle para elegir Mes vs Todos los meses
modo = st.sidebar.radio("Ver:", ["Mes Específico", "Todos los Meses Acumulado"])

categorias = st.sidebar.multiselect(
    "Selecciona Categoría",
    options=df["Categoria"].unique(),
    default=df["Categoria"].unique()
)

# LÓGICA DE FILTRO
if modo == "Mes Específico":
    meses = st.sidebar.selectbox(
        "Selecciona Mes", 
        options=df["Fecha"].dt.strftime('%Y-%m').unique()
    )
    df_filtrado = df[
        (df["Fecha"].dt.strftime('%Y-%m') == meses) & 
        (df["Categoria"].isin(categorias))
    ]
    titulo_kpi = f"Gasto Total {meses}"
else:
    df_filtrado = df[df["Categoria"].isin(categorias)]
    titulo_kpi = "Gasto Total Acumulado"

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric(titulo_kpi, f"${df_filtrado['Monto'].sum():,.0f}")
col2.metric("Promedio por Gasto", f"${df_filtrado['Monto'].mean():,.0f}")
col3.metric("Nº de Gastos", len(df_filtrado))

# Gráficos
col1, col2 = st.columns(2)
with col1:
    st.subheader("Gasto por Categoría")
    fig1 = px.bar(df_filtrado.groupby('Categoria')['Monto'].sum().reset_index(), 
                  x='Categoria', y='Monto')
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Distribución %")
    fig2 = px.pie(df_filtrado, values='Monto', names='Categoria')
    st.plotly_chart(fig2, use_container_width=True)

# NUEVO: Gráfico de tendencia siempre visible
st.subheader("Tendencia Mensual")
tendencia = df[df["Categoria"].isin(categorias)].groupby('Fecha')['Monto'].sum().reset_index()
fig3 = px.line(tendencia, x='Fecha', y='Monto', markers=True)
st.plotly_chart(fig3, use_container_width=True)

st.dataframe(df_filtrado)