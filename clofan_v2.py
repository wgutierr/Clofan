#!/usr/bin/env python
# coding: utf-8

# In[344]:


import pandas as pd
import numpy as np

import streamlit as st
from datetime import datetime, time, date 


# ## 1. Cargar Data

# # Definir ruta del Archivo
# ruta_archivo = r'dataset\VISOR_AYUDAS_DX_V4-CONDICIONES.xlsm'

# In[359]:


# Cargar tanto CITAS como DISP_EQUIPO
def cargar_datos(ruta, nombre_hoja, columnas):
    df = pd.read_excel(ruta, 
            sheet_name= nombre_hoja, 
            usecols= columnas)
    return df


# df = cargar_datos(ruta_archivo, 
#                     nombre_hoja='CITAS', 
#                         columnas='A:H')
# 
# df_original_equipos = cargar_datos(ruta_archivo, 
#                                     nombre_hoja='DISP_EQUIPO', 
#                                     columnas='A:F')

# ## 2. Pre-procesamiento de datos

# ### 2.1 Pre-procesamiento de datos de citas

# In[161]:


def preprocesamiento_datos_citas(df_original_citas):
    # Generar copia de trabajo
    df = df_original_citas.copy()

    # Cambiar formato de columna 'FECHA' a datetime format
    df['FECHA'] = pd.to_datetime(df['FECHA'])

    # Combinar 'FECHA' y 'HORA' para crear 'Start' - Hora de inicio
    df['Start'] = pd.to_datetime(df['FECHA'].dt.strftime('%d-%m-%y') + ' ' + df['HORA'], format='%d-%m-%y %H:%M')

    # Crea una nueva columna 'Finish' sumando DURACION con Start
    df['DURACION'] = pd.to_timedelta(df['DURACION'] + ':00')
    df['Finish'] = df['Start'] + df['DURACION']

    # Extraer tipo de dia de la semana y mes desde el indice
    df['DIA_SEM'] = df['FECHA'].dt.weekday
    df['MES_AÑO'] = df['FECHA'].dt.strftime('%m-%Y')

    # Crear y rellenar una nueva columna 'DOC_DISPONIBLE' con el texto: 'CITA AGENDADA'
    df['DOC_DISPONIBLE'] = 'CITA AGENDADA'

    # Mostrar Fecha Maxima y Minima
    st.write("Fecha minima:", df['Start'].min())
    st.write("Fecha Maxima:", df['Start'].max())

    return df




# In[348]:


#df = preprocesamiento_datos_citas(df_original_citas)


# ### 2.2. Pre-procesamiento de datos de disponibilidad

# In[163]:


def preprocesamiento_datos_disponibilidad(df_original_equipos):
    
    # Generar copia de trabajo
    df_equipos = df_original_equipos.copy()
    
    # Cambiar Numero de dia a formato Python: 0: Lunes, 1: Martes, 2: Miercoles, 3: Jueves, 4: Viernes, 5: Sabado, 5: Domingo
    mapa_dia = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
    df_equipos['DIA'] = df_equipos['DIA'].map(mapa_dia)

    # Asignar texto 'Sin Doctor Asignado' cuando haya disponibilidad del equipo pero sin doctor asignado
    df_equipos['DOC_DISPONIBLE'] = df_equipos['DOC_DISPONIBLE'].fillna('Sin Doctor Asignado')
    
    # Convertir formato hora a str para posterior manipulacion
    df_equipos['HORA INICIO'] = df_equipos['HORA INICIO'].astype(str)
    df_equipos['HORA FIN'] = df_equipos['HORA FIN'].astype(str)
    
    # Combinar 'DIA' y 'HORA INICIO'/'HORA FIN' para crear info completa de fecha con el tipo de dia
    df_equipos['Start'] = pd.to_datetime(df_equipos['DIA'].astype(str) + ' ' + df_equipos['HORA INICIO'], format='%w %H:%M:%S')
    df_equipos['Finish'] = pd.to_datetime(df_equipos['DIA'].astype(str) + ' ' + df_equipos['HORA FIN'], format='%w %H:%M:%S')

    return df_equipos


# In[349]:


#df_equipos = preprocesamiento_datos_disponibilidad(df_original_equipos)


