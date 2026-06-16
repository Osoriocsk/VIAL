"""Punto de entrada para ejecutar la simulación."""

from __future__ import annotations

import os
from pathlib import Path

_mpl_dir = Path(__file__).resolve().parent / "analytics" / ".mplconfig"
os.environ.setdefault("MPLCONFIGDIR", str(_mpl_dir))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from simulacion_trafico import config
from simulacion_trafico.analytics.validacion import checks_a_markdown, validar_resultado
from simulacion_trafico.simulation.escenarios import escenarios_oficiales
from simulacion_trafico.simulation.runner import ejecutar_escenario


def main() -> int:
    escenario_base = escenarios_oficiales()[0]
    resultado = ejecutar_escenario(escenario=escenario_base)

    print("REPORTE DE SIMULACIÓN (60 min)")
    print("=" * 30)
    print(f"Escenario: {resultado.escenario.nombre}")
    print(f"Total vehículos procesados {config.VIA_CRA27}: {resultado.resumen['procesados_cra27']}")
    print(f"Tiempo de espera promedio {config.VIA_CRA27} (s): {resultado.resumen['espera_prom_cra27_s']:.2f}")
    print(f"Longitud máxima de cola {config.VIA_CRA27}: {resultado.resumen['max_cola_cra27']}")
    print("-" * 30)
    print(f"Total vehículos procesados {config.VIA_CL45}: {resultado.resumen['procesados_cl45']}")
    print(f"Tiempo de espera promedio {config.VIA_CL45} (s): {resultado.resumen['espera_prom_cl45_s']:.2f}")
    print(f"Longitud máxima de cola {config.VIA_CL45}: {resultado.resumen['max_cola_cl45']}")

    checks = validar_resultado(resultado)
    print()
    print(checks_a_markdown(resultado.escenario.nombre, checks))

    ruta_grafico = Path(__file__).resolve().parent / "resultados.png"
    plt.figure(figsize=(10, 5))
    if not resultado.vehiculos_cra27.empty:
        plt.hist(
            resultado.vehiculos_cra27["espera_s"].astype(float).to_list(),
            bins=30,
            alpha=0.6,
            label=f"Espera {config.VIA_CRA27}",
        )
    if not resultado.vehiculos_cl45.empty:
        plt.hist(
            resultado.vehiculos_cl45["espera_s"].astype(float).to_list(),
            bins=30,
            alpha=0.6,
            label=f"Espera {config.VIA_CL45}",
        )
    plt.title("Distribución de tiempos de espera")
    plt.xlabel("Tiempo de espera (s)")
    plt.ylabel("Frecuencia")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ruta_grafico, dpi=150)
    plt.close()

    print()
    print(f"Gráfico guardado en: {ruta_grafico}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
