import os
import pandas as pd
from datetime import datetime
from tkinter import Tk, filedialog

# Ruta base fija para el proyecto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_FOLDER = os.path.join(BASE_DIR, "data", "UOAdataToVisualize")


def ensure_folder_exists(folder_path):
    """Crea el folder si no existe."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def select_files():
    """Permite al usuario seleccionar uno o más archivos para el análisis."""
    Tk().withdraw()  # Oculta la ventana principal de Tkinter
    ensure_folder_exists(DATA_FOLDER)  # Asegura que el folder existe
    file_paths = filedialog.askopenfilenames(
        title="Selecciona uno o más archivos",
        initialdir=DATA_FOLDER,
        filetypes=[("Archivos CSV", "*.csv"), ("Archivos Excel", "*.xlsx")]
    )
    return file_paths


def consolidate_files(file_paths):
    """Consolida múltiples archivos en uno solo."""
    consolidated_data = pd.DataFrame()

    for file_path in file_paths:
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            data = pd.read_excel(file_path)
        else:
            print(f"Formato no soportado: {file_path}")
            continue

        consolidated_data = pd.concat([consolidated_data, data], ignore_index=True)

    # Guardar archivo consolidado
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(DATA_FOLDER, f"UOA_Combined_{timestamp}.csv")
    consolidated_data.to_csv(output_file, index=False)
    print(f"Archivo consolidado guardado en: {output_file}")
    return output_file


def select_and_consolidate_files():
    """Selecciona archivos, los consolida y devuelve la ruta del archivo listo."""
    print("Selecciona los archivos para el análisis.")
    file_paths = select_files()

    if not file_paths:
        print("No se seleccionaron archivos.")
        return None

    if len(file_paths) > 1:
        print("Consolidando archivos seleccionados...")
        consolidated_file = consolidate_files(file_paths)
        print(f"Archivos consolidados en: {consolidated_file}")
        return consolidated_file
    else:
        print(f"Archivo único seleccionado: {file_paths[0]}")
        return file_paths[0]


if __name__ == "__main__":
    # Este bloque permite ejecutar el archivo para probar la funcionalidad
    result = select_and_consolidate_files()
    if result:
        print(f"Archivo procesado: {result}")
    else:
        print("No se procesaron archivos.")