# ### 2.3. Completar df_equipos con programacion semanal

# In[211]:


#fecha_especifica = pd.to_datetime('2024-08-09')#.date()


# In[213]:


def construir_programacion_completa(fecha_especifica, df, df_equipos):
    # Filtrar por mes-año a revisar
    df_prueba = df[df['FECHA'] == fecha_especifica]

    # Extraer Fechas unicas en el mes seleccionado
    unique_dates = df_prueba['FECHA'].unique()
    new_rows = []

    # Iterar por cada fecha única
    for date in unique_dates:
        for idx, row in df_equipos.iterrows():
            start_time = datetime.strptime(row['HORA INICIO'], '%H:%M:%S').time()
            end_time = datetime.strptime(row['HORA FIN'], '%H:%M:%S').time()
            
            start_datetime = pd.Timestamp(date) + pd.Timedelta(hours=start_time.hour, minutes=start_time.minute)
            end_datetime = pd.Timestamp(date) + pd.Timedelta(hours=end_time.hour, minutes=end_time.minute)
            
            # Chequear si el dia coincide
            if row['DIA'] == start_datetime.dayofweek:
                # Crear nueva fila con hora de inicio y fin
                new_row = {
                    'EQUIPO': row['EQUIPO'],
                    'DIA': row['DIA'],
                    'HORA INICIO': row['HORA INICIO'],
                    'HORA FIN': row['HORA FIN'],
                    'DOC_DISPONIBLE': row['DOC_DISPONIBLE'],
                    'TIPO PACIENTE': row['TIPO PACIENTE'],
                    'Start': start_datetime,
                    'Finish': end_datetime
                }
                new_rows.append(new_row)
    
    # Crear Data Frame con nuevas filas
    new_df_equipos = pd.DataFrame(new_rows)
        
    # Concatenar las nuevas filas con el df original de equipos
    df_equipos = pd.concat([df_equipos, new_df_equipos], ignore_index=True)
    
    # Eliminar fechas creadas con año 1900
    df_equipos = df_equipos[df_equipos['Start'].dt.year != 1900]
    
    # Mostrar df_equipos actualizado
    df_equipos = df_equipos.dropna(subset=['Start'])
    
    # Renombrar columnas para estandarizar con df citas
    df_equipos = df_equipos.rename(columns={'EQUIPO': 'RECURSO', 'DIA': 'DIA_SEM'})
    
    return df_equipos, df_prueba


# In[214]:


#df_equipos, df_prueba = construir_programacion_completa(fecha_especifica, df, df_equipos)


# ### 2.4 Pre-procesamiento de datos final

# In[216]:


def preprocesamiento_datos_final(df_equipos, df_prueba):

    # Eliminar columnas redundantes
    df_equipos_concatenar = df_equipos.drop(columns = {'HORA INICIO','HORA FIN','TIPO PACIENTE'}).copy()

    # Rellenar Cita con texto 'DISP_EQUIPO'
    df_equipos_concatenar['CITA'] = 'DISP_EQUIPO'

    # Extraer solo Fecha de 'Start'
    df_equipos_concatenar['FECHA'] = df_equipos_concatenar['Start'].dt.date

    # Extraer solo mes-año de 'Start'
    df_equipos_concatenar['MES_AÑO'] = df_equipos_concatenar['Start'].dt.strftime('%m-%Y')
        
    # Extraer y formatear Hora de 'Start'
    df_equipos_concatenar['HORA'] = df_equipos_concatenar['Start'].dt.strftime('%H:%M')

    # Crear Columna de duracion restando Finish con Start
    df_equipos_concatenar['DURACION'] = (df_equipos_concatenar['Finish'] - df_equipos_concatenar['Start'])

    # Aplicar Formato hora a Duración
    df_equipos_concatenar['DURACION'] = df_equipos_concatenar['DURACION'].apply(lambda x: f"{x.components.hours:02}:{x.components.minutes:02}")
    
    # Rellenar plan con Nan
    df_equipos_concatenar['PLAN'] = np.NaN
    
    # Rellenar Examen con Nan
    df_equipos_concatenar['EXAMEN'] = np.NaN
    
    # Rellenar Sede con Nan
    df_equipos_concatenar['SEDE'] = np.NaN
    
    # Capturar orden de las columnas en df_prueba
    orden_columnas = df_prueba.columns

    # Aplicar el mismo orden de las columnas par apoder concatenar
    df_equipos_concatenar = df_equipos_concatenar[orden_columnas]

    # Crear df consolidada de programación
    df_completa = pd.concat([df_prueba, df_equipos_concatenar], ignore_index=True)

    return df_completa


