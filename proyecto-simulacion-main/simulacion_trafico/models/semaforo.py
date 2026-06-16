"""Lógica del ciclo semafórico coordinado para la intersección.

Modelo:
- Cra 27 (N-S) y Calle 45 (E-W) tienen ciclos idénticos (55/5/60), pero desfasados.
- Cuando Cra 27 está en VERDE/AMARILLO, Calle 45 está en ROJO.
- Cuando Calle 45 está en VERDE/AMARILLO, Cra 27 está en ROJO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import simpy


ESTADO_VERDE = "VERDE"
ESTADO_AMARILLO = "AMARILLO"
ESTADO_ROJO = "ROJO"


@dataclass(frozen=True)
class TiemposSemaforo:
    verde_s: float
    amarillo_s: float
    rojo_s: float


class ControlSemaforico:
    """Proceso activo que alterna los estados de los semáforos."""

    def __init__(
        self,
        env: simpy.Environment,
        tiempos_cra27: TiemposSemaforo,
        tiempos_cl45: TiemposSemaforo,
        via_cra27: str,
        via_cl45: str,
    ) -> None:
        self.env = env
        self._tiempos_cra27 = tiempos_cra27
        self._tiempos_cl45 = tiempos_cl45
        self._via_cra27 = via_cra27
        self._via_cl45 = via_cl45

        self._estado: Dict[str, str] = {
            self._via_cra27: ESTADO_VERDE,
            self._via_cl45: ESTADO_ROJO,
        }

        self._cambio = self.env.event()

    def estado(self, via: str) -> str:
        return self._estado[via]

    def esta_verde(self, via: str) -> bool:
        return self.estado(via) == ESTADO_VERDE

    def _notificar_cambio(self) -> None:
        if not self._cambio.triggered:
            self._cambio.succeed()
        self._cambio = self.env.event()

    def _set_estado(self, via: str, estado: str) -> None:
        self._estado[via] = estado
        self._notificar_cambio()

    def esperar_verde(self, via: str):
        """Bloquea hasta que el semáforo de la vía esté en VERDE."""

        while not self.esta_verde(via):
            yield self._cambio

    def run(self):
        """Bucle infinito del control semafórico."""

        while True:
            self._set_estado(self._via_cra27, ESTADO_VERDE)
            self._set_estado(self._via_cl45, ESTADO_ROJO)
            yield self.env.timeout(self._tiempos_cra27.verde_s)

            self._set_estado(self._via_cra27, ESTADO_AMARILLO)
            self._set_estado(self._via_cl45, ESTADO_ROJO)
            yield self.env.timeout(self._tiempos_cra27.amarillo_s)

            self._set_estado(self._via_cra27, ESTADO_ROJO)
            self._set_estado(self._via_cl45, ESTADO_VERDE)
            yield self.env.timeout(self._tiempos_cl45.verde_s)

            self._set_estado(self._via_cra27, ESTADO_ROJO)
            self._set_estado(self._via_cl45, ESTADO_AMARILLO)
            yield self.env.timeout(self._tiempos_cl45.amarillo_s)

