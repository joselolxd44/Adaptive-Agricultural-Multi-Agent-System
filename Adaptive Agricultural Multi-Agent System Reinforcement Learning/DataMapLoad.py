from matplotlib.pylab import rand
import numpy as np
import rasterio
from bmi_topography import Topography
from rasterio.transform import xy
from math import sqrt
import VisualizationSystem as vs
# --- CONFIGURACIÓN ---
# 1. REEMPLAZA "TU_API_KEY_AQUI" con la clave que obtuviste de OpenTopography
MI_API_KEY = "4ee8a32509d978c16a6c9615fde75ea1"

SQUARE_SIZE_M=1250  # Tamaño de cada celda del grid en kilómetros

# 2. Tus coordenadas (en orden Sur, Norte, Oeste, Este)
SOUTH = -16.429766583594144  # Ymin
NORTH = -16.033212358752962  # Ymax
WEST  = -69.58308484020019   # Xmin
EAST  = -69.00455031907299   # Xmax
# --- FIN CONFIGURACIÓN ---

def descargar_y_extraer_heights(south, north, west, east, api_key):
    """Descarga un DEM (COP30) y retorna la matriz de heights y los metadatos."""
    
    print("1. Configurando la solicitud a OpenTopography...")
    # Configurar los parámetros de descarga usando 'COP30' (DEM sin vacíos)
    params = Topography.DEFAULT.copy()
    params.update({
        "dem_type": "COP30",  # <<< --- ESTA ES LA CLAVE: Usa Copernicus 30m
        "south": south,
        "north": north,
        "west": west,
        "east": east,
        "api_key": api_key,
        "output_format": "GTiff"
    })

    print(f"2. Descargando datos para el área: {west},{south} a {east},{north}")
    topo_dem = Topography(**params)
    
    # El método fetch() descarga el archivo .tif y devuelve su ruta
    archivo_tif = topo_dem.fetch()
    print(f"   Archivo descargado en: {archivo_tif}")

    print("3. Leyendo el archivo GeoTIFF con Rasterio...")
    # Usar rasterio para leer el archivo como una matriz de NumPy
    with rasterio.open(archivo_tif) as src:
        # Leer la primera banda (y única). Los datos de height están aquí.
        matriz_heights = src.read(1)
        
        # Obtener metadatos importantes
        perfil = src.profile
        transform = src.transform
        
        print(f"   Matriz de heights creada con forma: {matriz_heights.shape}")
        
        # Identificar y manejar valores "sin datos" (NoData)
        nodata_value = src.nodata
        if nodata_value is not None:
            print(f"   Valor NoData detectado: {nodata_value}. Reemplazando con NaN para facilitar el análisis.")
            # Reemplazar el valor de NoData (ej. -32768) con NaN de NumPy
            matriz_heights = np.where(matriz_heights == nodata_value, np.nan, matriz_heights)
        else:
            print("   No se detectó un valor NoData explícito.")
            
    return matriz_heights, archivo_tif, transform

