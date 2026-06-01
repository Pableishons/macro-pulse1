# app.py
# Macro Pulse - Frontend del sistema de alertas de inversiones.
# Muestra series macro del BCCh, hechos esenciales CMF y análisis profundo con IA.

import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_cliente

# ============================================
# CONFIGURACIÓN
# ============================================
st.set_page_config(
    page_title="Macro Pulse",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS personalizado
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 3px solid #1f3864;
    }

    /* Estilo de la tarjeta de alerta */
    .alerta-card {
        background-color: #ffffff;
        border: 1px solid #e0e4e8;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 4px solid #1f3864;
    }

    .alerta-titulo {
        font-size: 16px;
        font-weight: 600;
        color: #1f3864;
        margin: 0 0 6px 0;
    }

    .alerta-meta {
        font-size: 12px;
        color: #6c757d;
        margin-bottom: 10px;
    }

    .badge-alta {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
    }

    .badge-media {
        background-color: #fef3c7;
        color: #92400e;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
    }

    .badge-ipsa {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
        margin-left: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# CARGA DE DATOS
# ============================================

@st.cache_data(ttl=60)
def cargar_series_bcch():
    db = get_cliente()
    respuesta = db.table("series_bcch") \
        .select("*") \
        .order("fecha", desc=True) \
        .execute()
    return pd.DataFrame(respuesta.data)


@st.cache_data(ttl=60)
def cargar_hechos_esenciales():
    db = get_cliente()
    respuesta = db.table("hechos_esenciales") \
        .select("*") \
        .order("creado_en", desc=True) \
        .limit(100) \
        .execute()
    return pd.DataFrame(respuesta.data)


@st.cache_data(ttl=60)
def cargar_alertas_con_analisis():
    """Trae solo los hechos con análisis profundo, ordenados por relevancia."""
    db = get_cliente()
    respuesta = db.table("hechos_esenciales") \
        .select("*") \
        .not_.is_("analisis_completo", "null") \
        .order("creado_en", desc=True) \
        .limit(20) \
        .execute()
    return pd.DataFrame(respuesta.data)


# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("### Filtros")

    relevancia_filtro = st.multiselect(
        "Relevancia",
        options=["alta", "media", "baja"],
        default=["alta", "media"],
    )

    solo_ipsa = st.checkbox("Solo empresas IPSA", value=False)

    st.markdown("---")
    st.markdown("### Sobre Macro Pulse")
    st.caption(
        "Sistema personal de alertas de inversiones para el mercado chileno. "
        "Fuentes: BCCh + CMF. Análisis con IA (Gemini)."
    )

    if st.button("🔄 Actualizar datos"):
        st.cache_data.clear()
        st.rerun()


# ============================================
# HEADER
# ============================================
col_title, col_time = st.columns([3, 1])
with col_title:
    st.title("📊 Macro Pulse")
    st.caption("Inteligencia de mercado · Chile")
with col_time:
    st.markdown(
        f"<div style='text-align: right; padding-top: 20px;'>"
        f"<small style='color: gray;'>Actualizado<br>"
        f"<strong>{datetime.now().strftime('%d %b · %H:%M')}</strong></small>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.divider()


# ============================================
# CARGAR DATOS
# ============================================
df_series = cargar_series_bcch()
df_hechos = cargar_hechos_esenciales()
df_alertas = cargar_alertas_con_analisis()


# ============================================
# TABS
# ============================================
tab_alertas, tab_macro, tab_hechos = st.tabs([
    "🚨 Alertas",
    "📈 Indicadores macro",
    "📰 Hechos esenciales",
])


# --- TAB 1: ALERTAS (análisis profundo) ---
with tab_alertas:
    if df_alertas.empty:
        st.info(
            "Aún no hay alertas con análisis profundo. Corre `analisis_profundo.py` primero.")
    else:
        st.caption(
            f"Mostrando {len(df_alertas)} alertas con análisis IA completo.")

        for _, alerta in df_alertas.iterrows():
            analisis = alerta["analisis_completo"]

            if not analisis or "error" in analisis:
                continue

            relevancia = alerta.get("relevancia", "media")
            es_ipsa = alerta.get("es_ipsa", False)

            # Badge HTML según relevancia
            badge_rel = f'<span class="badge-{relevancia}">{relevancia.upper()}</span>'
            badge_ipsa = '<span class="badge-ipsa">IPSA</span>' if es_ipsa else ""

            titular = analisis.get("titular", alerta["empresa"])

            # Header de la alerta
            st.markdown(
                f"""<div class="alerta-card">
                <div>{badge_rel}{badge_ipsa}
                <span style="font-size: 11px; color: #6c757d; margin-left: 8px;">
                {alerta['fecha']} · {alerta['empresa']}</span></div>
                <p class="alerta-titulo">{titular}</p>
                </div>""",
                unsafe_allow_html=True,
            )

            # Detalles expandibles
            with st.expander("Ver análisis completo"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(
                        f"**Urgencia:** {analisis.get('urgencia', '—')}")
                with col2:
                    st.markdown(
                        f"**Magnitud:** {analisis.get('magnitud_esperada', '—')}")
                with col3:
                    st.markdown(
                        f"**Ventana:** {analisis.get('ventana_critica', '—')}")

                vi = analisis.get("version_interna", {})

                st.markdown("**📊 Resumen**")
                st.markdown(vi.get("resumen", "—"))

                st.markdown("**💡 Interpretación**")
                st.markdown(vi.get("interpretacion", "—"))

                accion = vi.get("accion_corredora", {})
                if accion:
                    st.markdown("**🎯 Acción comercial**")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("*Cliente con el papel:*")
                        st.markdown(accion.get("tiene_el_papel", "—"))
                    with col_b:
                        st.markdown("*Cliente sin el papel:*")
                        st.markdown(accion.get("no_tiene_el_papel", "—"))

                if vi.get("oportunidad_adicional"):
                    st.markdown("**✨ Oportunidad adicional**")
                    st.markdown(vi["oportunidad_adicional"])

                if vi.get("riesgos"):
                    st.markdown("**⚠️ Riesgos**")
                    st.markdown(vi["riesgos"])

                st.markdown("**📱 Forwardeable**")
                st.code(analisis.get("version_forwardeable", "—"), language=None)

                if analisis.get("tags"):
                    tags_str = " · ".join(f"`{t}`" for t in analisis["tags"])
                    st.caption(f"🏷️ {tags_str}")


# --- TAB 2: MACRO ---
with tab_macro:
    if df_series.empty:
        st.warning("No hay datos de series económicas todavía.")
    else:
        series_unicas = df_series["codigo"].unique()
        cols = st.columns(len(series_unicas))

        for i, codigo in enumerate(series_unicas):
            df_serie = df_series[df_series["codigo"] == codigo].sort_values(
                "fecha", ascending=False
            )

            if len(df_serie) < 2:
                continue

            actual = df_serie.iloc[0]
            anterior = df_serie.iloc[1]
            var_abs = actual["valor"] - anterior["valor"]

            if actual["tipo"] == "tasa":
                var_str = f"{var_abs * 100:+.0f} pb"
            else:
                if anterior["valor"] != 0:
                    var_pct = (var_abs / anterior["valor"]) * 100
                    var_str = f"{var_pct:+.2f}%"
                else:
                    var_str = "—"

            if actual["unidad"] == "%":
                valor_str = f"{actual['valor']:.2f}%"
            else:
                valor_str = f"{actual['valor']:,.2f}"

            nombre_corto = actual["nombre"].split("(")[0].strip()
            if len(nombre_corto) > 25:
                nombre_corto = nombre_corto[:23] + "..."

            with cols[i]:
                st.metric(
                    label=nombre_corto,
                    value=valor_str,
                    delta=var_str,
                )

        st.divider()
        st.subheader("Historial reciente")
        df_display = df_series[["nombre", "fecha", "valor", "unidad"]].head(20)
        df_display.columns = ["Indicador", "Fecha", "Valor", "Unidad"]
        st.dataframe(df_display, hide_index=True, use_container_width=True)


# --- TAB 3: HECHOS ESENCIALES ---
with tab_hechos:
    if df_hechos.empty:
        st.warning("No hay hechos esenciales en la base de datos todavía.")
    else:
        df_filtrado = df_hechos.copy()
        df_filtrado["relevancia"] = df_filtrado["relevancia"].fillna(
            "sin clasificar")
        df_filtrado = df_filtrado[df_filtrado["relevancia"].isin(
            relevancia_filtro)]

        if solo_ipsa and "es_ipsa" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["es_ipsa"] == True]

        col1, col2, col3 = st.columns(3)
        with col1:
            n_alta = len(df_filtrado[df_filtrado["relevancia"] == "alta"])
            st.metric("🔴 Alta relevancia", n_alta)
        with col2:
            n_media = len(df_filtrado[df_filtrado["relevancia"] == "media"])
            st.metric("🟡 Media relevancia", n_media)
        with col3:
            n_total = len(df_filtrado)
            st.metric("Total mostrados", n_total)

        st.divider()

        st.dataframe(
            df_filtrado[["fecha", "empresa",
                         "materia", "relevancia", "analizado"]],
            column_config={
                "fecha": st.column_config.TextColumn("Fecha", width="medium"),
                "empresa": st.column_config.TextColumn("Empresa", width="large"),
                "materia": st.column_config.TextColumn("Materia", width="large"),
                "relevancia": st.column_config.TextColumn("Relevancia", width="small"),
                "analizado": st.column_config.CheckboxColumn("IA", width="small"),
            },
            hide_index=True,
            use_container_width=True,
            height=500,
        )


# ============================================
# FOOTER
# ============================================
st.divider()
st.caption(
    f"Macro Pulse v0.2 · Datos: BCCh + CMF · Análisis IA: Gemini 2.5 · "
    f"Sistema personal de Pablo · {datetime.now().year}"
)
