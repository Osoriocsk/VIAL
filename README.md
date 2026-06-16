# Simulación de tráfico (SimPy) – Cra 27 con Calle 45 (Bucaramanga)

Proyecto de simulación de eventos discretos en Python usando `simpy` para modelar una intersección semaforizada (Carrera 27 vs Calle 45) y evaluar métricas de teoría de colas: tiempos de espera y longitudes de cola.

## Requisitos

- Python 3.10+
- Dependencias: `simpy`, `numpy`, `pandas`, `matplotlib`, `streamlit`, `plotly`

## Estructura

```
streamlit_app.py
simulacion_trafico/
  main.py
  config.py
  requirements.txt
  models/
    semaforo.py
    vehiculo.py
  analytics/
    metricas.py
    validacion.py
  simulation/
    escenarios.py
    runner.py
```

## Instalación

Recomendado: entorno virtual.

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/pip install -r simulacion_trafico/requirements.txt
```

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\pip install -r simulacion_trafico\requirements.txt
```

## Ejecución

Desde la raíz del repositorio:

### Linux / macOS

```bash
.venv/bin/python -m simulacion_trafico.main
```

### Windows (PowerShell)

```powershell
.\.venv\Scripts\python -m simulacion_trafico.main
```

Al finalizar (horizonte de 3600s), el programa:

- Imprime un reporte con:
  - Total de vehículos procesados por vía
  - Tiempo de espera promedio por vía
  - Longitud máxima de cola por vía
- Genera `simulacion_trafico/resultados.png` con un histograma simple de tiempos de espera.

## Interfaz gráfica (Streamlit)

La aplicación web permite ejecutar escenarios, ver el progreso de simulación y analizar resultados con gráficas interactivas.

### Linux / macOS

```bash
.venv/bin/streamlit run streamlit_app.py
```

### Windows (PowerShell)

```powershell
.\.venv\Scripts\streamlit run streamlit_app.py
```

## Escenarios (comparación)

Por defecto, la app incluye 3 escenarios (ciclo 120s, amarillo 5s) variando el verde de Cra 27 para comparar impacto en colas y esperas:

- Base: Verde Cra 27 = 55s (Verde Calle 45 = 55s)
- Más verde Cra 27: Verde Cra 27 = 65s (Verde Calle 45 = 45s)
- Menos verde Cra 27: Verde Cra 27 = 45s (Verde Calle 45 = 65s)

También puedes agregar un escenario personalizado desde la interfaz.

## Despliegue en Streamlit Community Cloud

1. Sube este repositorio a GitHub (público o privado).
2. En Streamlit Community Cloud: New app → selecciona tu repo.
3. Configura:
   - Main file path: `streamlit_app.py`
   - Branch: `main` (o la que uses)
4. El despliegue usa por defecto:
   - `requirements.txt` en la raíz (aquí incluye `simulacion_trafico/requirements.txt`)
   - `runtime.txt` para fijar versión de Python

Si la app falla al instalar dependencias, revisa el log de build y confirma que `requirements.txt` esté en la raíz del repositorio.

## Parámetros del modelo

Todos los parámetros se encuentran en `simulacion_trafico/config.py`.

- Horizonte: 3600 s
- Llegadas:
  - Cra 27: 18 veh/min (interarribos ~ Exponencial con λ = 18/60 veh/s)
  - Calle 45: 12 veh/min (λ = 12/60 veh/s)
- Semáforos:
  - Ciclo total: 120 s
  - Cra 27: Verde 55 s, Amarillo 5 s, Rojo 60 s
  - Calle 45: Verde 55 s, Amarillo 5 s, Rojo 60 s (desfasado: inicia en rojo cuando Cra 27 está en verde)
- Servicio (cruce): 2 s por vehículo cuando está en verde

## Cómo está modelado

- El semáforo es un proceso activo que alterna estados en bucle infinito.
- Se generan dos flujos de vehículos independientes (Cra 27 y Calle 45) con interarribos exponenciales.
- Cada vía se modela como un carril (capacidad 1): solo un vehículo cruza a la vez por vía.
- Al llegar, cada vehículo:
  1. Se encola (se registra longitud de cola)
  2. Espera si el semáforo no está en VERDE
  3. Cruza consumiendo 2 segundos
  4. Registra su tiempo de espera (inicio de cruce − llegada)

## Interpretación rápida

Con los parámetros por defecto, Cra 27 tiende a saturarse: durante su fase verde (55 s) la capacidad aproximada es 55/2 = 27.5 veh por ciclo, mientras que las llegadas esperadas por ciclo son 18 veh/min * 2 min = 36 veh. Esto genera crecimiento de cola y mayores tiempos de espera.

## Publicar en GitHub

1. Inicializa repositorio y primer commit:
```bash
git init
git add .
git commit -m "Simulación de tráfico con SimPy"
```

2. Crea el repositorio en GitHub y vincúlalo (reemplaza URL):
```bash
git remote add origin https://github.com/USUARIO/REPO.git
git branch -M main
git push -u origin main
```

## Autor

Proyecto académico/experimental para simulación de eventos discretos y teoría de colas.