# --- EJECUCIÓN PRINCIPAL ---
def download_and_process_dem():
    try:
        # Llamar a la función principal
        heights, ruta_tif, transformacion = descargar_y_extraer_heights(
            SOUTH, NORTH, WEST, EAST, MI_API_KEY
        )
        
        # --- 4. ANÁLISIS RÁPIDO DE LOS DATOS ---
        print("\n--- ANÁLISIS DE LA MATRIZ DE ALTURAS ---")
        
        # Calcular estadísticas ignorando los valores NaN (que representan los vacíos originales)
        print(f"Altura mínima encontrada: {np.nanmin(heights):.2f} metros")
        print(f"Altura máxima encontrada: {np.nanmax(heights):.2f} metros")
        print(f"Altura media: {np.nanmean(heights):.2f} metros")
        
        # Verificar si hay valores NaN (datos faltantes) en el área
        num_nan = np.sum(np.isnan(heights))
        total_pixeles = heights.size
        if num_nan > 0:
            print(f"ADVERTENCIA: Aún hay {num_nan} píxeles sin datos (NaN) de un total de {total_pixeles}.")
        else:
            print("¡ÉXITO! El DEM no contiene valores 'sin datos'. Ahora puedes calcular pendiente, rugosidad, etc.")

        # Mostrar un ejemplo de los primeros 5x5 valores de la esquina superior izquierda
        print("\nEjemplo de los primeros valores de la matriz de heights (esquina superior izquierda):")
        print(heights[:5, :5])
        
        # La variable 'heights' es una matriz de NumPy 2D que puedes usar directamente en tus cálculos
        # 'transformacion' te permite convertir entre coordenadas geográficas y las filas/columnas de la matriz
        
    except Exception as e:
        print(f"\n❌ Ocurrió un error durante el proceso: {e}")
        print("   Verifica que tu API key sea correcta y que tengas conexión a internet.")
    return heights, transformacion
        
from scipy.ndimage import label


def detectar_lago_por_conectividad(heights, transform, umbral=3812):
    """
    Detecta agua como región conectada.
    """

    # 1. máscara inicial (posibles zonas de agua)
    mask = heights > (umbral - 2)  # banda alrededor del nivel del lago

    # 2. componentes conectados
    labeled, num = label(mask)

    # 3. encontrar componente más grande (lago real)
    sizes = np.bincount(labeled.ravel())
    sizes[0] = 0  # fondo

    lago_id = np.argmax(sizes)

    lago_mask = (labeled == lago_id)

    return lago_mask

def coste_calorico_exponencial(altura_metros):
    """
    Modelo exponencial suave - el más realista biológicamente
    El coste aumenta lentamente al principio, más rápido después
    """
    COSTE_BASE = 2000
    
    # Normalizar altura (0 en 380m, 1 en 4600m)
    h_norm = (altura_metros - 380) / (4600 - 380)
    
    # Exponente 2.0 da crecimiento gradual
    # En 4600m = 2000 * 2.5 = 5000 kcal
    factor = 1 + (h_norm ** 1.8) * 1.5
    
    coste = COSTE_BASE * factor
    
    return int(round(coste, 0))


# Valores con modelo exponencial:
"""
380m  → 2000 kcal
1000m → 2085 kcal  (+85)
1500m → 2190 kcal  (+190)
2000m → 2320 kcal  (+320)
2500m → 2500 kcal  (+500)
3000m → 2750 kcal  (+750)
3500m → 3100 kcal  (+1100)
4000m → 3600 kcal  (+1600)
4300m → 4000 kcal  (+2000)
4600m → 4620 kcal  (+2620)
"""



def hallar_lago(
    heights,
    transform,
    lago_mask,
    cell_size_km=1.0,
    slope_threshold=2.0,
    lake_flat_threshold=1
):
    

    # Resolución del raster original en metros aprox
    pixel_width_deg = transform.a
    pixel_height_deg = abs(transform.e)

    # Aproximación local cerca de Titicaca
    meters_per_deg_lat = 111320
    meters_per_deg_lon = 106800

    pixel_width_m = pixel_width_deg * meters_per_deg_lon
    pixel_height_m = pixel_height_deg * meters_per_deg_lat

    # Cuántos píxeles equivalen a 1 km
    pixels_x = int(SQUARE_SIZE_M / pixel_width_m)
    pixels_y = int(SQUARE_SIZE_M / pixel_height_m)

    rows, cols = heights.shape

    grid = {}

    grid_y = 0

    for r in range(0, rows - pixels_y, pixels_y):

        grid_x = 0

        for c in range(0, cols - pixels_x, pixels_x):

            bloque = heights[r:r+pixels_y, c:c+pixels_x]

            # Ignorar bloques vacíos
            if np.isnan(bloque).all():
                grid_x += 1
                continue

            height_media = np.nanmean(bloque)

            height_min = np.nanmin(bloque)
            height_max = np.nanmax(bloque)

            pendiente = height_max - height_min
            
            rr = r
            cc = c

            rr2 = min(r + pixels_y, lago_mask.shape[0])
            cc2 = min(c + pixels_x, lago_mask.shape[1])

            if lago_mask[rr:rr2, cc:cc2].mean() > 0.6:
                No_es_lago = True
            else:
                No_es_lago = False

            if No_es_lago:
                grid_x += 1
                continue

            # Ignorar montañas imposibles
            if pendiente > 300:
                grid_x += 1
                continue

            # Coordenadas geográficas del centro
            center_r = r + pixels_y // 2
            center_c = c + pixels_x // 2

            lon, lat = xy(transform, center_r, center_c)

            grid[(grid_x, grid_y)] = {
                "x": grid_x,
                "y": grid_y,
                "es_lago": No_es_lago,
                "lat": lat,
                "lon": lon,
                "height": height_media,
                "pendiente": pendiente,
                "neighbors": []
            }

            grid_x += 1

        grid_y += 1

    return grid        