# In[242]:


def creacion_horario(df_completa, selected_resouces):
    df_completa_filtro = df_completa[df_completa['RECURSO'].isin(selected_resouces)].copy()
    
    start_date = df_completa_filtro['Start'].min()
    end_date = df_completa_filtro['Finish'].max()
    
    datetime_range = pd.date_range(start=start_date, end=end_date, freq='5min')
    filtered_datetime_range = datetime_range[
        (datetime_range.hour >= 6) & (datetime_range.hour < 20)]
    
    df_schedule = pd.DataFrame(index=filtered_datetime_range)
    
    # Agregar columnas para cada recurso
    for recurso in df_completa_filtro['RECURSO'].unique():
        df_schedule[f'AGENDA PARA_{recurso}'] = 0
    
    for recurso in df_completa_filtro['RECURSO'].unique():
        df_schedule[f'AGENDA PARA_{recurso}'] = df_schedule[f'AGENDA PARA_{recurso}'].astype(object)
        for index, row in df_completa_filtro[df_completa_filtro['RECURSO'] == recurso].iterrows():
            for timestamp in pd.date_range(start=row['Start'], end=row['Finish']-pd.Timedelta(minutes=1), freq='5min'):
            
                current_value = df_schedule.loc[timestamp, f'AGENDA PARA_{recurso}']
                new_value = np.where(
                    row['DOC_DISPONIBLE'] == 'Sin Doctor Asignado', 'Disponible',
                    np.where(row['DOC_DISPONIBLE'] != 'CITA AGENDADA' and row['DOC_DISPONIBLE'] != 'Sin Doctor Asignado', row['DOC_DISPONIBLE'],
                             np.where(row['DOC_DISPONIBLE'] == 'CITA AGENDADA', row['DOC_DISPONIBLE'], 0))
                )
    
                if current_value != 'CITA AGENDADA':
                    df_schedule.loc[timestamp, f'AGENDA PARA_{recurso}'] = new_value
    df_schedule.insert(0, 'HORA', df_schedule.index.strftime('%H:%M'))
    for col in df_schedule.columns:
        if col != 'HORA':
            df_schedule[col] = df_schedule.apply(lambda row: f"{row[col]} {row['HORA']}" if row[col] != 0 else 0, axis=1)
    
    
    return df_schedule


# In[350]:


# Define a function to apply styles
def apply_styles(val):
    if isinstance(val, str) and val.startswith("Disponible"):
        return "background-color: lightgray; color: black"
    elif isinstance(val, str) and val.startswith("CITA AGENDADA"):
        return "background-color: black; color: white"
    elif val == 0 or val == "0":
        return "background-color: white; color: white"
    else:
        return "background-color: lightblue; color: black"

def style_hora_column(val):
    return "background-color: gray; color: white"


# In[362]:


def apply_conditional_styles(val, column_name):
    if column_name != 'HORA':
        if 'Disponible' in val:
            return 'background-color: lightgray; color: black;'
        elif 'CITA AGENDADA' in val:
            return 'background-color: black; color: white;'
    return ''  # Default style
def apply_styles_to_df(df):
    def style_func(val):
        column_name = df.columns[df.apply(lambda col: col == val).idxmax()]
        return apply_conditional_styles(val, column_name)
    
    return df.style.map(style_func)


# def aplicar_formato(df_schedule):
#     # Apply the styles using Styler
#     columns_to_style = df_schedule.columns.difference(['HORA'])
#     styled_df = df_schedule.style.map(apply_styles, subset= columns_to_style)
#     styled_df = styled_df.map(style_hora_column, subset=['HORA'])
#     
#     # Style the header and hide the index
#     styled_df = styled_df.set_table_styles(
#         [
#             {'selector': 'th', 'props': [('background-color', 'gray'), ('color', 'white'), ('text-align', 'center')]},
#             {'selector': 'td', 'props': [('text-align', 'center')]}  # Add this line to center text in cells
#         ]
#     ).hide(axis="index")
#     
#     # Display the styled DataFrame
#     return styled_df

