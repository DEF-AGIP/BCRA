import os
import json
import ssl
import urllib.request
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
SSL_CTX = ssl._create_unverified_context()

# Variables clave que afectan a la recaudación de entidades bancarias
VARIABLE_IDS = [
    # 1. Tipo de Cambio y Bandas Cambiarias
    4, 5, 84, 1187, 1188,
    # 2. Inflación (IPC), Expectativas (REM) y Coeficientes de Indexación (CER / UVA)
    27, 28, 29, 30, 31,
    # 3. Tasas Activas por Línea de Crédito
    13, 14, 1199, 1215, 1216, 1217, 1218, 1219, 1240,
    # 4. Tasas Pasivas (Plazos Fijos y Depósitos)
    7, 8, 12, 35, 44, 1189, 1190, 1191, 1192, 1193, 1203, 1205, 1208, 1227,
    # 5. Stock de Préstamos por Línea - Total Sectores (ARS: 1275-1291, USD: 1296-1312)
    1275, 1276, 1277, 1278, 1279, 1280, 1281, 1282, 1283, 1284, 1285, 1286, 1287, 1291,
    1296, 1297, 1298, 1299, 1300, 1301, 1302, 1303, 1304, 1305, 1306, 1307, 1308, 1312,
    # 6. Stock de Préstamos por Línea - Sector Público (ARS: 1313-1326, USD: 1327-1340)
    1313, 1314, 1315, 1316, 1317, 1318, 1319, 1320, 1321, 1322, 1323, 1324, 1325, 1326,
    1327, 1328, 1329, 1330, 1331, 1332, 1333, 1334, 1335, 1336, 1337, 1338, 1339, 1340,
    # 7. Stock de Préstamos por Línea - Sector Privado (ARS: 1341-1354, USD: 1355-1368)
    1341, 1342, 1343, 1344, 1345, 1346, 1347, 1348, 1349, 1350, 1351, 1352, 1353, 1354,
    1355, 1356, 1357, 1358, 1359, 1360, 1361, 1362, 1363, 1364, 1365, 1366, 1367, 1368,
    # 8. Referencias de Balance Bancario (Plazos Fijos y Títulos Valores en Cartera)
    24, 1273, 1294
]

def fetch_json(url, retries=3):
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            if attempt == retries - 1:
                print(f"[WARN] Error consultando {url}: {e}")
    return None

def fetch_full_catalog():
    """Obtiene el catálogo completo del BCRA paginando offset=0 y offset=1000."""
    catalog = []
    for offset in (0, 1000):
        data = fetch_json(f"{BASE_URL}?offset={offset}&limit=1000")
        if data and "results" in data:
            catalog.extend(data["results"])
    return catalog

def fetch_variable_history(vid, limit=450):
    """Descarga los últimos registros históricos (aprox. 2 años hábiles diarios) de una variable."""
    data = fetch_json(f"{BASE_URL}/{vid}?limit={limit}")
    if data and "results" in data and data["results"]:
        detalle = data["results"][0].get("detalle", [])
        # Ordenar cronológicamente ascendente (YYYY-MM-DD)
        return vid, sorted(detalle, key=lambda x: x.get("fecha", ""))
    return vid, []

def main():
    print("=== INICIANDO DESCARGA DE DATOS BCRA (RECAUDACIÓN ENTIDADES FINANCIERAS) ===")
    all_catalog = fetch_full_catalog()
    if not all_catalog:
        raise RuntimeError("No se pudo obtener el catálogo de variables de la API del BCRA.")

    print(f"Catálogo BCRA obtenido: {len(all_catalog)} variables totales.")

    catalog_by_id = {item.get("idVariable"): item for item in all_catalog}
    selected_variables = []
    for vid in VARIABLE_IDS:
        item = catalog_by_id.get(vid)
        if item:
            selected_variables.append({
                "idVariable": item.get("idVariable"),
                "descripcion": (item.get("descripcion") or "").strip(),
                "ultValorInformado": item.get("ultValorInformado"),
                "ultFechaInformada": item.get("ultFechaInformada"),
                "unidadExpresion": (item.get("unidadExpresion") or "").strip(),
                "categoria": (item.get("categoria") or "").strip()
            })

    print(f"Descargando series históricas para {len(VARIABLE_IDS)} variables seleccionadas...")
    history = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_variable_history, vid): vid for vid in VARIABLE_IDS}
        for future in as_completed(futures):
            vid, serie = future.result()
            history[str(vid)] = serie

    # Regla lógica de consistencia: asegurar que el Total de Préstamos y todas sus líneas
    # aperturadas (IDs 1275 a 1368) compartan exactamente la misma fecha de cierre (sin cortes a mitad de carga).
    loan_ids = [vid for vid in VARIABLE_IDS if 1275 <= vid <= 1368]
    last_dates = [
        history[str(vid)][-1]["fecha"]
        for vid in loan_ids
        if history.get(str(vid))
    ]
    if last_dates:
        common_cutoff_date = min(last_dates)
        max_seen_date = max(last_dates)
        if common_cutoff_date != max_seen_date:
            print(f"[INFO] Normalizando cierre de préstamos a fecha común sincronizada: {common_cutoff_date} (detectado desfasaje hasta {max_seen_date})")
            for vid in loan_ids:
                s_vid = str(vid)
                if s_vid in history:
                    history[s_vid] = [pt for pt in history[s_vid] if pt["fecha"] <= common_cutoff_date]
            for v_meta in selected_variables:
                if 1275 <= v_meta["idVariable"] <= 1368:
                    serie_norm = history.get(str(v_meta["idVariable"]), [])
                    if serie_norm:
                        v_meta["ultFechaInformada"] = serie_norm[-1]["fecha"]
                        v_meta["ultValorInformado"] = serie_norm[-1]["valor"]

    art_tz = timezone(timedelta(hours=-3))
    now_iso = datetime.now(art_tz).isoformat()

    output = {
        "metadata": {
            "last_update": now_iso,
            "source": "Banco Central de la República Argentina (API Estadísticas Monetarias v4.0)",
            "variables_count": len(selected_variables)
        },
        "variables": selected_variables,
        "history": history
    }

    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "bcra_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(output_path) / 1024
    print(f"=== PROCESO FINALIZADO: {output_path} generado ({size_kb:.1f} KB) ===")

if __name__ == "__main__":
    main()