def crear_grid_sin_lago(
    heights,
    transform,
    grid_lago,
):
    """
    Reconstruye el grid base evitando crear celdas
    que ya existen en grid_lago (mismos índices x,y).
    """
    pixel_width_deg = transform.a
    pixel_height_deg = abs(transform.e)
    
    meters_per_deg_lat = 111320
    meters_per_deg_lon = 106800
    
    pixel_width_m = pixel_width_deg * meters_per_deg_lon
    pixel_height_m = pixel_height_deg * meters_per_deg_lat
    
    pixels_x = int(SQUARE_SIZE_M / pixel_width_m)
    pixels_y = int(SQUARE_SIZE_M / pixel_height_m)
    
    rows, cols = heights.shape

    grid = {}

    grid_y = 0

    for r in range(0, rows - pixels_y, pixels_y):

        grid_x = 0

        for c in range(0, cols - pixels_x, pixels_x):

            key = (grid_x, grid_y)

            
            if key in grid_lago:
                grid_x += 1
                continue

            bloque = heights[r:r+pixels_y, c:c+pixels_x]

            

            height_media = np.nanmean(bloque)

            height_max = np.nanmax(bloque)
            height_min = np.nanmin(bloque)

            pendiente = height_max - height_min

            if pendiente > 400:
                grid_x += 1
                continue

            center_r = r + pixels_y // 2
            center_c = c + pixels_x // 2

            lon, lat = xy(transform, center_r, center_c)

            cost=coste_calorico_exponencial(height_media)

            
            grid[key] = {
                "x": grid_x,
                "y": grid_y,
                "lat": lat,
                "lon": lon,
                "height": float(height_media),
                "slope": float(pendiente),
                "stay_cost": cost,
                "neighbors": [],
                "actions": {}
            }

            grid_x += 1

        grid_y += 1
    
    return grid

import numpy as np

def costo_por_celda(pendiente_grados, peso_kg=70):
    """
    Costo calórico por METRO para una celda de 1.5 km.
    
    Retorna: kcal por metro
    """
    s_rad = np.radians(pendiente_grados)
    
    # Tobler: velocidad en km/h
    velocidad_kmh = 6 * np.exp(-3.5 * abs(s_rad + 0.05))
    if pendiente_grados > 0:
        met = 3.2 + (pendiente_grados * 0.2)
    else:
        met = 2.3  # bajada o plano
    
    # kcal por hora = met * peso_kg
    kcal_por_hora = met * peso_kg
    
    # tiempo en horas para 1 km = 1 / velocidad_kmh
    # pero para 1 metro = (1 / velocidad_kmh) / 1000
    horas_por_metro = (1 / velocidad_kmh) / 1000
    
    kcal_por_metro = kcal_por_hora * horas_por_metro
    return kcal_por_metro