# df = preprocesamiento_datos_citas(df_original_citas)
# df_equipos = preprocesamiento_datos_disponibilidad(df_original_equipos)
# 
# fecha_especifica = pd.to_datetime('2024-08-10')
# df_equipos, df_prueba = construir_programacion_completa(fecha_especifica, df, df_equipos)
# df_completa = preprocesamiento_datos_final(df_equipos, df_prueba)
# 
# selected_resouces = ['OCT CIRRUS', 'ECOGRAFO', 'PAQUIMETRO', 'OCT SOLIX']
# df_schedule = creacion_horario(df_completa, selected_resouces)
# styled_df = aplicar_formato(df_schedule)
# styled_df

# In[363]:
def formato_colores(celda):
    if 'Disponible' in str(celda):
        return 'background-color: lightgray; color: black'
    #elif 'CITA AGENDADA' in str(celda):
    #    return 'background-color: black; color: white'
    #elif celda == 0:
    #    return 'background-color: white; color: white'
    else:
        return 'background-color: lightblue; color: black'
#def color_columna_hora(col):
#       return ['background-color: gray; color: white']*len(col)

st.title("Programación de Citas Clofan")

# File uploader widget
archivo_cargado = st.file_uploader("Cargar archivo Excel", type=['xlsx', 'xls', 'xlsm'])

if archivo_cargado is not None:
    # Read the uploaded Excel file
        
    df_original_citas = cargar_datos(archivo_cargado, 
                                     nombre_hoja='CITAS', 
                                     columnas='A:H')

    df_original_equipos = cargar_datos(archivo_cargado, 
                                     nombre_hoja='DISP_EQUIPO', 
                                     columnas='A:F')
    
    df = preprocesamiento_datos_citas(df_original_citas)
    df_equipos = preprocesamiento_datos_disponibilidad(df_original_equipos)
    
    today = date.today()
    fecha_especifica = st.date_input("Seleccione una Fecha", today)
    fecha_especifica = pd.Timestamp(fecha_especifica)
    st.session_state.fecha_especifica = fecha_especifica
    df_equipos, df_prueba = construir_programacion_completa(fecha_especifica, df, df_equipos)
    df_completa = preprocesamiento_datos_final(df_equipos, df_prueba)
    st.session_state.df_completa = df_completa
    unique_resources = df_completa['RECURSO'].unique()

    # Multiselect widget for resources
    selected_resources = st.multiselect(
        "Select Resources",
        options=unique_resources,
        default=[unique_resources[0]]  # Default to the first option
    )
    st.session_state.selected_resources = selected_resources
    # Uncheck all option
    if st.button("Uncheck All"):
        st.session_state.selected_resources = [unique_resources[0]]

    # Filter the DataFrame based on selected resources
    df_schedule = creacion_horario(st.session_state.df_completa, st.session_state.selected_resources)
    #styled_df = aplicar_formato(df_schedule)
    #styled_df = apply_styles_to_df(df_schedule)
#    styled_df = df_schedule.style.map(formato_colores).apply(color_columna_hora, subset=['HORA'])
    st.session_state.df_schedule = df_schedule
    # Display in Streamlit
    st.write('Agenda para:', fecha_especifica)
    #st.dataframe(st.session_state.df_schedule.style.map(formato_colores), hide_index=True)
    #st.dataframe(st.session_state.df_schedule.style.map(formato_colores).apply(color_columna_hora, subset=['HORA']), hide_index=True, height=600)
    #st.write(styled_html, unsafe_allow_html=True)
    df_styled = df_schedule.style.applymap(lambda x: "background-color: black; color: white" if isinstance(x, str) and x.startswith("CITA AGENDADA") else "background-color: lightgray; color: balck" if isinstance(x, str) and x.startswith("disponible") else "")
    st.dataframe(df_styled, hide_index=True, height=600)
      
else:
    st.write("Por favor cargue el archivo de Programacion y Disponibilidad de Equipos")


# In[ ]:




