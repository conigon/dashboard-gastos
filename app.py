import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="Dashboard Gastos", layout="wide")
SHEET_NAME = "DB_Gastos"

@st.cache_resource
def conectar_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

sheet = conectar_sheets()

@st.cache_data
def cargar_datos():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df['Monto'] = pd.to_numeric(df['Monto'])
        df['ID'] = df.index + 2
    return df

def guardar_gasto(fecha, categoria, descripcion, monto):
    sheet.append_row([fecha.strftime("%Y-%m-%d"), categoria, descripcion, monto])

def actualizar_gasto(row_id, fecha, categoria, descripcion, monto):
    sheet.update(f'A{row_id}:D{row_id}', [[fecha.strftime("%Y-%m-%d"), categoria, descripcion, monto]])

def borrar_gasto(row_id):
    sheet.delete_rows(row_id)

st.title("💰 Dashboard de Gastos")
tab1, tab2 = st.tabs(["📊 Ver Gastos", "➕ Agregar Gasto"])
df = cargar_datos()

# Estado para saber qué fila estamos editando
if 'editando_id' not in st.session_state:
    st.session_state.editando_id = None

with tab2:
    st.subheader("Registrar nuevo gasto")
    with st.form("form_gasto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", datetime.now())
            categoria = st.selectbox("Categoría", ["Comida", "Transporte", "Casa", "Salud", "Ocio", "Otros"])
        with col2:
            monto = st.number_input("Monto", min_value=0.0, format="%.2f")
            descripcion = st.text_input("Descripción")

        if st.form_submit_button("Guardar Gasto"):
            if descripcion and monto > 0:
                guardar_gasto(fecha, categoria, descripcion, monto)
                st.success("Guardado!")
                st.cache_data.clear()
                st.rerun()

with tab1:
    st.subheader("Historial de Gastos")
    if df.empty:
        st.info("Aún no hay gastos")
    else:
        # FILTROS
        st.markdown("### Filtros")
        col1, col2, col3 = st.columns(3)
        with col1: filtro_cat = st.selectbox("Categoría", ["Todas"] + df['Categoria'].unique().tolist())
        with col2: fecha_inicio = st.date_input("Desde", df['Fecha'].min())
        with col3: fecha_fin = st.date_input("Hasta", df['Fecha'].max())
        buscador = st.text_input("🔍 Buscar en descripción")

        df_filtrado = df.copy()
        if filtro_cat!= "Todas": df_filtrado = df_filtrado[df_filtrado['Categoria'] == filtro_cat]
        df_filtrado = df_filtrado[(df_filtrado['Fecha'] >= pd.to_datetime(fecha_inicio)) & (df_filtrado['Fecha'] <= pd.to_datetime(fecha_fin))]
        if buscador: df_filtrado = df_filtrado[df_filtrado['Descripcion'].str.contains(buscador, case=False, na=False)]

        st.metric("Total Filtrado", f"${df_filtrado['Monto'].sum():,.2f}")

        # TABLA CON EDITAR Y BORRAR
        for i, row in df_filtrado.sort_values("Fecha", ascending=False).iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([2,2,3,2,1,1])
            col1.write(row['Fecha'].strftime("%Y-%m-%d"))
            col2.write(row['Categoria'])
            col3.write(row['Descripcion'])
            col4.write(f"${row['Monto']:,.2f}")

            if col5.button("✏️", key=f"edit_{row['ID']}"):
                st.session_state.editando_id = row['ID']
                st.rerun()

            if col6.button("🗑️", key=f"del_{row['ID']}"):
                borrar_gasto(int(row['ID']))
                st.cache_data.clear()
                st.rerun()

        # FORMULARIO DE EDICION
        if st.session_state.editando_id:
            st.markdown("---")
            st.subheader("Editando gasto")
            fila = df[df['ID'] == st.session_state.editando_id].iloc[0]

            with st.form("form_editar"):
                col1, col2 = st.columns(2)
                with col1:
                    new_fecha = st.date_input("Fecha", fila['Fecha'])
                    new_categoria = st.selectbox("Categoría", ["Comida", "Transporte", "Casa", "Salud", "Ocio", "Otros"], index=["Comida", "Transporte", "Casa", "Salud", "Ocio", "Otros"].index(fila['Categoria']))
                with col2:
                    new_monto = st.number_input("Monto", value=float(fila['Monto']), format="%.2f")
                    new_descripcion = st.text_input("Descripción", fila['Descripcion'])

                col1, col2 = st.columns(2)
                if col1.form_submit_button("Guardar Cambios"):
                    actualizar_gasto(int(st.session_state.editando_id), new_fecha, new_categoria, new_descripcion, new_monto)
                    st.session_state.editando_id = None
                    st.cache_data.clear()
                    st.success("Actualizado!")
                    st.rerun()
                if col2.form_submit_button("Cancelar"):
                    st.session_state.editando_id = None
                    st.rerun()