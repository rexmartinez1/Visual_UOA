import os
import time
import random
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import platform

# Directorio raíz del proyecto
project_root = os.path.abspath(os.path.dirname(__file__))

# Verificar si estamos en un sistema Windows
is_windows = platform.system() == 'Windows'

# Cargar variables de entorno
load_dotenv(os.path.join(project_root, '.env'))
username = os.getenv("BARCHART_USERNAME")
password = os.getenv("BARCHART_PASSWORD")

# Configuración de paths relativos
data_folder = os.path.join(project_root, "..", "data")
download_folder = os.path.join(data_folder, "downloads")
uoa_folder = os.path.join(data_folder, "UOAdataToVisualize")

# Crear directorios si no existen
os.makedirs(download_folder, exist_ok=True)
os.makedirs(uoa_folder, exist_ok=True)

# Lista de User-Agents comunes
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0"
]

# Selecciona un User-Agent aleatorio
random_user_agent = random.choice(user_agents)

# Configura las opciones de Chrome
chrome_options = Options()
chrome_options.add_argument(f"user-agent={random_user_agent}")
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors=yes')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": os.path.abspath(download_folder),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})


# Función para cerrar anuncios y banners
def close_ads(driver):
    try:
        ad_frames = driver.find_elements(By.TAG_NAME, "iframe")
        for frame in ad_frames:
            driver.execute_script("arguments[0].remove();", frame)
            print("Ad iframe removed.")
    except Exception as close_ads_error:
        print(f"No ads found or unable to remove: {close_ads_error}")


# Función para realizar el login en Barchart
def login_to_barchart(driver):
    login_url = "https://www.barchart.com/login"
    driver.get(login_url)

    try:
        close_ads(driver)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Login with email']"))
        )
        driver.find_element(By.XPATH, "//input[@placeholder='Login with email']").send_keys(username)
        driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(password)
        driver.find_element(By.XPATH, "//button[contains(text(), 'Log In')]").click()
        WebDriverWait(driver, 15).until(EC.url_contains("barchart.com"))
        print("Inicio de sesión exitoso en Barchart.")
    except TimeoutException as login_error:
        print(f"Error: No se pudo completar el inicio de sesión en Barchart: {login_error}")
        driver.quit()
        raise


# Función para descargar datos
def download_data(web_driver, target_url, temp_filename):
    web_driver.get(target_url)
    time.sleep(5)

    try:
        download_button = WebDriverWait(web_driver, 15).until(
            EC.visibility_of_element_located((By.XPATH, "//a[contains(@class, 'download')]"))
        )
        web_driver.execute_script("arguments[0].click();", download_button)
        print(f"Descargando datos para {temp_filename}.")

        timeout = 30
        while timeout > 0:
            downloaded_files = [f for f in os.listdir(download_folder) if isinstance(f, str) and f.endswith('.csv')]
            if downloaded_files:
                latest_file = max([os.path.join(download_folder, f) for f in downloaded_files],
                                  key=os.path.getctime)
                if latest_file.endswith('.csv') and not latest_file.endswith('.crdownload'):
                    final_path = os.path.join(download_folder, temp_filename)
                    os.replace(latest_file, final_path)
                    print(f"{temp_filename} descargado y renombrado exitosamente.")
                    return final_path
            time.sleep(1)
            timeout -= 1
    except TimeoutException as download_error:
        print(f"No se pudo descargar los datos para {temp_filename}: {download_error}")

    return None


def clean_data(input_file_path):
    with open(input_file_path, 'r') as file:
        lines = file.readlines()
    cleaned_lines = [line for line in lines if "Downloaded from Barchart.com" not in line]
    with open(input_file_path, 'w') as file:
        file.writelines(cleaned_lines)


# URLs para descarga
urls = {
    "Stocks": "https://www.barchart.com/options/unusual-activity/stocks",
    "ETFs": "https://www.barchart.com/options/unusual-activity/etfs",
    "Indices": "https://www.barchart.com/options/unusual-activity/indices"
}

def main():
    print(f"Iniciando proceso de descarga en {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    data_frames = []

    try:
        main_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        login_to_barchart(main_driver)

        for dataset_name, dataset_url in urls.items():
            temp_file = f"{dataset_name}.csv"
            dataset_path = download_data(main_driver, dataset_url, temp_file)
            if dataset_path and os.path.isfile(dataset_path):
                clean_data(dataset_path)
                df = pd.read_csv(dataset_path)
                data_frames.append(df)
                os.remove(dataset_path)
                print(f"{dataset_name}: {len(df)} filas añadidas.")

        if data_frames:
            final_data = pd.concat(data_frames, ignore_index=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(uoa_folder, f"UOA_{timestamp}.csv")
            final_data.to_csv(output_file, index=False)
            print(f"Datos consolidados y guardados en {output_file} con un total de {len(final_data)} filas.")
        else:
            print("No se encontraron datos para consolidar.")

        main_driver.quit()
    except Exception as general_error:
        print(f"Error durante el proceso: {general_error}")


if __name__ == "__main__":
    main()
