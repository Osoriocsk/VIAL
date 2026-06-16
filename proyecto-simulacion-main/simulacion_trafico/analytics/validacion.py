"""Validación de consistencia del modelo y exactitud estadística básica.

La validación aquí está pensada para una entrega académica:
- Confirma que el escenario cumple el ciclo configurado.
- Verifica que el número de llegadas sea coherente con el valor esperado (Poisson) dentro de tolerancia.
- Verifica coherencia básica de conteos (procesados <= llegadas).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from simulacion_trafico import config
from simulacion_trafico.simulation.runner import ResultadoEscenario


@dataclass(frozen=True)
class Check:
    nombre: str
    ok: bool
    detalle: str


def _tolerancia_poisson(mu: float, n_sigmas: float = 3.0) -> float:
    if mu <= 0:
        return 0.0
    return n_sigmas * sqrt(mu)


def validar_resultado(
    resultado: ResultadoEscenario,
    lambda_cra27: float = config.LAMBDA_CRA27_VEH_POR_S,
    lambda_cl45: float = config.LAMBDA_CL45_VEH_POR_S,
    duracion_s: int = config.SIM_DURACION_S,
    tiempo_cruce_s: float = config.TIEMPO_CRUCE_POR_VEH_S,
) -> list[Check]:
    e = resultado.escenario

    checks: list[Check] = []
    suma_ciclo = e.verde_cra27_s + e.amarillo_s + e.verde_cl45_s + e.amarillo_s
    checks.append(
        Check(
            nombre="Ciclo semafórico",
            ok=(suma_ciclo == e.ciclo_s),
            detalle=f"Suma={suma_ciclo}s vs ciclo={e.ciclo_s}s (G_cra27={e.verde_cra27_s}, Y={e.amarillo_s}, G_cl45={e.verde_cl45_s})",
        )
    )

    mu_cra27 = lambda_cra27 * duracion_s
    mu_cl45 = lambda_cl45 * duracion_s
    tol_cra27 = _tolerancia_poisson(mu_cra27)
    tol_cl45 = _tolerancia_poisson(mu_cl45)

    lleg_cra27 = int(resultado.resumen["llegadas_cra27"])
    lleg_cl45 = int(resultado.resumen["llegadas_cl45"])

    checks.append(
        Check(
            nombre="Llegadas Cra 27 (Poisson)",
            ok=(abs(lleg_cra27 - mu_cra27) <= tol_cra27),
            detalle=f"Observado={lleg_cra27}, esperado≈{mu_cra27:.0f} ± {tol_cra27:.0f}",
        )
    )
    checks.append(
        Check(
            nombre="Llegadas Calle 45 (Poisson)",
            ok=(abs(lleg_cl45 - mu_cl45) <= tol_cl45),
            detalle=f"Observado={lleg_cl45}, esperado≈{mu_cl45:.0f} ± {tol_cl45:.0f}",
        )
    )

    proc_cra27 = int(resultado.resumen["procesados_cra27"])
    proc_cl45 = int(resultado.resumen["procesados_cl45"])
    checks.append(
        Check(
            nombre="Consistencia Cra 27",
            ok=(proc_cra27 <= lleg_cra27),
            detalle=f"Procesados={proc_cra27} <= Llegadas={lleg_cra27}",
        )
    )
    checks.append(
        Check(
            nombre="Consistencia Calle 45",
            ok=(proc_cl45 <= lleg_cl45),
            detalle=f"Procesados={proc_cl45} <= Llegadas={lleg_cl45}",
        )
    )

    ciclos_max = int((duracion_s // e.ciclo_s) + 2)
    cap_cra27 = (e.verde_cra27_s / tiempo_cruce_s) * ciclos_max
    cap_cl45 = (e.verde_cl45_s / tiempo_cruce_s) * ciclos_max
    checks.append(
        Check(
            nombre="Capacidad máxima Cra 27",
            ok=(proc_cra27 <= cap_cra27 + 1e-9),
            detalle=f"Procesados={proc_cra27} <= Capacidad≈{cap_cra27:.1f} (ciclos≈{ciclos_max})",
        )
    )
    checks.append(
        Check(
            nombre="Capacidad máxima Calle 45",
            ok=(proc_cl45 <= cap_cl45 + 1e-9),
            detalle=f"Procesados={proc_cl45} <= Capacidad≈{cap_cl45:.1f} (ciclos≈{ciclos_max})",
        )
    )

    return checks


def checks_a_markdown(escenario_nombre: str, checks: list[Check]) -> str:
    lineas = [f"### Validación: {escenario_nombre}", ""]
    for c in checks:
        estado = "OK" if c.ok else "FALLA"
        lineas.append(f"- {estado} — {c.nombre}: {c.detalle}")
    return "\n".join(lineas)
