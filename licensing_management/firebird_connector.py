import os

import fdb
from dotenv import load_dotenv

# Carga las variables de entorno del archivo .env
load_dotenv()

# --- Configuración de la base de datos Firebird ---
# Es crucial que estos datos coincidan con tu configuración real de Firebird
# Puedes definirlos en tu .env o directamente aquí si lo prefieres,
# pero las variables de entorno son más seguras.
FIREBIRD_HOST = os.getenv(
    "FIREBIRD_HOST", "localhost"
)  # IP o nombre del host donde corre Firebird
FIREBIRD_PORT = int(os.getenv("FIREBIRD_PORT", "3050"))  # Puerto de Firebird
FIREBIRD_DB_PATH = os.getenv(
    "FIREBIRD_DB_PATH", "/ruta/a/tu/base/datos/SAEDAT01.FDB"
)  # ¡RUTA ABSOLUTA O RELATIVA ACCESIBLE DESDE EL CONTENEDOR!
FIREBIRD_USER = os.getenv("FIREBIRD_USER", "SYSDBA")  # Usuario de Firebird
FIREBIRD_PASSWORD = os.getenv(
    "FIREBIRD_PASSWORD", "masterkey"
)  # Contraseña de Firebird
FIREBIRD_CHARSET = os.getenv(
    "FIREBIRD_CHARSET", "WIN1251"
)  # O tu charset, comúnmente WIN1251 o ISO8859_1
FIREBIRD_ENCODING = os.getenv(
    "FIREBIRD_ENCODING", "latin-1"
)  # Encoding de Python para decodificar (generalmente coincide con charset)


def get_firebird_connection():
    """
    Establece y retorna una conexión a la base de datos Firebird.
    """
    conn = None
    try:
        conn = fdb.connect(
            host=FIREBIRD_HOST,
            port=FIREBIRD_PORT,
            database=FIREBIRD_DB_PATH,
            user=FIREBIRD_USER,
            password=FIREBIRD_PASSWORD,
            charset=FIREBIRD_CHARSET,
        )
        print("Conexión a Firebird establecida exitosamente.")
        return conn
    except fdb.Error as e:
        print(f"Error al conectar a Firebird: {e}")
        # Considera relanzar la excepción o manejarla de forma más robusta
        return None


def fetch_data_from_firebird(query):
    """
    Ejecuta una consulta SQL en Firebird y retorna los resultados.
    """
    conn = None
    cursor = None
    try:
        conn = get_firebird_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]  # Nombres de las columnas
            rows = cursor.fetchall()

            # Convertir a una lista de diccionarios para facilitar el manejo
            results = []
            for row in rows:
                row_dict = {}
                for i, col_name in enumerate(columns):
                    value = row[i]
                    # Decodificar si es bytes y no es None
                    if isinstance(value, bytes):
                        try:
                            value = value.decode(FIREBIRD_ENCODING)
                        except UnicodeDecodeError:
                            print(
                                f"Advertencia: No se pudo decodificar el valor '{value}' con {FIREBIRD_ENCODING}"
                            )
                            value = value.decode(
                                "utf-8", errors="ignore"
                            )  # Intenta con utf-8 o ignora errores
                    row_dict[col_name] = value
                results.append(row_dict)
            return results
        else:
            return []
    except fdb.Error as e:
        print(f"Error al ejecutar consulta en Firebird: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    # Ejemplo de uso (solo se ejecuta si corres este archivo directamente)
    print("Intentando conectar y obtener datos de clientes de Firebird...")
    # Esta consulta es solo un ejemplo, ajusta el nombre de la tabla/columnas
    # a tu esquema real de Aspel SAE (ej. CLIENTES, CLAVE, NOMBRE)
    sample_query = (
        "SELECT CLAVE, NOMBRE, RFC FROM CLIE01 WHERE STATUS='A' ORDER BY CLAVE ROWS 10"
    )
    client_data = fetch_data_from_firebird(sample_query)

    if client_data:
        print(f"Se encontraron {len(client_data)} clientes:")
        for client in client_data:
            print(client)
    else:
        print("No se pudieron obtener datos de clientes o no se encontraron.")
