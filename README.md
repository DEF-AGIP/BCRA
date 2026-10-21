# DEFBCRA · Monitor de Variables Bancarias (BCRA)

Tablero ejecutivo para el seguimiento diario de las variables del Banco Central de la República Argentina (BCRA) que impactan en la actividad y recaudación de entidades financieras:

1. **Stock de Deuda por Línea de Crédito** (Categoría *Préstamos por línea* / `diar_fin.xls` de la API v4.0 del BCRA), abierto por:
   - **Sectores**: `Sector Privado`, `Sector Público` y `Total de Sectores`.
   - **Monedas**: `Pesos (ARS)`, `Dólares (USD)` y `Consolidado en Pesos` (valuado al Tipo de Cambio Contable del BCRA).
   - **Líneas**: Adelantos en Cuenta Corriente, Otros Adelantos, Documentos a Sola Firma, Descuento de Documentos, Documentos Comprados, Préstamos Personales, Tarjetas de Crédito, Préstamos Hipotecarios, Préstamos Prendarios, Créditos Documentarios, Otros Préstamos e Intereses Documentados.
2. **Tasas Activas de Líneas de Crédito (% TNA)**: Personales, Tarjetas de Crédito, Adelantos en Cta. Cte., Documentos a Sola Firma, Hipotecarios (Tasa Fija y UVA) y Prendarios.
3. **Tasas Pasivas de Plazos Fijos (% TNA / % TEA)**: Total Sistema en Pesos, Personas Humanas, Personas Jurídicas, Prestadores de Servicios Financieros, tramos de plazo (30 días, 7-59 días, 60+ días), BADLAR, TM20, TAMAR, Plazo Fijo UVA y Plazo Fijo USD.
4. **Tipo de Cambio ($/USD)**: Mayorista (Com. A 3500), Valuación Contable BCRA, Minorista y Bandas Cambiarias.
5. **Inflación y Coeficientes de Ajuste**: IPC Mensual, IPC Interanual, REM (12M), CER y UVA.

## Estructura del Repositorio

```text
DEFBCRA-main/
├── .github/workflows/update_data.yml  # Automatización diaria vía GitHub Actions
├── data/bcra_data.json                # Base de datos JSON actualizada desde la API v4.0 del BCRA
├── fetch_data.py                      # Script Python (sin dependencias externas)
├── index.html                         # Tablero web ejecutivo (Tailwind CSS + Chart.js)
└── README.md
```

## Puesta en marcha en GitHub

1. **No requiere claves secretas (`Secrets`)**: La API Estadísticas Monetarias v4.0 del BCRA es pública y gratuita, y el script `fetch_data.py` utiliza únicamente librerías nativas de Python.
2. Subí el contenido de esta carpeta a tu repositorio en GitHub.
3. En **Settings > Pages**, activá GitHub Pages apuntando a la rama `main` (`/` root).
4. En **Settings > Actions > General > Workflow permissions**, verificá que esté seleccionada la opción **Read and write permissions** para permitir que la acción diaria actualice `data/bcra_data.json`.
