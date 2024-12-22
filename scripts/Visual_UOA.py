import pandas as pd
import re
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
from UOA_file_selector import select_and_consolidate_files

# Inicializa la aplicación Dash
app = Dash(__name__)

# Seleccionar y cargar el archivo
print("Selecciona los archivos para el análisis.")
file_path = select_and_consolidate_files()
if file_path is None:
    print("No se seleccionó ningún archivo. Saliendo...")
    exit()

# Carga de datos
try:
    data = pd.read_csv(file_path)
    print(f"Datos cargados: {data.shape}")
    print(data.head())  # Mostrar las primeras filas para verificar el contenido

    data['Premium'] = (data['Last'] * 100) * data['Volume']

    # Filtrar datos para el gráfico 1
    filtered_data_g1 = (
        data[data['Premium'] > 1000000]
        .groupby('Symbol', as_index=False)
        .agg({'Premium': 'sum'})
        .sort_values(by='Premium', ascending=False)
    )
    print(f"Datos filtrados para el Gráfico 1: {filtered_data_g1.shape}")
    print(filtered_data_g1.head())
except Exception as e:
    print(f"Error al cargar o procesar los datos: {e}")
    filtered_data_g1 = pd.DataFrame()  # Asegura que no falle si hay errores

# Diseño de la aplicación
app.layout = html.Div([
    html.H1("Visualización Interactiva UOA", style={"textAlign": "center"}),

    # Filtro interactivo
    html.Div([
        html.Label("Selecciona Symbols:"),
        dcc.Dropdown(
            id='symbol-filter',
            options=[{'label': symbol, 'value': symbol} for symbol in filtered_data_g1['Symbol'].unique()],
            multi=True,
            placeholder="Selecciona uno o más Symbols"
        )
    ], style={"margin": "20px"}),

    dcc.Store(id='selected-symbol-store'),  # Almacenar el Symbol seleccionado

    # Primera fila: Gráficos 1 y 2
    html.Div([
        dcc.Graph(id='graph1', style={'display': 'inline-block', 'width': '48%'}),
        dcc.Graph(id='graph2', style={'display': 'inline-block', 'width': '48%'})
    ], style={'display': 'flex', 'justify-content': 'space-between'}),

    # Segunda fila: Gráficos 3 y 4
    html.Div([
        dcc.Graph(id='graph3', style={'display': 'inline-block', 'width': '48%'}),
        dcc.Graph(id='graph4', style={'display': 'inline-block', 'width': '48%'})
    ], style={'display': 'flex', 'justify-content': 'space-between'}),
])


# Callback para actualizar el Gráfico 1 con base en el filtro
@app.callback(
    Output('graph1', 'figure'),
    Input('symbol-filter', 'value')  # Escucha el filtro
)
def update_graph1(selected_symbols):
    if filtered_data_g1.empty:
        print("No hay datos disponibles para el Gráfico 1.")
        return px.bar(title="No hay datos disponibles para el Gráfico 1")

    # Filtrar los Symbols seleccionados
    filtered_data = filtered_data_g1
    if selected_symbols:
        filtered_data = filtered_data_g1[filtered_data_g1['Symbol'].isin(selected_symbols)]
        print(f"Datos filtrados para los Symbols seleccionados: {filtered_data.shape}")

    # Crear el gráfico
    fig = px.bar(
        filtered_data,
        x='Symbol',
        y='Premium',
        title="Top UOA Liquidity $1M+",
        labels={'Symbol': 'Ticker', 'Premium': 'Premium'}
    )
    fig.update_layout(
        xaxis_title=None,
        yaxis_title="Premium",
        title_font_size=18,
        xaxis_tickangle=-45,
        clickmode='event+select'  # Habilitar selección
    )
    return fig

# Callback para capturar clics en el eje X del Gráfico 1
@app.callback(
    Output('selected-symbol-store', 'data'),
    Input('graph1', 'clickData')  # Detectar clics en el gráfico
)
def capture_symbol(click_data):
    if click_data and 'points' in click_data and len(click_data['points']) > 0:
        symbol = click_data['points'][0]['x']
        print(f"Symbol capturado: {symbol}")
        return symbol
    return None

