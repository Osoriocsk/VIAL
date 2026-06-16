"""Ejecución de simulaciones y generación de DataFrames segundo a segundo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
import pandas as pd
import simpy

from simulacion_trafico import config
from simulacion_trafico.analytics.metricas import RecolectorMetricas
from simulacion_trafico.models.semaforo import ControlSemaforico, TiemposSemaforo
from simulacion_trafico.models.vehiculo import ParametrosFlujo, generar_flujo
from simulacion_trafico.simulation.escenarios import Escenario


@dataclass(frozen=True)
class ResultadoEscenario:
    escenario: Escenario
    serie_tiempo: pd.DataFrame
    vehiculos_cra27: pd.DataFrame
    vehiculos_cl45: pd.DataFrame
    resumen: dict[str, float | int | str]


def _longitud_cola(recurso: simpy.Resource) -> int:
    return len(recurso.queue) + recurso.count


def ejecutar_escenario(
    escenario: Escenario,
    duracion_s: int = config.SIM_DURACION_S,
    semilla: int = config.SEMILLA_ALEATORIA,
    lambda_cra27: float = config.LAMBDA_CRA27_VEH_POR_S,
    lambda_cl45: float = config.LAMBDA_CL45_VEH_POR_S,
    tiempo_cruce_s: float = config.TIEMPO_CRUCE_POR_VEH_S,
    tick_s: int = 1,
    on_tick: Optional[Callable[[int, int, dict[str, object]], None]] = None,
) -> ResultadoEscenario:
    escenario.validar()
    if duracion_s <= 0:
        raise ValueError("duracion_s debe ser mayor que 0")
    if tick_s <= 0:
        raise ValueError("tick_s debe ser mayor que 0")

    rng = np.random.default_rng(semilla)
    env = simpy.Environment()

    tiempos_cra27 = TiemposSemaforo(
        verde_s=float(escenario.verde_cra27_s),
        amarillo_s=float(escenario.amarillo_s),
        rojo_s=float(escenario.ciclo_s - (escenario.verde_cra27_s + escenario.amarillo_s)),
    )
    tiempos_cl45 = TiemposSemaforo(
        verde_s=float(escenario.verde_cl45_s),
        amarillo_s=float(escenario.amarillo_s),
        rojo_s=float(escenario.ciclo_s - (escenario.verde_cl45_s + escenario.amarillo_s)),
    )

    semaforo = ControlSemaforico(
        env=env,
        tiempos_cra27=tiempos_cra27,
        tiempos_cl45=tiempos_cl45,
        via_cra27=config.VIA_CRA27,
        via_cl45=config.VIA_CL45,
    )
    env.process(semaforo.run())

    linea_parada_cra27 = simpy.Resource(env, capacity=1)
    linea_parada_cl45 = simpy.Resource(env, capacity=1)

    metricas = RecolectorMetricas(vias=[config.VIA_CRA27, config.VIA_CL45])

    flujo_cra27 = ParametrosFlujo(
        via=config.VIA_CRA27,
        lambda_veh_por_s=lambda_cra27,
        tiempo_cruce_s=tiempo_cruce_s,
    )
    flujo_cl45 = ParametrosFlujo(
        via=config.VIA_CL45,
        lambda_veh_por_s=lambda_cl45,
        tiempo_cruce_s=tiempo_cruce_s,
    )

    env.process(
        generar_flujo(
            env=env,
            parametros=flujo_cra27,
            semaforo=semaforo,
            linea_parada=linea_parada_cra27,
            metricas=metricas,
            rng=rng,
        )
    )
    env.process(
        generar_flujo(
            env=env,
            parametros=flujo_cl45,
            semaforo=semaforo,
            linea_parada=linea_parada_cl45,
            metricas=metricas,
            rng=rng,
        )
    )

    filas: list[dict[str, object]] = []
    for t in range(0, duracion_s + 1, tick_s):
        if t > env.now:
            env.run(until=t)

        fila: dict[str, object] = {
            "t_s": int(t),
            "estado_cra27": semaforo.estado(config.VIA_CRA27),
            "estado_cl45": semaforo.estado(config.VIA_CL45),
            "cola_cra27": int(_longitud_cola(linea_parada_cra27)),
            "cola_cl45": int(_longitud_cola(linea_parada_cl45)),
            "llegadas_cra27": int(metricas.total_llegadas(config.VIA_CRA27)),
            "llegadas_cl45": int(metricas.total_llegadas(config.VIA_CL45)),
            "procesados_cra27": int(metricas.total_procesados(config.VIA_CRA27)),
            "procesados_cl45": int(metricas.total_procesados(config.VIA_CL45)),
            "espera_prom_cra27_s": float(metricas.espera_promedio(config.VIA_CRA27)),
            "espera_prom_cl45_s": float(metricas.espera_promedio(config.VIA_CL45)),
        }
        filas.append(fila)

        if on_tick is not None:
            on_tick(int(t), int(duracion_s), fila)

    df_ts = pd.DataFrame(filas)

    df_veh_cra27 = pd.DataFrame(metricas.registros_vehiculos(config.VIA_CRA27))
    if not df_veh_cra27.empty:
        df_veh_cra27.insert(0, "via", config.VIA_CRA27)

    df_veh_cl45 = pd.DataFrame(metricas.registros_vehiculos(config.VIA_CL45))
    if not df_veh_cl45.empty:
        df_veh_cl45.insert(0, "via", config.VIA_CL45)

    resumen: dict[str, float | int | str] = {
        "escenario": escenario.nombre,
        "ciclo_s": escenario.ciclo_s,
        "amarillo_s": escenario.amarillo_s,
        "verde_cra27_s": escenario.verde_cra27_s,
        "verde_cl45_s": escenario.verde_cl45_s,
        "llegadas_cra27": metricas.total_llegadas(config.VIA_CRA27),
        "llegadas_cl45": metricas.total_llegadas(config.VIA_CL45),
        "procesados_cra27": metricas.total_procesados(config.VIA_CRA27),
        "procesados_cl45": metricas.total_procesados(config.VIA_CL45),
        "espera_prom_cra27_s": metricas.espera_promedio(config.VIA_CRA27),
        "espera_prom_cl45_s": metricas.espera_promedio(config.VIA_CL45),
        "max_cola_cra27": metricas.max_cola(config.VIA_CRA27),
        "max_cola_cl45": metricas.max_cola(config.VIA_CL45),
    }

    return ResultadoEscenario(
        escenario=escenario,
        serie_tiempo=df_ts,
        vehiculos_cra27=df_veh_cra27,
        vehiculos_cl45=df_veh_cl45,
        resumen=resumen,
    )


def ejecutar_escenarios(
    escenarios: list[Escenario],
    duracion_s: int = config.SIM_DURACION_S,
    semilla_base: int = config.SEMILLA_ALEATORIA,
    on_tick: Optional[Callable[[str, int, int, dict[str, object]], None]] = None,
) -> list[ResultadoEscenario]:
    resultados: list[ResultadoEscenario] = []
    for idx, esc in enumerate(escenarios):
        def _cb(t: int, total: int, fila: dict[str, object], nombre: str = esc.nombre) -> None:
            if on_tick is not None:
                on_tick(nombre, t, total, fila)

        resultados.append(
            ejecutar_escenario(
                escenario=esc,
                duracion_s=duracion_s,
                semilla=semilla_base + idx,
                on_tick=_cb,
            )
        )
    return resultados
