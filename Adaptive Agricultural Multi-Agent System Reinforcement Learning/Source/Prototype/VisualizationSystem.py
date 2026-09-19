import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

def visualizar_mapa(altura, pendiente, clasificacion=None, mascara_lago=None, 
                    titulo="Análisis de Terreno", guardar=False, nombre_archivo="mapa_terreno.png"):
    """
    Visualiza los diferentes layers del análisis de terreno.
    
    Parámetros:
    - altura: matriz 2D con valores de elevación (metros)
    - pendiente: matriz 2D con pendiente (grados)
    - clasificacion: matriz 2D con códigos (1=cultivo, 2=lago, 3=no_apto) o None
    - mascara_lago: matriz booleana 2D (True=lago) o None
    - titulo: título principal del mapa
    - guardar: si True guarda la imagen
    - nombre_archivo: nombre del archivo si guardar=True
    """
    
    # Determinar cuántos subplots mostrar
    n_plots = 2  # altura y pendiente siempre
    if clasificacion is not None:
        n_plots += 1
    if mascara_lago is not None and clasificacion is None:
        n_plots += 1
    
    # Crear figura
    fig, axes = plt.subplots(1, n_plots, figsize=(5*n_plots, 5))
    if n_plots == 1:
        axes = [axes]
    
    # Colormap personalizado para clasificación
    cmap_clasificacion = LinearSegmentedColormap.from_list(
        'clasificacion', ['#2ecc71', '#3498db', '#e74c3c'], N=3
    )
    
    plot_idx = 0
    
    # 1. Mapa de alturas
    im1 = axes[plot_idx].imshow(altura, cmap='terrain', interpolation='bilinear')
    axes[plot_idx].set_title(f'Altura\n({np.nanmin(altura):.0f} - {np.nanmax(altura):.0f} m)')
    axes[plot_idx].set_xlabel('Columna')
    axes[plot_idx].set_ylabel('Fila')
    plt.colorbar(im1, ax=axes[plot_idx], label='Elevación (m)')
    plot_idx += 1
    
    # 2. Mapa de pendiente
    im2 = axes[plot_idx].imshow(pendiente, cmap='YlOrRd', interpolation='bilinear', vmax=30)
    axes[plot_idx].set_title(f'Pendiente\n(media: {np.nanmean(pendiente):.1f}°)')
    axes[plot_idx].set_xlabel('Columna')
    axes[plot_idx].set_ylabel('Fila')
    plt.colorbar(im2, ax=axes[plot_idx], label='Pendiente (°)')
    plot_idx += 1
    
    # 3. Clasificación o máscara de lago
    if clasificacion is not None:
        im3 = axes[plot_idx].imshow(clasificacion, cmap=cmap_clasificacion, 
                                     interpolation='nearest', vmin=1, vmax=3)
        axes[plot_idx].set_title('Clasificación de Terreno')
        axes[plot_idx].set_xlabel('Columna')
        axes[plot_idx].set_ylabel('Fila')
        
        # Crear leyenda manual
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#2ecc71', label='Cultivable'),
            Patch(facecolor='#3498db', label='Lago'),
            Patch(facecolor='#e74c3c', label='No apto')
        ]
        axes[plot_idx].legend(handles=legend_elements, loc='upper right')
        
    elif mascara_lago is not None:
        # Mostrar máscara de lago superpuesta
        fondo = np.zeros_like(mascara_lago, dtype=np.float32)
        fondo[mascara_lago] = 1
        im3 = axes[plot_idx].imshow(fondo, cmap='Blues', interpolation='nearest', alpha=0.7)
        axes[plot_idx].set_title(f'Lago\n({np.sum(mascara_lago)} celdas)')
        axes[plot_idx].set_xlabel('Columna')
        axes[plot_idx].set_ylabel('Fila')
        plt.colorbar(im3, ax=axes[plot_idx], label='Lago')
    
    plt.suptitle(titulo, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if guardar:
        plt.savefig(nombre_archivo, dpi=150, bbox_inches='tight')
        print(f"✓ Mapa guardado: {nombre_archivo}")
    
    plt.show()


def visualizar_grid_1km(grid_data, altura_shape, resolucion_m=500):
    """
    Visualiza el grid de 1 km como mapa de bloques.
    
    Parámetros:
    - grid_data: lista de diccionarios con datos del grid
    - altura_shape: tuple (filas, columnas) del DEM original
    - resolucion_m: resolución en metros del DEM
    """
    
    if not grid_data:
        print("No hay datos para visualizar")
        return
    
    # Convertir a DataFrame para facilitar
    import pandas as pd
    df = pd.DataFrame(grid_data)
    
    # Encontrar dimensiones del grid
    max_fila = df['fila'].max()
    max_col = df['columna'].max()
    
    # Crear matriz para visualización
    matriz_altura = np.full((max_fila + 1, max_col + 1), np.nan)
    matriz_validez = np.zeros((max_fila + 1, max_col + 1), dtype=bool)
    
    for _, row in df.iterrows():
        i, j = int(row['fila']), int(row['columna'])
        if row['es_valido']:
            matriz_altura[i, j] = row['altura_media_m']
            matriz_validez[i, j] = True
    
    # Crear figura
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Mapa de alturas por recuadro
    im1 = ax1.imshow(matriz_altura, cmap='terrain', interpolation='nearest')
    ax1.set_title(f'Grid 1km - Altura media\n({len(df)} recuadros)')
    ax1.set_xlabel('Columna (1 km)')
    ax1.set_ylabel('Fila (1 km)')
    plt.colorbar(im1, ax=ax1, label='Altura (m)')
    
    # Mapa de validez
    ax2.imshow(matriz_validez, cmap='Greens', interpolation='nearest', vmin=0, vmax=1)
    ax2.set_title('Recuadros válidos (sin lago)')
    ax2.set_xlabel('Columna (1 km)')
    ax2.set_ylabel('Fila (1 km)')
    
    plt.tight_layout()
    plt.show()
    
    print(f"\n📊 Resumen grid:")
    print(f"   Total recuadros: {len(df)}")
    print(f"   Válidos: {df['es_valido'].sum()}")
    print(f"   Inválidos (lago o sin datos): {(~df['es_valido']).sum()}")


def visualizar_perfil_transecto(altura, pendiente, fila=None, columna=None):
    """
    Visualiza un perfil transversal (fila fija o columna fija) del terreno.
    
    Parámetros:
    - altura: matriz 2D de alturas
    - pendiente: matriz 2D de pendiente
    - fila: índice de fila para perfil horizontal (None = usar columna)
    - columna: índice de columna para perfil vertical (None = usar fila)
    """
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    if fila is not None:
        # Perfil horizontal (fila fija)
        perfil_altura = altura[fila, :]
        perfil_pendiente = pendiente[fila, :]
        titulo = f"Perfil transversal - Fila {fila}"
        
        ax1.plot(perfil_altura, 'b-', linewidth=1.5)
        ax1.set_ylabel('Altura (m)')
        ax1.grid(True, alpha=0.3)
        
        ax2.plot(perfil_pendiente, 'r-', linewidth=1.5)
        ax2.set_ylabel('Pendiente (°)')
        ax2.set_xlabel('Columna (celda)')
        ax2.grid(True, alpha=0.3)
        
    elif columna is not None:
        # Perfil vertical (columna fija)
        perfil_altura = altura[:, columna]
        perfil_pendiente = pendiente[:, columna]
        titulo = f"Perfil longitudinal - Columna {columna}"
        
        ax1.plot(perfil_altura, 'b-', linewidth=1.5)
        ax1.set_ylabel('Altura (m)')
        ax1.grid(True, alpha=0.3)
        
        ax2.plot(perfil_pendiente, 'r-', linewidth=1.5)
        ax2.set_ylabel('Pendiente (°)')
        ax2.set_xlabel('Fila (celda)')
        ax2.grid(True, alpha=0.3)
    else:
        print("Especifica 'fila' o 'columna'")
        return
    
    fig.suptitle(titulo, fontsize=12)
    plt.tight_layout()
    plt.show()
    
    # Estadísticas del perfil
    print(f"\n📊 Estadísticas del perfil:")
    print(f"   Altura media: {np.nanmean(perfil_altura):.1f} m")
    print(f"   Altura min/max: {np.nanmin(perfil_altura):.1f} / {np.nanmax(perfil_altura):.1f} m")
    print(f"   Pendiente media: {np.nanmean(perfil_pendiente):.1f}°")
    print(f"   Desnivel total: {np.nanmax(perfil_altura) - np.nanmin(perfil_altura):.1f} m")


def visualizar_3d(altura, mascara_lago=None, elevacion=30, azimut=45, guardar=False):
    """
    Visualización 3D del terreno.
    
    Parámetros:
    - altura: matriz 2D de alturas
    - mascara_lago: matriz booleana (True=lago) para resaltar
    - elevacion: ángulo de elevación de la cámara (grados)
    - azimut: ángulo de rotación (grados)
    """
    from mpl_toolkits.mplot3d import Axes3D
    
    # Crear grid de coordenadas
    x = np.arange(altura.shape[1])
    y = np.arange(altura.shape[0])
    X, Y = np.meshgrid(x, y)
    
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Normalizar alturas para colores
    norm = plt.Normalize(vmin=np.nanmin(altura), vmax=np.nanmax(altura))
    
    # Graficar superficie
    surf = ax.plot_surface(X, Y, altura, cmap='terrain', 
                           norm=norm, alpha=0.9, linewidth=0, 
                           antialiased=True)
    
    # Resaltar lago si se proporciona
    if mascara_lago is not None and np.any(mascara_lago):
        # Crear máscara para lago
        lago_mask = np.ma.masked_where(~mascara_lago, altura)
        ax.plot_surface(X, Y, lago_mask, color='blue', alpha=0.5, linewidth=0)
    
    ax.view_init(elev=elevacion, azim=azimut)
    ax.set_xlabel('Columna')
    ax.set_ylabel('Fila')
    ax.set_zlabel('Altura (m)')
    ax.set_title('Modelo de Elevación Digital (3D)')
    
    plt.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='Altura (m)')
    
    if guardar:
        plt.savefig('terreno_3d.png', dpi=150, bbox_inches='tight')
        print("✓ Visualización 3D guardada: terreno_3d.png")
    
    plt.show()