def costo_casilla_completa(desnivel_m, distancia_m=1500, peso_kg=70):
    """
    Costo calórico para recorrer UNA casilla de 1.5 km.
    
    Parámetros:
    - desnivel_m: cambio de height dentro de la casilla (metros)
    - distancia_m: distancia horizontal (1500 m fijo)
    """
    pendiente_grados = np.degrees(np.arctan(desnivel_m / distancia_m))
    kcal_por_metro = costo_por_celda(pendiente_grados, peso_kg)
    
    # Para casilla de 1500 m
    costo_total_kcal = kcal_por_metro * distancia_m
    
    return costo_total_kcal


def costo_acumulado_hacia_civilizacion(height, origen_fila, origen_columna, peso_kg=70):
    """
    Calcula costo calórico acumulado desde el origen (civilización) a cada casilla.
    
    Parámetros:
    - height: matriz 2D de heights (m)
    - origen_fila, origen_columna: índice de la casilla origen
    - peso_kg: peso de la persona
    """
    from scipy.sparse.csgraph import dijkstra
    
    n_filas, n_cols = height.shape
    LADO_M = 1500
    
    # Construir grafo de costo entre casillas adyacentes (8 neighbors)
    n_nodos = n_filas * n_cols
    costo_aristas = np.full((n_nodos, n_nodos), np.inf)
    
    for i in range(n_filas):
        for j in range(n_cols):
            nodo_actual = i * n_cols + j
            
            # Revisar 8 neighbors
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if di == 0 and dj == 0:
                        continue
                    
                    ni, nj = i + di, j + dj
                    if 0 <= ni < n_filas and 0 <= nj < n_cols:
                        # Desnivel entre casillas
                        desnivel = height[ni, nj] - height[i, j]
                        
                        # Distancia real (ortogonal = 1500m, diagonal = 2121m)
                        if di != 0 and dj != 0:
                            distancia_real = LADO_M * np.sqrt(2)  # 2121 m
                        else:
                            distancia_real = LADO_M  # 1500 m
                        
                        # Pendiente
                        pendiente = np.degrees(np.arctan(abs(desnivel) / distancia_real))
                        
                        # Costo calórico de esta arista
                        costo = costo_por_metro(pendiente, peso_kg) * distancia_real
                        
                        # Penalización por subida (cuesta más subir que bajar)
                        if desnivel > 0:
                            costo *= 1.3  # Subir cuesta 30% más
                        
                        nodo_vecino = ni * n_cols + nj
                        costo_aristas[nodo_actual, nodo_vecino] = costo
    
    # Nodo origen (civilización)
    nodo_origen = origen_fila * n_cols + origen_columna
    
    # Dijkstra para costos acumulados
    distancias, predecesores = dijkstra(costo_aristas, directed=True, 
                                         indices=nodo_origen, return_predecessors=True)
    
    # Reconstruir matriz
    matriz_costo = distancias.reshape(n_filas, n_cols)
    matriz_costo[matriz_costo == np.inf] = np.nan
    
    return matriz_costo, predecesores.reshape(n_filas, n_cols)

def probabilidad_movimiento(desnivel_m, distancia_m=1500, umbral_referencia=100) -> float:
    """
    Calcula la probabilidad de que la civilización INTENTE moverse a una casilla vecina.
    
    Parámetros:
    - desnivel_m: diferencia de height con la casilla vecina (positivo = subida)
    - distancia_m: distancia horizontal (1500 m fijo)
    - umbral_referencia: desnivel donde P(moverse) = 50% (por defecto 100m)
    
    Retorna:
    - P(moverse): float entre 0 y 1
    - P(quedarse): 1 - P(moverse)
    """
    
    pendiente_grados = np.degrees(np.arctan(desnivel_m / distancia_m))
    
    # Curva logística (sigmoide)
    # A mayor desnivel, menor probabilidad de moverse
    k = 0.03  # pendiente de la curva (ajustable)
    punto_medio = umbral_referencia
    
    # Probabilidad de moverse (para desnivel positivo o negativo)
    # El desnivel negativo (bajar) es más fácil, así que tratamos el valor absoluto
    desnivel_abs = abs(desnivel_m)
    
    p_moverse = 1 / (1 + np.exp(k * (desnivel_abs - punto_medio)))
    
    # Corrección: bajar es ligeramente más fácil que subir
    if desnivel_m < 0:
        p_moverse = min(1.0, p_moverse * 1.2)  # 20% más probable bajar
    
    return p_moverse

