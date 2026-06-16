"""Definición de escenarios para comparar cambios en tiempos de verde.

Convención del ciclo:
- Cra 27: VERDE -> AMARILLO
- Calle 45: VERDE -> AMARILLO
Total ciclo = G_cra27 + Y + G_cl45 + Y
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Escenario:
    nombre: str
    ciclo_s: int
    amarillo_s: int
    verde_cra27_s: int

    @property
    def verde_cl45_s(self) -> int:
        return int(self.ciclo_s - self.verde_cra27_s - 2 * self.amarillo_s)

    def validar(self) -> None:
        if self.ciclo_s <= 0:
            raise ValueError("ciclo_s debe ser mayor que 0")
        if self.amarillo_s <= 0:
            raise ValueError("amarillo_s debe ser mayor que 0")
        if self.verde_cra27_s <= 0:
            raise ValueError("verde_cra27_s debe ser mayor que 0")
        if self.verde_cl45_s <= 0:
            raise ValueError(
                "verde_cl45_s calculado no es válido; ajusta verde_cra27_s/amarillo_s/ciclo_s"
            )


def escenarios_oficiales() -> list[Escenario]:
    """Tres escenarios para comparación académica.

Se mantiene ciclo total 120s y amarillo 5s, variando el verde de Cra 27.
"""

    base = Escenario(nombre="Base (G=55)", ciclo_s=120, amarillo_s=5, verde_cra27_s=55)
    mas_verde = Escenario(nombre="Más verde Cra 27 (G=65)", ciclo_s=120, amarillo_s=5, verde_cra27_s=65)
    menos_verde = Escenario(nombre="Menos verde Cra 27 (G=45)", ciclo_s=120, amarillo_s=5, verde_cra27_s=45)
    for e in (base, mas_verde, menos_verde):
        e.validar()
    return [base, mas_verde, menos_verde]