# Callback para el Gráfico 2
@app.callback(
    Output('graph2', 'figure'),
    Input('selected-symbol-store', 'data')  # Usar el Symbol capturado
)
def update_graph2(selected_symbol):
    if not selected_symbol:
        print("No se seleccionó ningún Symbol.")
        return px.bar(title="Seleccione un Symbol en el Gráfico 1")

    print(f"Actualizando con Symbol seleccionado: {selected_symbol}")

    # Filtrar datos por Symbol
    filtered_data_g2 = data[data['Symbol'] == selected_symbol]
    if filtered_data_g2.empty:
        print(f"No hay datos disponibles para {selected_symbol}")
        return px.bar(title=f"No hay datos disponibles para {selected_symbol}")

    # Procesar datos para jerarquías
    filtered_data_g2['Year'] = pd.to_datetime(filtered_data_g2['Exp Date']).dt.year
    filtered_data_g2['Month'] = pd.to_datetime(filtered_data_g2['Exp Date']).dt.strftime('%b')
    filtered_data_g2['Qtr'] = "Q" + ((pd.to_datetime(filtered_data_g2['Exp Date']).dt.month - 1) // 3 + 1).astype(str)
    filtered_data_g2['Month_Sort'] = pd.to_datetime(filtered_data_g2['Exp Date']).dt.month

    # Agrupar datos por Year, Qtr, Month, y Type
    grouped_data = (
        filtered_data_g2.groupby(['Type', 'Year', 'Qtr', 'Month', 'Month_Sort'], as_index=False)
        .agg({'Premium': 'sum'})
        .sort_values(by=['Year', 'Qtr', 'Month_Sort', 'Type'])
    )

    print("Datos agrupados para el Gráfico 2:")
    print(grouped_data)

    if grouped_data.empty:
        return px.bar(title=f"No hay datos agrupados para {selected_symbol}")

    # Crear etiquetas jerárquicas para el eje X
    grouped_data['x_label'] = grouped_data['Month'] + " (" + grouped_data['Year'].astype(str) + ")"

    # Crear el gráfico con colores personalizados
    fig = px.bar(
        grouped_data,
        x='x_label',
        y='Premium',
        color='Type',
        barmode='group',
        text='Premium',
        title=f"CALLs vs PUTs ({selected_symbol})",
        labels={'x_label': 'Mes (Año)', 'Premium': 'Premium'},
        color_discrete_map={
            "Call": "blue",  # Azul para Call
            "Put": "red"     # Rojo para Put
        }
    )

    # Ajustar el diseño del gráfico
    fig.update_layout(
        xaxis=dict(tickangle=0, title=None),
        yaxis_title="Premium",
        title_font_size=18,
        showlegend=True,
        height=700,
        margin=dict(b=150)
    )
    fig.update_traces(texttemplate='%{y}', textposition='outside')

    return fig

#Callback para Grafico #3
@app.callback(
    Output('graph3', 'figure'),
    [Input('graph1', 'clickData'),  # Symbol seleccionado
     Input('graph2', 'clickData')]  # Month-Year seleccionado
)
def update_graph3(selected_symbol_data, selected_month_data):
    # Verificar selección en gráficos previos
    if not selected_symbol_data or not selected_month_data:
        print("No se seleccionó Symbol o Month-Year.")
        return px.bar(title="Seleccione un Symbol y un Month-Year para el gráfico Pareto")

    # Obtener el Symbol seleccionado
    selected_symbol = selected_symbol_data['points'][0]['x']

    # Extraer Month y Year del formato "Dec (2024)"
    selected_month_year = selected_month_data['points'][0]['x']
    match = re.match(r"(\w+)\s\((\d{4})\)", selected_month_year)
    if not match:
        print(f"Error al interpretar Month-Year: {selected_month_year}")
        return px.bar(title="Error al interpretar Month-Year seleccionado")

    selected_month, selected_year = match.groups()
    selected_year = int(selected_year)  # Convertir Year a entero
    print(f"Symbol seleccionado: {selected_symbol}, Month-Year seleccionado: {selected_month} {selected_year}")

    # Filtrar datos por Symbol, Month-Year y Type = Call
    filtered_data = data[
        (data['Symbol'] == selected_symbol) &
        (pd.to_datetime(data['Exp Date']).dt.strftime('%b') == selected_month) &
        (pd.to_datetime(data['Exp Date']).dt.year == selected_year) &
        (data['Type'] == 'Call')  # Filtrar solo por Call
    ]

    # Imprimir datos filtrados para depuración
    print(f"Datos filtrados para {selected_symbol}, {selected_month} {selected_year} (Call): {filtered_data.shape}")
    if filtered_data.empty:
        print(f"No hay datos disponibles para Symbol: {selected_symbol}, Month-Year: {selected_month} {selected_year} (Call)")
        return px.bar(title=f"No hay datos disponibles para {selected_symbol} en {selected_month} {selected_year}")

    # Calcular Premium y Day
    filtered_data['Premium'] = filtered_data['Last'] * filtered_data['Volume'] * 100
    filtered_data['Day'] = pd.to_datetime(filtered_data['Exp Date']).dt.day

    # Determinar color basado en la lógica
    def determine_color(row):
        if pd.isna(row['Last']) or pd.isna(row['Bid']) or pd.isna(row['Ask']):
            return 'black'  # Default color for missing values
        elif row['Last'] > row['Ask']:
            return 'green'  # Verde para Last > Ask
        elif row['Last'] < row['Bid']:
            return 'red'    # Rojo para Last < Bid
        else:
            return 'yellow' # Amarillo para Bid <= Last <= Ask

    filtered_data['Color'] = filtered_data.apply(determine_color, axis=1)

    # Agrupar por Day, Strike, y Color
    grouped_data = filtered_data.groupby(['Day', 'Strike', 'Color'], as_index=False).agg({'Premium': 'sum'})

    print("Datos agrupados para el Gráfico 3:")
    print(grouped_data)

    # Mapa de colores forzados
    color_map = {
        'green': 'green',
        'red': 'red',
        'yellow': 'yellow',
        'black': 'black'  # Por si hay valores inesperados
    }

    # Crear el gráfico con colores forzados
    fig = px.bar(
        grouped_data,
        x='Day',
        y='Premium',
        color='Color',  # Usar columna Color
        text='Strike',  # Mostrar Strike como texto
        title=f"{selected_month} {selected_year} CALLs for {selected_symbol}",
        labels={'Day': 'Day', 'Premium': 'Premium'},
        color_discrete_map=color_map  # Forzar colores específicos
    )

    # Ajustar diseño del gráfico
    fig.update_layout(
        barmode='stack',  # Barras apiladas por Day
        xaxis=dict(title=None, tickangle=-90),  # Rotar etiquetas del eje x
        yaxis=dict(title="Premium"),
        title=dict(font_size=18),
        showlegend=False,  # Ocultar la leyenda de colores
        height=700,
        margin=dict(t=50, b=200)  # Ajustar margen para etiquetas jerárquicas
    )

    # Ajustar las barras
    fig.update_traces(
        texttemplate='%{text}',  # Mostrar Strike como texto
        textposition='inside',   # Colocar texto dentro de la barra
        insidetextanchor='middle',  # Centrar el texto
        marker=dict(line=dict(color='black', width=1)),  # Añadir borde negro a las barras
        textfont=dict(color='black')  # Color de texto siempre negro
    )

    return fig

#Callback para el Grafico #4
@app.callback(
    Output('graph4', 'figure'),
    [Input('graph1', 'clickData'),  # Symbol seleccionado
     Input('graph2', 'clickData')]  # Month-Year seleccionado
)
def update_graph4(selected_symbol_data, selected_month_data):
    # Verificar selección en gráficos previos
    if not selected_symbol_data or not selected_month_data:
        print("No se seleccionó Symbol o Month-Year.")
        return px.bar(title="Seleccione un Symbol y un Month-Year para el gráfico Pareto")

    # Obtener el Symbol seleccionado
    selected_symbol = selected_symbol_data['points'][0]['x']

    # Extraer Month y Year del formato "Dec (2024)"
    selected_month_year = selected_month_data['points'][0]['x']
    match = re.match(r"(\w+)\s\((\d{4})\)", selected_month_year)
    if not match:
        print(f"Error al interpretar Month-Year: {selected_month_year}")
        return px.bar(title="Error al interpretar Month-Year seleccionado")

    selected_month, selected_year = match.groups()
    selected_year = int(selected_year)  # Convertir Year a entero
    print(f"Symbol seleccionado: {selected_symbol}, Month-Year seleccionado: {selected_month} {selected_year}")

    # Filtrar datos por Symbol, Month-Year y Type = Put
    filtered_data = data[
        (data['Symbol'] == selected_symbol) &
        (pd.to_datetime(data['Exp Date']).dt.strftime('%b') == selected_month) &
        (pd.to_datetime(data['Exp Date']).dt.year == selected_year) &
        (data['Type'] == 'Put')  # Filtrar solo por Put
    ]

    # Imprimir datos filtrados para depuración
    print(f"Datos filtrados para {selected_symbol}, {selected_month} {selected_year} (Put): {filtered_data.shape}")
    if filtered_data.empty:
        print(f"No hay datos disponibles para Symbol: {selected_symbol}, Month-Year: {selected_month} {selected_year} (Put)")
        return px.bar(title=f"No hay datos disponibles para {selected_symbol} en {selected_month} {selected_year}")

    # Calcular Premium y Day
    filtered_data['Premium'] = filtered_data['Last'] * filtered_data['Volume'] * 100
    filtered_data['Day'] = pd.to_datetime(filtered_data['Exp Date']).dt.day

    # Determinar color basado en la lógica
    def determine_color(row):
        if pd.isna(row['Last']) or pd.isna(row['Bid']) or pd.isna(row['Ask']):
            return 'black'  # Default color for missing values
        elif row['Last'] > row['Ask']:
            return 'green'  # Verde para Last > Ask
        elif row['Last'] < row['Bid']:
            return 'red'    # Rojo para Last < Bid
        else:
            return 'yellow' # Amarillo para Bid <= Last <= Ask

    filtered_data['Color'] = filtered_data.apply(determine_color, axis=1)

    # Agrupar por Day, Strike, y Color
    grouped_data = filtered_data.groupby(['Day', 'Strike', 'Color'], as_index=False).agg({'Premium': 'sum'})

    print("Datos agrupados para el Gráfico 4:")
    print(grouped_data)

    # Mapa de colores forzados
    color_map = {
        'green': 'green',
        'red': 'red',
        'yellow': 'yellow',
        'black': 'black'  # Por si hay valores inesperados
    }

    # Crear el gráfico con colores forzados
    fig = px.bar(
        grouped_data,
        x='Day',
        y='Premium',
        color='Color',  # Usar columna Color
        text='Strike',  # Mostrar Strike como texto
        title=f"{selected_month} {selected_year} PUTs for {selected_symbol}",
        labels={'Day': 'Day', 'Premium': 'Premium'},
        color_discrete_map=color_map  # Forzar colores específicos
    )

    # Ajustar diseño del gráfico
    fig.update_layout(
        barmode='stack',  # Barras apiladas por Day
        xaxis=dict(title=None, tickangle=-90),  # Rotar etiquetas del eje x
        yaxis=dict(title="Premium"),
        title=dict(font_size=18),
        showlegend=False,  # Ocultar la leyenda de colores
        height=700,
        margin=dict(t=50, b=200)  # Ajustar margen para etiquetas jerárquicas
    )

    # Ajustar las barras
    fig.update_traces(
        texttemplate='%{text}',  # Mostrar Strike como texto
        textposition='inside',   # Colocar texto dentro de la barra
        insidetextanchor='middle',  # Centrar el texto
        marker=dict(line=dict(color='black', width=1)),  # Añadir borde negro a las barras
        textfont=dict(color='black')  # Color de texto siempre negro
    )

    return fig












# Ejecutar la aplicación
if __name__ == "__main__":
    print("Iniciando servidor Dash...")
    app.run_server(debug=False)