def conectar_neighbors(grid, max_slope_diff=150):

    direcciones = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1)
    ]

    for (x, y), celda in grid.items():
        
        for dx, dy in direcciones:
            estado=(x,y)
            vecino_key = (x + dx, y + dy)
            celda["actions"][vecino_key] = []
            if vecino_key not in grid:
                continue

            vecino = grid[vecino_key]

            diff_height = abs(
                celda["height"] - vecino["height"]
            )

            # Evitar saltos absurdos
            if diff_height > max_slope_diff:
                continue
            
            costo=costo_casilla_completa(diff_height)
            probabilidad=probabilidad_movimiento(diff_height)
            prob_fallo = 1 - probabilidad
            neighbor = [
                {"key": vecino_key, "probability": float(probabilidad), "cost": float(costo)},
                {"key": estado, "probability": float(prob_fallo), "cost": float(costo)}
            ]
            celda["actions"][vecino_key] = neighbor
        celda["actions"][(0,0)] = [{"key": (0,0), "probability": 1.0, "cost":celda["stay_cost"]}]
            


import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def visualizar_heights_grid(
    heights,
    transform,
    cell_size_km=1.0,
    cmap="terrain"
):
    """
    Crea un mapa de recuadros de 1 km:
    - todos los bloques (incluyendo lago)
    - color según height
    - muestra height promedio por celda
    """

    # --- Conversión aproximada grados -> metros ---
    meters_per_deg_lat = 111320
    meters_per_deg_lon = 106800

    pixel_width_deg = transform.a
    pixel_height_deg = abs(transform.e)

    pixel_width_m = pixel_width_deg * meters_per_deg_lon
    pixel_height_m = pixel_height_deg * meters_per_deg_lat

    pixels_x = int(SQUARE_SIZE_M / pixel_width_m)
    pixels_y = int(SQUARE_SIZE_M / pixel_height_m)

    
    
    rows, cols = heights.shape

    # --- Crear lista de celdas ---
    celdas = []

    for r in range(0, rows - pixels_y, pixels_y):

        for c in range(0, cols - pixels_x, pixels_x):

            bloque = heights[r:r+pixels_y, c:c+pixels_x]

            if np.isnan(bloque).all():
                continue

            height_media = np.nanmean(bloque)

            celdas.append({
                "fila": r,
                "col": c,
                "height": height_media
            })

    # --- Normalización para colores ---
    heights_lista = [c["height"] for c in celdas]

    h_min = np.min(heights_lista)
    h_max = np.max(heights_lista)

    norm = plt.Normalize(h_min, h_max)
    colormap = plt.colormaps[cmap]

    # --- Crear figura ---
    fig, ax = plt.subplots(figsize=(14, 14))

    # --- Dibujar celdas ---
    for celda in celdas:

        r = celda["fila"]
        c = celda["col"]
        h = celda["height"]

        color = colormap(norm(h))

        rect = patches.Rectangle(
            (c, r),
            pixels_x,
            pixels_y,
            linewidth=0.5,
            edgecolor='black',
            facecolor=color
        )

        ax.add_patch(rect)

        # Centro del bloque
        center_x = c + pixels_x / 2
        center_y = r + pixels_y / 2

        # Texto height
        ax.text(
            center_x,
            center_y,
            f"{int(h)}",
            ha='center',
            va='center',
            fontsize=6
        )

    # --- Configuración visual ---
    ax.set_xlim(0, cols)
    ax.set_ylim(rows, 0)

    ax.set_aspect('equal')

    ax.set_title("Mapa de heights - Grid 1km")
    ax.set_xlabel("Columnas raster")
    ax.set_ylabel("Filas raster")

    # Barra de colores
    sm = plt.cm.ScalarMappable(
        cmap=colormap,
        norm=norm
    )

    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label("Altura (m)")

    plt.show()


