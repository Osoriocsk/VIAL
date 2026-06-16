"""Generación y lógica de vehículos (procesos) en SimPy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import simpy

from simulacion_trafico.analytics.metricas import RecolectorMetricas
from simulacion_trafico.models.semaforo import ControlSemaforico


@dataclass(frozen=True)
class ParametrosFlujo:
    via: str
    lambda_veh_por_s: float
    tiempo_cruce_s: float


def _longitud_cola(recurso: simpy.Resource) -> int:
    return len(recurso.queue) + recurso.count


def vehiculo(
    env: simpy.Environment,
    vehiculo_id: str,
    via: str,
    semaforo: ControlSemaforico,
    linea_parada: simpy.Resource,
    tiempo_cruce_s: float,
    metricas: RecolectorMetricas,
):
    """Proceso de un vehículo individual.

    Reglas:
    - Si semáforo está en VERDE: cruza (toma 2s).
    - Si está en ROJO o AMARILLO: espera en cola hasta VERDE.
    - Se asume 1 carril por vía (un vehículo cruza a la vez por vía).
    """

    t_llegada = env.now
    metricas.registrar_llegada(
        via=via,
        t_llegada=t_llegada,
        longitud_cola=_longitud_cola(linea_parada) + 1,
    )

    with linea_parada.request() as req:
        yield req

        if not semaforo.esta_verde(via):
            yield env.process(semaforo.esperar_verde(via))

        t_inicio_cruce = env.now
        yield env.timeout(tiempo_cruce_s)
        t_fin_cruce = env.now

    metricas.registrar_cruce(
        via=via,
        vehiculo_id=vehiculo_id,
        t_llegada=t_llegada,
        t_inicio_cruce=t_inicio_cruce,
        t_fin_cruce=t_fin_cruce,
    )


def generar_flujo(
    env: simpy.Environment,
    parametros: ParametrosFlujo,
    semaforo: ControlSemaforico,
    linea_parada: simpy.Resource,
    metricas: RecolectorMetricas,
    rng: np.random.Generator,
    prefijo_id: Optional[str] = None,
):
    """Genera vehículos con tiempo entre llegadas exponencial."""

    if parametros.lambda_veh_por_s <= 0:
        raise ValueError("lambda_veh_por_s debe ser mayor que 0")

    contador = 0
    prefijo = prefijo_id or parametros.via

    while True:
        contador += 1
        vehiculo_id = f"{prefijo}-{contador}"
        env.process(
            vehiculo(
                env=env,
                vehiculo_id=vehiculo_id,
                via=parametros.via,
                semaforo=semaforo,
                linea_parada=linea_parada,
                tiempo_cruce_s=parametros.tiempo_cruce_s,
                metricas=metricas,
            )
        )

        interarribo = float(rng.exponential(scale=1.0 / parametros.lambda_veh_por_s))
        yield env.timeout(interarribo)
