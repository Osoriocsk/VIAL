from __future__ import annotations

from dataclasses import asdict
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from simulacion_trafico.analytics.validacion import validar_resultado
from simulacion_trafico.simulation.escenarios import Escenario, escenarios_oficiales
from simulacion_trafico.simulation.runner import ResultadoEscenario, ejecutar_escenarios


def _resumen_df(resultados: list[ResultadoEscenario]) -> pd.DataFrame:
    df = pd.DataFrame([r.resumen for r in resultados])
    if df.empty:
        return df
    df["throughput_cra27_veh_min"] = df["procesados_cra27"] / 60
    df["throughput_cl45_veh_min"] = df["procesados_cl45"] / 60
    return df


def _checks_df(resultados: list[ResultadoEscenario]) -> pd.DataFrame:
    filas: list[dict[str, Any]] = []
    for r in resultados:
        for c in validar_resultado(r):
            filas.append(
                {
                    "escenario": r.escenario.nombre,
                    "check": c.nombre,
                    "ok": c.ok,
                    "detalle": c.detalle,
                }
            )
    return pd.DataFrame(filas)


def _plot_colas(r: ResultadoEscenario):
    df = r.serie_tiempo[["t_s", "cola_cra27", "cola_cl45"]].copy()
    df = df.melt(id_vars="t_s", var_name="via", value_name="cola")
    df["via"] = df["via"].replace({"cola_cra27": "Cra 27", "cola_cl45": "Calle 45"})
    fig = px.line(
        df,
        x="t_s",
        y="cola",
        color="via",
        title=f"Evolución de colas — {r.escenario.nombre}",
        labels={"t_s": "Tiempo (s)", "cola": "Vehículos en cola"},
    )
    fig.update_layout(legend_title_text="Vía")
    return fig


def _plot_espera_prom(r: ResultadoEscenario):
    df = r.serie_tiempo[["t_s", "espera_prom_cra27_s", "espera_prom_cl45_s"]].copy()
    df = df.melt(id_vars="t_s", var_name="via", value_name="espera_prom_s")
    df["via"] = df["via"].replace({"espera_prom_cra27_s": "Cra 27", "espera_prom_cl45_s": "Calle 45"})
    fig = px.line(
        df,
        x="t_s",
        y="espera_prom_s",
        color="via",
        title=f"Evolución de espera promedio — {r.escenario.nombre}",
        labels={"t_s": "Tiempo (s)", "espera_prom_s": "Espera promedio (s)"},
    )
    fig.update_layout(legend_title_text="Vía")
    return fig


def _plot_hist_esperas(r: ResultadoEscenario):
    df = pd.concat([r.vehiculos_cra27, r.vehiculos_cl45], ignore_index=True)
    if df.empty:
        return None
    df = df.copy()
    df["via"] = df["via"].replace({"CRA27": "Cra 27", "CL45": "Calle 45"})
    fig = px.histogram(
        df,
        x="espera_s",
        color="via",
        nbins=40,
        barmode="overlay",
        opacity=0.6,
        title=f"Distribución de tiempos de espera — {r.escenario.nombre}",
        labels={"espera_s": "Tiempo de espera (s)"},
    )
    fig.update_layout(legend_title_text="Vía")
    return fig


def _plot_comparativa(resumen: pd.DataFrame):
    df = resumen.copy()
    if df.empty:
        return None
    metricas = [
        ("espera_prom_cra27_s", "Espera prom Cra 27 (s)"),
        ("espera_prom_cl45_s", "Espera prom Calle 45 (s)"),
        ("max_cola_cra27", "Máx cola Cra 27"),
        ("max_cola_cl45", "Máx cola Calle 45"),
    ]
    filas = []
    for col, label in metricas:
        for _, row in df.iterrows():
            filas.append({"escenario": row["escenario"], "métrica": label, "valor": float(row[col])})
    dfm = pd.DataFrame(filas)
    fig = px.bar(
        dfm,
        x="escenario",
        y="valor",
        color="métrica",
        barmode="group",
        title="Comparativa de métricas clave",
        labels={"valor": "Valor"},
    )
    return fig


