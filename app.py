import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuración
st.set_page_config(page_title="Dashboard Gastos", layout="wide")
st.title("💰 Dashboard de Gastos Personales")

# Conectar con Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# Abre tu Sheet. Cambia el nombre si tu Sheet se llama distinto
SHEET_NAME = "DB_Gastos" 
sheet = client.open(SHEET_NAME).sheet1

# Función para cargar datos
@st.cache_data(ttl=60)
def cargar_datos():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df['Monto'] = pd.to_numeric(df['Monto'])
    return df

df = cargar_datos()

# FORMULARIO PARA AGREGAR GASTOS
st.subheader("Agregar nuevo gasto")
with st.form("nuevo_gasto"):
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha", datetime.now())
        categoria = st.selectbox("Categoria", ["Comida", "Transporte", "Supermercado", "Casa", "Ocio", "Salud", "Otros"])
    with col2:
        monto = st.number_input("Monto", min_value=0, step=1000)
        descripcion = st.text_input("Descripcion")
    
    submitted = st.form_submit_button("Guardar Gasto")
    if submitted:
        nueva_fila = [str(fecha), categoria, monto, descripcion]
        sheet.append_row(nueva_fila)
        st.success("Gasto guardado!")
        st.cache_data.clear() # Recarga los datos
        st.rerun()

# MOSTRAR DATOS Y GRAFICO
st.subheader("Tus Gastos")
if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    st.subheader("Gastos por Categoria")
    gastos_cat = df.groupby("Categoria")["Monto"].sum()
    st.bar_chart(gastos_cat)
    
    st.metric("Total Gastado", f"${df['Monto'].sum():,.0f}")
else:
    st.info("Aún no hay gastos. Agrega el primero arriba 👆")