import pandas as pd
import plotly.express as px

# Ruta del archivo
file_path = "C:/Users/rexma/OneDrive/Documents/Visual_UOA/data/UOAdataToVisualize/UOA_20241220_160857.csv"

# Cargar los datos
data = pd.read_csv(file_path)
print(f"Datos cargados: {data.shape}")
print(data.head())

# Crear una nueva columna "Premium"
data['Premium'] = data['Last'] * data['Volume']

# Filtrar y agrupar
filtered_data = (
    data[data['Premium'] > 1000000]
    .groupby('Symbol', as_index=False)
    .agg({'Premium': 'sum'})
    .sort_values(by='Premium', ascending=False)
)

print(f"Datos filtrados: {filtered_data.shape}")
print(filtered_data.head())

# Crear el gráfico
fig = px.bar(
    filtered_data,
    x='Symbol',
    y='Premium',
    title="Top UOA Liquidity $1M+",
    labels={'Symbol': 'Ticker', 'Premium': 'Premium'}
)

# Mostrar el gráfico
fig.show()
