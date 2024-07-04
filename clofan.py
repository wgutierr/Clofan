#!/usr/bin/env python
# coding: utf-8

# In[69]:


import plotly.express as px
import pandas as pd
import numpy as np
import plotly.io as pio
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, time 


# ## 1. Cargar Data

# # Definir ruta del Archivo
# ruta_archivo = r'dataset\VISOR_AYUDAS_DX_V4-CONDICIONES.xlsm'

# # Cargar tanto CITAS como DISP_EQUIPO
# df_original_citas = pd.read_excel(ruta_archivo, 
#                             sheet_name='CITAS', 
#                             usecols='A:H')
# 
# df_original_equipos = pd.read_excel(ruta_archivo, 
#                             sheet_name='DISP_EQUIPO', 
#                             usecols='A:F')

# ## 2. Pre-procesamiento de datos

# ### 2.1 Pre-procesamiento de datos de citas

# In[143]:


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




# df = preprocesamiento_datos_citas(df_original_citas)
# #df

# ### 2.2. Pre-procesamiento de datos de disponibilidad

# In[145]:


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


# df_equipos = preprocesamiento_datos_disponibilidad(df_original_equipos)
# df_equipos

# ### 2.3. Completar df_equipos con programacion semanal

# mes_año = '08-2024'

# In[154]:


def construir_programacion_completa(mes_año, df, df_equipos):
    # Filtrar por mes-año a revisar
    df_prueba = df[df['MES_AÑO'] == mes_año]

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


# df_equipos, df_prueba = construir_programacion_completa(mes_año, df, df_equipos)
# df_equipos

# ### 2.4 Pre-procesamiento de datos final

# In[150]:


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


# df_completa = preprocesamiento_datos_final(df_equipos, df_prueba)
# df_completa

# ## 3. Codigo Streamlit para publicacion

# In[153]:


# Streamlit application
st.title("Programación de Citas por Diagrama de Gantt")

# File uploader widget
archivo_cargado = st.file_uploader("Cargar archivo Excel", type=['xlsx', 'xls', 'xlsm'])

if archivo_cargado is not None:
    # Read the uploaded Excel file
    df_original_citas = pd.read_excel(archivo_cargado, 
                            sheet_name='CITAS', 
                            usecols='A:H')

    df_original_equipos = pd.read_excel(archivo_cargado, 
                            sheet_name='DISP_EQUIPO', 
                            usecols='A:F')
    
    df = preprocesamiento_datos_citas(df_original_citas)
    df_equipos = preprocesamiento_datos_disponibilidad(df_original_equipos)
    
    # Unique 'MES_ANO' values for dropdown
    mes_año_unicos = df['MES_AÑO'].unique()
    
    #Dropdown widget to select 'MES_ANO'
    mes_año = st.selectbox('Seleccionar Mes-Año', mes_año_unicos)

    
    df_equipos, df_prueba = construir_programacion_completa(mes_año, df, df_equipos)
    df_completa = preprocesamiento_datos_final(df_equipos, df_prueba)

    # Unique resources
    unique_resources = df_completa['RECURSO'].unique()

    # Multiselect widget for resources
    selected_resources = st.multiselect(
        "Select Resources",
        options=unique_resources,
        default=[unique_resources[0]]  # Default to the first option
    )

    # Uncheck all option
    if st.button("Uncheck All"):
        selected_resources = [unique_resources[0]]

    # Filter the DataFrame based on selected resources
    filtered_df = df_completa[df_completa['RECURSO'].isin(selected_resources)]

    # Plotly Gantt chart
    fig = px.timeline(
        filtered_df,
        x_start="Start",
        x_end="Finish",
        y="RECURSO",
        color="DOC_DISPONIBLE",
        title="Gantt para Citas",
        labels={"Start": "Hora Inicio", "Finish": "Hora Fin","CITA": "Cita N°"},
        color_discrete_sequence=px.colors.qualitative.Pastel,  # Use Plotly's Pastel color sequence
        hover_data={
            "Start": True,  # Display the start time in the hover label
            "Finish": True,  # Display the finish time in the hover label
            "CITA": True  # Display the "CITA" column in the hover label
        }
    )

    # Updating the x-axis to show time range
    fig.update_xaxes(
        tickformat="%d-%m-%Y %H:%M",
        range=[
            df_completa['Start'].min(),  # Specify the minimum date in the 'Start' column
            df_completa['Finish'].max()  # Specify the maximum date in the 'Finish' column
        ],
        nticks=25,  # Increase the number of ticks
        tickangle=45  # Rotate the dates by 45 degrees
    )

    num_resources = len(filtered_df['RECURSO'].unique())
    height_per_resource = 20  # Set the height per resource (adjust as needed)
    height = np.minimum(num_resources * height_per_resource * 20, 500)

    hourly_ticks = pd.date_range(start=filtered_df['Start'].min(), end=filtered_df['Finish'].max(), freq='h').tolist()
    hourly_ticks = [tick for tick in hourly_ticks if tick >= filtered_df['Start'].min() and tick <= filtered_df['Finish'].max()]

    shapes = []
    for hour_tick in hourly_ticks:
        shapes.append(
            {
                'type': 'line',
                'xref': 'x',
                'yref': 'paper',  # Reference to the y-axis (paper means relative to the plot area)
                'x0': hour_tick,
                'y0': 0,
                'x1': hour_tick,
                'y1': 1,
                'line': {
                    'color': 'rgba(68, 68, 68, 0.2)',  # Color of the line (light gray with opacity)
                    'width': 1,  # Width of the line
                    'dash': 'dot'  # Line style (dotted)
                }
            }
        )

    # Update layout with height, shapes for grid lines, and legend customization
    fig.update_layout(
        height=height,  # Specify the height in pixels
        width=1200,
        legend=dict(
            orientation="h",  # Horizontal orientation
            yanchor="top",    # Anchor legend to the top of the plot
            y=3.1,            # Position the legend slightly above the plot
            xanchor="right",  # Anchor legend to the right of the plot
            x=1               # Position the legend to the right
        ),
        shapes=shapes  # Add the shapes (dotted grid lines)
    )

    # Set opacity to 0.7
    fig.update_traces(opacity=0.8)
    fig.update_traces(marker=dict(color="black"), selector=dict(name="CITA AGENDADA"))
    fig.update_traces(marker=dict(color="lightgray"), selector=dict(name="Sin Doctor Asignado"))
    # Customize hover label style for each trace
    for trace in fig.data:
        trace.hoverlabel.bgcolor = trace.marker.color

    # Display the chart
    st.plotly_chart(fig)
else:
    st.write("Por favor cargue el archivo de Programacion y Disponibilidad de Equipos")


# In[ ]:




