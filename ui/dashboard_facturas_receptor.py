from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from dropbox_integration.image_renamer import _find_jpg_images
from dropbox_integration.invoice_receptor_analytics import build_invoices_dataset, summarize_by_receptor


def _find_audit_snapshots(root: Path) -> list[Path]:
    versions = root / "docs" / "versions"
    if not versions.exists():
        return []
    return sorted(versions.glob("**/*search_audit*.json"), key=lambda p: p.stat().st_mtime)


def _load_registros_default(repo_root: Path) -> list[dict[str, object]]:
    path = repo_root / "docs" / "dropbox_asignacion_app.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [x for x in payload if isinstance(x, dict)]


def render_dashboard_facturas_receptor(
    carpeta_facturacion: Path,
    repo_root: Path,
    registros: list[dict[str, object]] | None = None,
) -> None:
    st.markdown("### Dashboard de facturas por receptor")

    registros_base = registros if isinstance(registros, list) else _load_registros_default(repo_root)

    snapshots = _find_audit_snapshots(repo_root)
    options = ["Sin filtro snapshot", *[p.name for p in snapshots]]
    snapshot_sel = st.selectbox("Filtrar por snapshot", options=options, index=0, key="receptor_snapshot_filter")
    snapshot_paths = {p.name: p for p in snapshots}

    rows = build_invoices_dataset(registros_base)
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("No hay facturas detectadas para dashboard de receptor.")
        return

    if snapshot_sel != "Sin filtro snapshot":
        try:
            payload = json.loads(snapshot_paths[snapshot_sel].read_text(encoding="utf-8"))
            rutas = {
                str(item.get("ruta", ""))
                for item in payload.get("resultados_scores", [])
                if isinstance(item, dict)
            }
            if rutas:
                df = df[df["ruta"].astype(str).isin(rutas)]
        except Exception:
            pass

    receptor_options = ["AG DISTRIBUIDORA", "MEDBRIGHT", "OTROS"]
    receptor_sel = st.selectbox("Receptor", receptor_options, index=0, key="receptor_bucket_selector")

    provider_options = sorted(df.get("proveedor_detectado", pd.Series(dtype=str)).astype(str).unique().tolist())
    provider_sel = st.selectbox("Proveedor", ["TODOS", *provider_options], index=0, key="receptor_provider_selector")

    df_filtered = df[df["receptor_bucket"].astype(str) == receptor_sel]
    if provider_sel != "TODOS":
        df_filtered = df_filtered[df_filtered["proveedor_detectado"].astype(str) == provider_sel]

    cols = [c for c in ["nombre_archivo", "fecha", "total", "rfc_emisor", "rfc_receptor", "uuid", "proveedor_detectado"] if c in df_filtered.columns]
    st.dataframe(df_filtered[cols], use_container_width=True, height=220)

    summary = summarize_by_receptor(rows)
    total_receptor = float(summary.get("totals", {}).get(receptor_sel, 0.0))
    count_receptor = int(summary.get("counts", {}).get(receptor_sel, 0))
    avg_receptor = (total_receptor / count_receptor) if count_receptor else 0.0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total facturado", f"${total_receptor:,.2f}")
    k2.metric("Número de facturas", f"{count_receptor:,}")
    k3.metric("Promedio por factura", f"${avg_receptor:,.2f}")

    totals_df = pd.DataFrame(
        [{"receptor": k, "total": v} for k, v in summary.get("totals", {}).items()]
    )
    counts_df = pd.DataFrame(
        [{"receptor": k, "count": v} for k, v in summary.get("counts", {}).items()]
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption("Total por receptor")
        if not totals_df.empty:
            st.vega_lite_chart(
                totals_df,
                {
                    "mark": {"type": "bar", "color": "#1565C0"},
                    "encoding": {
                        "x": {"field": "receptor", "type": "nominal"},
                        "y": {"field": "total", "type": "quantitative"},
                    },
                },
                use_container_width=True,
            )

    with c2:
        st.caption("Distribución de facturas")
        if not counts_df.empty:
            st.vega_lite_chart(
                counts_df,
                {
                    "mark": {"type": "arc", "innerRadius": 45},
                    "encoding": {
                        "theta": {"field": "count", "type": "quantitative"},
                        "color": {
                            "field": "receptor",
                            "type": "nominal",
                            "scale": {"range": ["#0D47A1", "#1565C0", "#1E88E5", "#42A5F5"]},
                        },
                    },
                },
                use_container_width=True,
            )

    with c3:
        st.caption("Evolución mensual por receptor")
        monthly_rows: list[dict[str, object]] = []
        for receptor, months in summary.get("monthly", {}).items():
            for month, total in months.items():
                monthly_rows.append({"receptor": receptor, "mes": month, "total": total})
        monthly_df = pd.DataFrame(monthly_rows)
        if not monthly_df.empty:
            st.vega_lite_chart(
                monthly_df,
                {
                    "mark": {"type": "line", "point": True, "color": "#1E88E5"},
                    "encoding": {
                        "x": {"field": "mes", "type": "nominal", "sort": None},
                        "y": {"field": "total", "type": "quantitative"},
                        "detail": {"field": "receptor"},
                    },
                },
                use_container_width=True,
            )

    st.caption("Imágenes asociadas (si existen)")
    images = _find_jpg_images(carpeta_facturacion / "Imagenes")
    image_rows = [
        {
            "ruta": str(img),
            "nombre": img.name,
            "carpeta": img.parent.name,
        }
        for img in images
        if receptor_sel.lower().replace(" ", "") in str(img).lower().replace(" ", "") or receptor_sel == "OTROS"
    ]
    if image_rows:
        st.dataframe(pd.DataFrame(image_rows), use_container_width=True, height=180)
    else:
        st.info("No hay imágenes asociadas visibles para el receptor/filtro actual.")
