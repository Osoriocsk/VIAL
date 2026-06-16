"""Recolección de datos, cálculo de promedios y gráficas."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, List

_mpl_dir = Path(__file__).resolve().parent / ".mplconfig"
os.environ.setdefault("MPLCONFIGDIR", str(_mpl_dir))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


@dataclass
class _DatosVia:
    tiempos_espera: List[float] = field(default_factory=list)
    llegadas: int = 0
    total_procesados: int = 0
    max_cola: int = 0
    registros_vehiculos: List[Dict[str, float | str]] = field(default_factory=list)


class RecolectorMetricas:
    """Acumula métricas para cada vía."""

    def __init__(self, vias: List[str]) -> None:
        self._datos: Dict[str, _DatosVia] = {via: _DatosVia() for via in vias}

    def registrar_llegada(self, via: str, t_llegada: float, longitud_cola: int) -> None:
        _ = t_llegada
        datos = self._datos[via]
        datos.llegadas += 1
        datos.max_cola = max(datos.max_cola, int(longitud_cola))

    def registrar_cruce(
        self,
        via: str,
        vehiculo_id: str,
        t_llegada: float,
        t_inicio_cruce: float,
        t_fin_cruce: float,
    ) -> None:
        datos = self._datos[via]
        datos.total_procesados += 1
        espera = float(t_inicio_cruce - t_llegada)
        datos.tiempos_espera.append(espera)
        datos.registros_vehiculos.append(
            {
                "vehiculo_id": vehiculo_id,
                "t_llegada": float(t_llegada),
                "t_inicio_cruce": float(t_inicio_cruce),
                "t_fin_cruce": float(t_fin_cruce),
                "espera_s": espera,
            }
        )

    def total_llegadas(self, via: str) -> int:
        return self._datos[via].llegadas

    def total_procesados(self, via: str) -> int:
        return self._datos[via].total_procesados

    def espera_promedio(self, via: str) -> float:
        tiempos = self._datos[via].tiempos_espera
        if not tiempos:
            return 0.0
        return sum(tiempos) / len(tiempos)

    def max_cola(self, via: str) -> int:
        return self._datos[via].max_cola

    def tiempos_espera(self, via: str) -> List[float]:
        return list(self._datos[via].tiempos_espera)

    def registros_vehiculos(self, via: str) -> List[Dict[str, float | str]]:
        return list(self._datos[via].registros_vehiculos)

    def generar_reporte(self, via_1: str, via_2: str) -> str:
        lineas = [
            "REPORTE DE SIMULACIÓN (60 min)",
            "=" * 30,
            f"Total vehículos procesados {via_1}: {self.total_procesados(via_1)}",
            f"Tiempo de espera promedio {via_1} (s): {self.espera_promedio(via_1):.2f}",
            f"Longitud máxima de cola {via_1}: {self.max_cola(via_1)}",
            "-" * 30,
            f"Total vehículos procesados {via_2}: {self.total_procesados(via_2)}",
            f"Tiempo de espera promedio {via_2} (s): {self.espera_promedio(via_2):.2f}",
            f"Longitud máxima de cola {via_2}: {self.max_cola(via_2)}",
        ]
        return "\n".join(lineas)

    def guardar_grafico(self, via_1: str, via_2: str, ruta_salida: Path) -> None:
        tiempos_1 = self._datos[via_1].tiempos_espera
        tiempos_2 = self._datos[via_2].tiempos_espera

        plt.figure(figsize=(10, 5))
        bins = 30
        if tiempos_1:
            plt.hist(tiempos_1, bins=bins, alpha=0.6, label=f"Espera {via_1}")
        if tiempos_2:
            plt.hist(tiempos_2, bins=bins, alpha=0.6, label=f"Espera {via_2}")

        plt.title("Distribución de tiempos de espera")
        plt.xlabel("Tiempo de espera (s)")
        plt.ylabel("Frecuencia")
        plt.legend()
        plt.tight_layout()

        ruta_salida.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(ruta_salida, dpi=150)
        plt.close()