def main() -> None:
    st.set_page_config(page_title="Simulación de tráfico (SimPy)", layout="wide")
    st.title("Simulación de tráfico — Cra 27 con Calle 45 (Bucaramanga)")
    st.write(
        "Herramienta académica para ejecutar escenarios, ver el progreso de la simulación y analizar resultados "
        "con visualizaciones interactivas."
    )

    oficiales = escenarios_oficiales()
    mapa_oficiales = {e.nombre: e for e in oficiales}

    with st.sidebar:
        st.header("Configuración")
        duracion_s = st.number_input("Horizonte de simulación (s)", min_value=60, max_value=7200, value=3600, step=60)
        semilla = st.number_input("Semilla aleatoria", min_value=0, max_value=10_000_000, value=42, step=1)
        ui_refresh = st.slider("Actualizar progreso cada (s)", min_value=1, max_value=30, value=5, step=1)

        st.subheader("Escenarios a ejecutar")
        nombres_sel = st.multiselect(
            "Selecciona escenarios",
            options=list(mapa_oficiales.keys()),
            default=list(mapa_oficiales.keys()),
        )

        usar_personalizado = st.checkbox("Agregar escenario personalizado", value=False)
        escenario_personalizado = None
        if usar_personalizado:
            verde_cra27 = st.slider("Verde Cra 27 (s)", min_value=10, max_value=100, value=55, step=1)
            amarillo = st.slider("Amarillo (s)", min_value=3, max_value=10, value=5, step=1)
            ciclo = st.selectbox("Ciclo total (s)", options=[120], index=0)
            escenario_personalizado = Escenario(
                nombre=f"Personalizado (G={verde_cra27})",
                ciclo_s=int(ciclo),
                amarillo_s=int(amarillo),
                verde_cra27_s=int(verde_cra27),
            )

            try:
                escenario_personalizado.validar()
                st.caption(f"Verde Calle 45 calculado: {escenario_personalizado.verde_cl45_s}s")
            except Exception as exc:
                st.error(str(exc))

        ejecutar = st.button("Ejecutar simulación", type="primary")

    if not ejecutar:
        st.info("Configura los escenarios y pulsa 'Ejecutar simulación'.")
        st.stop()

    escenarios: list[Escenario] = [mapa_oficiales[n] for n in nombres_sel]
    if escenario_personalizado is not None:
        escenarios.append(escenario_personalizado)

    if not escenarios:
        st.warning("Selecciona al menos un escenario.")
        st.stop()

    progreso = st.progress(0)
    estado = st.empty()
    preview = st.empty()

    total_esc = len(escenarios)
    ultimo_refresh: dict[str, int] = {}

    def on_tick(nombre_esc: str, t: int, total: int, fila: dict[str, object]) -> None:
        ultimo = ultimo_refresh.get(nombre_esc, -1)
        if t != total and (t - ultimo) < ui_refresh:
            return
        ultimo_refresh[nombre_esc] = t

        idx = next((i for i, e in enumerate(escenarios) if e.nombre == nombre_esc), 0)
        avance = (idx * (total + 1) + t) / (total_esc * (total + 1))
        progreso.progress(int(avance * 100))

        estado.write(f"Ejecutando: {nombre_esc} — t={t}/{total}s")
        df_preview = pd.DataFrame([fila])
        preview.dataframe(df_preview, width="stretch", hide_index=True)

    with st.spinner("Ejecutando simulación..."):
        resultados = ejecutar_escenarios(
            escenarios=escenarios,
            duracion_s=int(duracion_s),
            semilla_base=int(semilla),
            on_tick=on_tick,
        )
    progreso.progress(100)

    resumen = _resumen_df(resultados)
    checks = _checks_df(resultados)

    st.subheader("Resumen por escenario")
    st.dataframe(resumen, width="stretch", hide_index=True)

    st.subheader("Informe de validación")
    st.dataframe(checks, width="stretch", hide_index=True)

    fig_comp = _plot_comparativa(resumen)
    if fig_comp is not None:
        st.plotly_chart(fig_comp, width="stretch")

    st.subheader("Visualizaciones por escenario")
    tabs = st.tabs([r.escenario.nombre for r in resultados])
    for tab, r in zip(tabs, resultados, strict=True):
        with tab:
            st.write("Parámetros del escenario")
            st.json(asdict(r.escenario))

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(_plot_colas(r), width="stretch")
            with col2:
                st.plotly_chart(_plot_espera_prom(r), width="stretch")

            fig_hist = _plot_hist_esperas(r)
            if fig_hist is not None:
                st.plotly_chart(fig_hist, width="stretch")

            st.write("Serie de tiempo (segundo a segundo)")
            st.dataframe(r.serie_tiempo, width="stretch", hide_index=True)

            st.write("Resumen estadístico de tiempos de espera (por vía)")
            df_veh = pd.concat([r.vehiculos_cra27, r.vehiculos_cl45], ignore_index=True)
            if not df_veh.empty:
                df_veh["via"] = df_veh["via"].replace({"CRA27": "Cra 27", "CL45": "Calle 45"})
                stats = df_veh.groupby("via")["espera_s"].describe(percentiles=[0.5, 0.9, 0.95]).reset_index()
                st.dataframe(stats, width="stretch", hide_index=True)
            else:
                st.info("No hay registros de vehículos para este escenario.")


if __name__ == "__main__":
    main()
