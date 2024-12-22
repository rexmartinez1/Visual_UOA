import pandas as pd

# Ruta del archivo seleccionado
file_path = "C:/Users/rexma/OneDrive/Documents/Visual_UOA/data/UOAdataToVisualize/UOA_20241220_160857.csv"  # Cambia según corresponda

# Cargar los datos
try:
    data = pd.read_csv(file_path)
    print(f"Datos cargados: {data.shape}")
    print(data.head())  # Muestra las primeras filas para validar el contenido
except Exception as e:
    print(f"Error al cargar los datos: {e}")