def visualizar_grid(grid, mostrar_ids=False):
    """
    Dibuja:
    - nodos del grid
    - conexiones entre neighbors

    Parámetros:
    - grid: diccionario generado anteriormente
    - mostrar_ids: muestra coordenadas (x,y) de cada nodo
    """

    fig, ax = plt.subplots(figsize=(12, 12))

    # --- DIBUJAR CONEXIONES ---
    for (x, y), celda in grid.items():

        lon1 = celda["lon"]
        lat1 = celda["lat"]

        for v  in celda["neighbors"]:

            vecino = grid[v["key"]]

            lon2 = vecino["lon"]
            lat2 = vecino["lat"]

            ax.plot(
                [lon1, lon2],
                [lat1, lat2],
                linewidth=0.5
            )

    # --- DIBUJAR NODOS ---
    lons = []
    lats = []

    for (x, y), celda in grid.items():

        lons.append(celda["lon"])
        lats.append(celda["lat"])

    ax.scatter(
        lons,
        lats,
        s=15
    )

    # --- IDS OPCIONALES ---
    if mostrar_ids:

        for (x, y), celda in grid.items():

            ax.text(
                celda["lon"],
                celda["lat"],
                f"{y},{x}",
                fontsize=6
            )

    # --- ESTILO ---
    ax.set_title("Grid navegable Juli + Pomata")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")

    ax.set_aspect('equal')

    plt.show()
    
 
def visualizar_heights_grid_final(
    grid,
    heights,
    transform,
    cell_size_km=1.0,
    cmap="terrain"
):
    """Mapa de celdas del grid con altura media."""

    meters_per_deg_lat = 111320
    meters_per_deg_lon = 106800

    pixel_width_deg = transform.a
    pixel_height_deg = abs(transform.e)

    pixel_width_m = pixel_width_deg * meters_per_deg_lon
    pixel_height_m = pixel_height_deg * meters_per_deg_lat

    pixels_x = max(1, int(SQUARE_SIZE_M / pixel_width_m))
    pixels_y = max(1, int(SQUARE_SIZE_M / pixel_height_m))

    rows, cols = heights.shape

    celdas = []
    grid_y = 0
    for r in range(0, rows - pixels_y + 1, pixels_y):
        grid_x = 0
        for c in range(0, cols - pixels_x + 1, pixels_x):

            # grid usa (x, y)
            if (grid_x, grid_y) not in grid:
                grid_x += 1
                continue

            bloque = heights[r:r + pixels_y, c:c + pixels_x]

            if np.isnan(bloque).all():
                grid_x += 1
                continue

            height_media = np.nanmean(bloque)

            celdas.append({
                "fila": r,
                "col": c,
                "height": height_media
            })
            grid_x += 1
        grid_y += 1

    if not celdas:
        print("No se encontraron celdas para visualizar.")
        return

    heights_lista = [celda["height"] for celda in celdas]

    h_min = np.min(heights_lista)
    h_max = np.max(heights_lista)

    norm = plt.Normalize(h_min, h_max)
    colormap = plt.colormaps[cmap]

    fig, ax = plt.subplots(figsize=(14, 14))

    for celda in celdas:

        r = celda["fila"]
        c = celda["col"]
        h = celda["height"]

        color = colormap(norm(h))

        rect = patches.Rectangle(
            (c, r),
            pixels_x,
            pixels_y,
            linewidth=0.5,
            edgecolor="black",
            facecolor=color
        )

        ax.add_patch(rect)

        center_x = c + pixels_x / 2
        center_y = r + pixels_y / 2

        ax.text(
            center_x,
            center_y,
            f"{int(h)}",
            ha="center",
            va="center",
            fontsize=6
        )

    ax.set_xlim(0, cols)
    ax.set_ylim(rows, 0)
    ax.set_aspect("equal")

    ax.set_title("Mapa de heights - Grid 1 km")
    ax.set_xlabel("Columnas raster")
    ax.set_ylabel("Filas raster")

    sm = plt.cm.ScalarMappable(
        cmap=colormap,
        norm=norm
    )

    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label("Altura (m)")

    plt.show()
   
    
