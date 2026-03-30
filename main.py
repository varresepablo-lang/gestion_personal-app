import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import calendar
import os

st.set_page_config(page_title="Gestión Varrese - Rotaciones 4x2", layout="wide")

def calcular_rotacion_4x2(fecha_inicio_ciclo, fecha_objetivo):
    """Calcula matemáticamente el ciclo 4x2 (4 trabajo, 2 franco)"""
    diferencia_dias = (fecha_objetivo - fecha_inicio_ciclo).days
    posicion_en_ciclo = diferencia_dias % 6
    return "A" if posicion_en_ciclo < 4 else "Z"

def main():
    st.title("🖥️ Sistema de Gestión de Capacitación")
    st.markdown(f"**Instructor Responsable:** Pablo Daniel Varrese")
    st.divider()

    # 1. DETECCIÓN DE ARCHIVOS
    archivos = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    base_file = next((f for f in archivos if "MIBASE" in f.upper()), None)
    curso_file = next((f for f in archivos if "FECHASCURSO" in f.upper()), None)

    if not base_file:
        st.error("No se detecta MIBASE.xlsx en la carpeta.")
        return

    # 2. PANEL LATERAL (TODOS LOS FILTROS)
    with st.sidebar:
        st.header("⚙️ Filtros de Control")
        
        # Filtros de Tiempo
        anio_sel = st.selectbox("Año:", [2026, 2027, 2028])
        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_sel_nombre = st.selectbox("Mes:", meses_nombres, index=date.today().month - 1)
        mes_sel_num = meses_nombres.index(mes_sel_nombre) + 1
        
        st.divider()

        # NUEVO FILTRO DE DÍAS (1 al 15)
        # Permite elegir un día específico o "Todos" (del 1 al 15)
        opciones_dias = ["Todos (1-15)"] + [str(i) for i in range(1, 16)]
        dia_seleccionado = st.selectbox("Seleccionar Día:", opciones_dias)

        st.divider()
        
        # Filtros Operativos
        compania_sel = st.multiselect("Compañía:", ["ARSA", "BOA", "GOL"], default=["ARSA", "BOA", "GOL"])
        turno_sel = st.multiselect("Turno:", ["Mañana", "Tarde", "Noche"], default=["Mañana", "Tarde", "Noche"])
        
        st.divider()
        solo_francos = st.checkbox("Ver solo personal con Franco (Z)")

    # 3. PROCESAMIENTO DE DATOS
    try:
        xls = pd.ExcelFile(base_file)
        df_lista = []
        for sheet in xls.sheet_names:
            temp_df = pd.read_excel(base_file, sheet_name=sheet, skiprows=2)
            cols = list(temp_df.columns)
            if len(cols) > 1: cols[1] = "Legajos"
            if len(cols) > 2: cols[2] = "Personal"
            if len(cols) > 3: cols[3] = "Turno"
            temp_df.columns = cols
            df_lista.append(temp_df)
        
        df_master = pd.concat(df_lista, ignore_index=True)
        df_master["Legajos"] = pd.to_numeric(df_master["Legajos"], errors='coerce').fillna(0).astype(int)
        df_master = df_master[df_master["Legajos"] > 0].drop_duplicates(subset=["Legajos"])

        # 4. LÓGICA DE ROTACIÓN 4x2
        fecha_base = datetime(2026, 1, 1) 
        
        # Determinar qué columnas de días generar
        if dia_seleccionado == "Todos (1-15)":
            dias_a_generar = [str(i) for i in range(1, 16)]
        else:
            dias_a_generar = [dia_seleccionado]
        
        for d_str in dias_a_generar:
            fecha_obj = datetime(anio_sel, mes_sel_num, int(d_str))
            df_master[d_str] = df_master.apply(lambda row: calcular_rotacion_4x2(fecha_base, fecha_obj), axis=1)

        # 5. BOTONES Y VISUALIZACIÓN
        st.subheader(f"📋 Proyección 4x2: {mes_sel_nombre} {anio_sel}")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Generar Grilla de Cursos"):
                if curso_file:
                    df_cursos = pd.read_excel(curso_file, skiprows=1)
                    df_cursos.columns = [str(c).strip() for c in df_cursos.columns]
                    df_cursos['LEGAJO'] = pd.to_numeric(df_cursos['LEGAJO'], errors='coerce').fillna(0).astype(int)
                    df_master = pd.merge(df_master, df_cursos[['LEGAJO', 'CURSO 2025/2026']], left_on="Legajos", right_on='LEGAJO', how='left')
                    st.success("Historial vinculado.")
        
        with c2:
            st.download_button("📥 Exportar Lista", df_master.to_csv(index=False).encode('utf-8'), f"Rotacion_{mes_sel_nombre}.csv", "text/csv")

        # Filtro de Francos
        if solo_francos:
            df_master = df_master[df_master[dias_a_generar].isin(['Z']).any(axis=1)]

        # Mostrar tabla
        cols_finales = ["Legajos", "Personal", "Turno"]
        if 'CURSO 2025/2026' in df_master.columns:
            cols_finales.append('CURSO 2025/2026')
        cols_finales += dias_a_generar

        st.dataframe(df_master[cols_finales], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error: {e}")

if __name__ == "__main__":
    main()