def generate_grid():
    heights, transformacion=download_and_process_dem()
    lago_mask=detectar_lago_por_conectividad(heights, transformacion)
    lago_grid = hallar_lago(
        heights,
        transformacion,
        lago_mask
    )
    grid=crear_grid_sin_lago(
        heights,
        transformacion,
        lago_grid
    )
    conectar_neighbors(grid)
    return grid

def visualizar_mapa_concurrencia(grid, visits):
    """
    Mapa de calor:
    - Color = cantidad de visitas
    - Texto = altura de la celda
    """

    if not visits:
        print("No hay visitas registradas.")
        return

    # -----------------------------------------
    # Obtener dimensiones del grid
    # -----------------------------------------

    xs = [x for x, y in grid.keys()]
    ys = [y for x, y in grid.keys()]

    min_x = min(xs)
    max_x = max(xs)

    min_y = min(ys)
    max_y = max(ys)

    width = max_x - min_x + 1
    height = max_y - min_y + 1

    # -----------------------------------------
    # Matriz de visitas
    # -----------------------------------------

    heatmap = np.zeros((height, width), dtype=float)

    # -----------------------------------------
    # Rellenar matriz
    # -----------------------------------------

    for (x, y), count in visits.items():

        if (x, y) not in grid:
            continue

        row = y - min_y
        col = x - min_x

        heatmap[row, col] = count

    # -----------------------------------------
    # Crear figura
    # -----------------------------------------

    fig, ax = plt.subplots(figsize=(14, 14))

    im = ax.imshow(
        heatmap,
        origin="upper",
        interpolation="nearest",
        cmap="hot"
    )

    # -----------------------------------------
    # Escribir altura en cada celda
    # -----------------------------------------

    for (x, y), celda in grid.items():

        row = y - min_y
        col = x - min_x

        # Altura
        h = celda["height"]

        # Número de visitas
        visitas = visits.get((x, y), 0)

        ax.text(
            col,
            row,
            f"{int(h)}",
            ha="center",
            va="center",
            fontsize=5
        )

    # -----------------------------------------
    # Barra de color
    # -----------------------------------------

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Número de visitas")

    # -----------------------------------------
    # Configuración
    # -----------------------------------------

    ax.set_title(
        "Concurrencia de la civilización y altura del terreno"
    )

    ax.set_xlabel("X del Grid")
    ax.set_ylabel("Y del Grid")

    plt.show()

def main():
    heights, transformacion=download_and_process_dem()
    lago_mask=detectar_lago_por_conectividad(heights, transformacion)
    lago_grid = hallar_lago(
        heights,
        transformacion,
        lago_mask
    )
    #visualizar_grid(lago_grid, mostrar_ids=False)
    grid=crear_grid_sin_lago(
        heights,
        transformacion,
        lago_grid
    )
    #visualizar_heights_grid(heights, transformacion)
    
    conectar_neighbors(grid)
    #visualizar_grid(grid, mostrar_ids=True)
    print(grid)
    #visualizar_heights_grid_final(grid, heights, transformacion)
    
    
    
    
    
    
if __name__ == "__main__":
    main()