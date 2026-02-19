from __future__ import annotations

import csv
import json
import logging
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .ai_classifier import buscar_similares
from .content_extractor import extraer_texto_archivo

try:
    from .tagging_engine import asignar_etiquetas_automaticas
except Exception:
    asignar_etiquetas_automaticas = None

try:
    from rapidfuzz import fuzz  # type: ignore
except Exception:
    fuzz = None

logger = logging.getLogger(__name__)

TOKEN_REGEX = re.compile(r"\w+", re.UNICODE)
STRICT_MODE = "estricta"
FLEX_MODE = "flexible"
SEARCH_ENGINE_VERSION = "2.2.0"


@dataclass(frozen=True)
class SearchWeights:
    """Pesos base del ranking híbrido avanzado."""

    exacto: float = 0.25
    fuzzy: float = 0.16
    tfidf: float = 0.26
    contenido: float = 0.12
    tokens: float = 0.10
    temporal: float = 0.06
    estructural: float = 0.05


@dataclass
class DocumentoIndexado:
    """Representación indexada de un documento con metadatos de búsqueda."""

    nombre: str
    ruta: str
    extension: str
    carpeta: str
    tipo: str
    etiquetas: list[str]
    tamano: int
    fecha_modificacion: str
    contenido: str
    hash: str
    proveedor_virtual: str = "SIN_PROVEEDOR"
    hospital_virtual: str = "SIN_HOSPITAL"
    mes_virtual: str = "SIN_MES"
    anio_virtual: str = "SIN_AÑO"
    carpeta_virtual: str = ""
    score: float = 0.0


@dataclass
class QueryContext:
    """Contexto preprocesado de una consulta para ranking y auditoría."""

    query_raw: str
    query_norm: str
    query_tokens: list[str]
    filtros: dict[str, object]
    modo: str
    usar_fuzzy: bool
    usar_nombre: bool
    usar_contenido: bool
    usar_semantico: bool
    weights: SearchWeights
    boost_weights: dict[str, float]
    include_debug: bool = False
    profiling: bool = False
    idf_query_factor: float = 1.0
    audit_id: str = ""
    started_at: float = field(default_factory=perf_counter)


class SearchEngine:
    """Motor de búsqueda documental híbrido y extensible para Dropbox IA."""

    def __init__(self, documentos: list[dict[str, object]]) -> None:
        self.documentos = documentos or []
        self.index: list[DocumentoIndexado] = []
        self._tfidf: TfidfVectorizer | None = None
        self._matriz_tfidf: Any = None
        self._idf_map: dict[str, float] = {}
        self._doc_tokens: dict[str, set[str]] = {}
        self._doc_name_norm: dict[str, str] = {}
        self._doc_content_norm: dict[str, str] = {}
        self._doc_struct_tokens: dict[str, set[str]] = {}
        self._doc_date: dict[str, datetime] = {}
        self._field_freq: dict[str, Counter[str]] = {
            "proveedor": Counter(),
            "hospital": Counter(),
            "mes": Counter(),
            "anio": Counter(),
            "tipo": Counter(),
        }
        self.audit_log: list[dict[str, object]] = []
        self._last_query_context: dict[str, object] = {}
        self._last_audited_results: list[dict[str, object]] = []
        self._last_performance_metrics: dict[str, object] = {}

    @staticmethod
    def _normalizar_texto(valor: Any) -> str:
        return str(valor or "").strip().lower()

    @staticmethod
    def _tokenizar(texto: str) -> list[str]:
        return [m.group(0).lower() for m in TOKEN_REGEX.finditer(texto or "")]

    @staticmethod
    def _to_int(valor: Any) -> int:
        try:
            return int(valor)
        except Exception:
            return 0

    @staticmethod
    def _to_float(valor: Any) -> float:
        try:
            return float(valor)
        except Exception:
            return 0.0

    @staticmethod
    def _parse_fecha(valor: str) -> datetime | None:
        if not valor:
            return None
        try:
            dt = datetime.fromisoformat(valor.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    @staticmethod
    def _norm_or_default(valor: Any, default: str) -> str:
        out = str(valor or "").strip()
        return out if out else default

    @staticmethod
    def _normalize_mode(valor: Any) -> str:
        raw = str(valor or "").strip().lower()
        if raw in {"estricto", "estricta", "strict", STRICT_MODE}:
            return STRICT_MODE
        return FLEX_MODE

    @staticmethod
    def _safe_ratio(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        if fuzz is None:
            return 1.0 if a == b else 0.0
        try:
            return float(fuzz.ratio(a, b)) / 100.0
        except Exception:
            return 0.0

    @staticmethod
    def _semantic_vector(doc: DocumentoIndexado) -> str:
        return f"{doc.nombre} {' '.join(doc.etiquetas)} {doc.tipo} {doc.proveedor_virtual} {doc.hospital_virtual} {doc.mes_virtual} {doc.anio_virtual} {doc.contenido}".strip()

    def _resultado(self, doc: DocumentoIndexado, score: float) -> dict[str, object]:
        out = asdict(doc)
        out["fecha"] = doc.fecha_modificacion
        out["relevancia"] = round(float(max(0.0, score)), 4)
        out["id"] = doc.hash or doc.ruta
        return out

    def _invalidate_semantic_cache(self) -> None:
        self._tfidf = None
        self._matriz_tfidf = None
        self._idf_map = {}

    def _compute_dynamic_tfidf_config(self) -> dict[str, object]:
        corpus_size = len(self.index)
        if corpus_size <= 5:
            max_df = 1.0
            min_df = 1
            max_features = 1200
        elif corpus_size <= 80:
            max_df = 0.96
            min_df = 1
            max_features = 3000
        elif corpus_size <= 2000:
            max_df = 0.92
            min_df = 2
            max_features = 5000
        else:
            max_df = 0.88
            min_df = 3
            max_features = 10000
        return {
            "max_features": max_features,
            "ngram_range": (1, 2),
            "max_df": max_df,
            "min_df": min_df,
            "sublinear_tf": True,
        }

    def _refresh_field_frequencies(self) -> None:
        for counter in self._field_freq.values():
            counter.clear()
        for doc in self.index:
            self._field_freq["proveedor"][self._normalizar_texto(doc.proveedor_virtual)] += 1
            self._field_freq["hospital"][self._normalizar_texto(doc.hospital_virtual)] += 1
            self._field_freq["mes"][self._normalizar_texto(doc.mes_virtual)] += 1
            self._field_freq["anio"][self._normalizar_texto(doc.anio_virtual)] += 1
            self._field_freq["tipo"][self._normalizar_texto(doc.tipo)] += 1

    def _build_document_cache(self, doc: DocumentoIndexado) -> None:
        doc_id = doc.hash or doc.ruta
        name_norm = self._normalizar_texto(doc.nombre)
        content_norm = self._normalizar_texto(doc.contenido)
        tokens = set(self._tokenizar(f"{doc.nombre} {' '.join(doc.etiquetas)} {doc.contenido}"))
        struct_tokens = set(
            self._tokenizar(
                " ".join(
                    [
                        doc.carpeta,
                        doc.carpeta_virtual,
                        doc.proveedor_virtual,
                        doc.hospital_virtual,
                        doc.mes_virtual,
                        doc.anio_virtual,
                        doc.ruta,
                    ]
                )
            )
        )
        self._doc_name_norm[doc_id] = name_norm
        self._doc_content_norm[doc_id] = content_norm
        self._doc_tokens[doc_id] = tokens
        self._doc_struct_tokens[doc_id] = struct_tokens
        fecha_dt = self._parse_fecha(doc.fecha_modificacion)
        if fecha_dt is not None:
            self._doc_date[doc_id] = fecha_dt

    def _extraer_etiquetas(self, raw: dict[str, object]) -> list[str]:
        etiquetas_raw = raw.get("etiquetas", [])
        etiquetas = [str(x).lower() for x in etiquetas_raw] if isinstance(etiquetas_raw, list) else []
        if etiquetas:
            return etiquetas
        if asignar_etiquetas_automaticas is None:
            return []
        try:
            auto = asignar_etiquetas_automaticas([dict(raw)])
            if auto and isinstance(auto[0].get("etiquetas"), list):
                return [str(x).lower() for x in auto[0].get("etiquetas", [])]
        except Exception:
            logger.debug("No se pudieron asignar etiquetas automáticas para %s", raw.get("ruta_completa", ""), exc_info=True)
        return []

    def _build_document(self, raw: dict[str, object], i: int) -> DocumentoIndexado:
        ruta = str(raw.get("ruta_completa", "")).strip()
        path = Path(ruta) if ruta else None
        contenido = str(raw.get("contenido_extraido", "") or "").strip()
        if not contenido and path and path.exists():
            try:
                contenido = extraer_texto_archivo(path)
            except Exception:
                logger.warning("Extracción fallida para %s", ruta, exc_info=True)
        extension = self._normalizar_texto(raw.get("extension", ""))
        if extension and not extension.startswith("."):
            extension = f".{extension}"
        return DocumentoIndexado(
            nombre=str(raw.get("nombre_archivo", "")),
            ruta=ruta,
            extension=extension,
            carpeta=str(raw.get("carpeta", "")),
            tipo=self._norm_or_default(raw.get("categoria", "Sin clasificar"), "Sin clasificar"),
            etiquetas=self._extraer_etiquetas(raw),
            tamano=self._to_int(raw.get("tamaño", 0) or 0),
            fecha_modificacion=str(raw.get("fecha_modificacion", "")),
            contenido=contenido,
            hash=str(raw.get("hash") or raw.get("sha256") or ruta or i),
            proveedor_virtual=self._norm_or_default(raw.get("proveedor_virtual", "SIN_PROVEEDOR"), "SIN_PROVEEDOR"),
            hospital_virtual=self._norm_or_default(raw.get("hospital_virtual", "SIN_HOSPITAL"), "SIN_HOSPITAL"),
            mes_virtual=self._norm_or_default(raw.get("mes_virtual", "SIN_MES"), "SIN_MES"),
            anio_virtual=self._norm_or_default(raw.get("anio_virtual", "SIN_AÑO"), "SIN_AÑO"),
            carpeta_virtual=self._norm_or_default(raw.get("carpeta_virtual", ""), ""),
            score=0.0,
        )

    def _log_audit(self, evento: dict[str, object]) -> None:
        self.audit_log.append(evento)
        if len(self.audit_log) > 2000:
            self.audit_log = self.audit_log[-2000:]

    def _ctx_to_dict(self, ctx: QueryContext) -> dict[str, object]:
        return {
            "query_raw": ctx.query_raw,
            "query_norm": ctx.query_norm,
            "query_tokens": list(ctx.query_tokens),
            "filtros": dict(ctx.filtros),
            "modo": ctx.modo,
            "usar_fuzzy": ctx.usar_fuzzy,
            "usar_nombre": ctx.usar_nombre,
            "usar_contenido": ctx.usar_contenido,
            "usar_semantico": ctx.usar_semantico,
            "weights": asdict(ctx.weights),
            "boost_weights": dict(ctx.boost_weights),
            "idf_query_factor": float(ctx.idf_query_factor),
            "audit_id": ctx.audit_id,
            "include_debug": ctx.include_debug,
            "profiling": ctx.profiling,
        }

    def _score_summary(self, resultados: list[dict[str, object]]) -> dict[str, float]:
        if not resultados:
            return {
                "score_final_avg": 0.0,
                "score_final_max": 0.0,
                "score_final_min": 0.0,
                "score_boosting_avg": 0.0,
            }
        finals = [self._to_float(r.get("score_final", r.get("relevancia", 0.0))) for r in resultados]
        boosts = [self._to_float(r.get("score_boosting", 0.0)) for r in resultados]
        return {
            "score_final_avg": round(float(np.mean(finals)), 6),
            "score_final_max": round(float(np.max(finals)), 6),
            "score_final_min": round(float(np.min(finals)), 6),
            "score_boosting_avg": round(float(np.mean(boosts)), 6),
        }

    def _build_auditoria_payload(self) -> dict[str, object]:
        """Construye payload completo de auditoría para exportación offline."""
        generated_at = datetime.now(timezone.utc).isoformat()
        resultados = list(self._last_audited_results)
        payload: dict[str, object] = {
            "metadata": {
                "engine_version": SEARCH_ENGINE_VERSION,
                "generated_at": generated_at,
                "indexed_documents": len(self.index),
                "audit_events": len(self.audit_log),
                "result_rows": len(resultados),
            },
            "query_context": dict(self._last_query_context),
            "audit_log": list(self.audit_log),
            "resultados_scores": resultados,
            "resumen_scores": self._score_summary(resultados),
        }
        if self._last_performance_metrics:
            payload["performance_metrics"] = dict(self._last_performance_metrics)
        return payload

    def export_auditoria_json(self, path: str) -> Path:
        """Exporta auditoría avanzada del buscador en formato JSON."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self._build_auditoria_payload()
        try:
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as error:
            logger.error("Error exportando auditoría JSON a %s", target, exc_info=True)
            raise RuntimeError(f"No se pudo exportar auditoría JSON: {error}") from error
        return target

    def export_auditoria_csv(self, path: str) -> Path:
        """Exporta auditoría avanzada del buscador en formato CSV."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        columnas = [
            "ruta",
            "score_exacto",
            "score_fuzzy",
            "score_semantico",
            "score_tokens",
            "score_temporal",
            "score_estructural",
            "score_boosting",
            "score_final",
        ]
        try:
            with target.open("w", newline="", encoding="utf-8") as handler:
                writer = csv.DictWriter(handler, fieldnames=columnas)
                writer.writeheader()
                for row in self._last_audited_results:
                    writer.writerow(
                        {
                            "ruta": str(row.get("ruta", "")),
                            "score_exacto": self._to_float(row.get("score_exacto", 0.0)),
                            "score_fuzzy": self._to_float(row.get("score_fuzzy", 0.0)),
                            "score_semantico": self._to_float(row.get("score_semantico", 0.0)),
                            "score_tokens": self._to_float(row.get("score_tokens", 0.0)),
                            "score_temporal": self._to_float(row.get("score_temporal", 0.0)),
                            "score_estructural": self._to_float(row.get("score_estructural", 0.0)),
                            "score_boosting": self._to_float(row.get("score_boosting", 0.0)),
                            "score_final": self._to_float(row.get("score_final", row.get("relevancia", 0.0))),
                        }
                    )
        except Exception as error:
            logger.error("Error exportando auditoría CSV a %s", target, exc_info=True)
            raise RuntimeError(f"No se pudo exportar auditoría CSV: {error}") from error
        return target

    def export_performance_json(self, path: str) -> Path:
        """Exporta métricas de performance de la última búsqueda perfilada."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(self._last_performance_metrics)
        try:
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as error:
            logger.error("Error exportando performance JSON a %s", target, exc_info=True)
            raise RuntimeError(f"No se pudo exportar performance JSON: {error}") from error
        return target

    def export_performance_csv(self, path: str) -> Path:
        """Exporta métricas de performance de la última búsqueda perfilada en formato tabular."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        perf = dict(self._last_performance_metrics)
        components = perf.get("components", {}) if isinstance(perf.get("components", {}), dict) else {}
        try:
            with target.open("w", newline="", encoding="utf-8") as handler:
                writer = csv.DictWriter(handler, fieldnames=["component", "time_ms"])
                writer.writeheader()
                for key, value in components.items():
                    writer.writerow({"component": key, "time_ms": self._to_float(value)})
        except Exception as error:
            logger.error("Error exportando performance CSV a %s", target, exc_info=True)
            raise RuntimeError(f"No se pudo exportar performance CSV: {error}") from error
        return target

    def _idf_factor_query(self, query_tokens: list[str]) -> float:
        if not query_tokens or not self._idf_map:
            return 1.0
        values = [self._idf_map.get(tok, 0.0) for tok in query_tokens]
        valid = [v for v in values if v > 0]
        if not valid:
            return 0.95
        median_idf = float(np.median(valid))
        max_idf = max(self._idf_map.values()) if self._idf_map else 1.0
        if max_idf <= 0:
            return 1.0
        rarity = median_idf / max_idf
        return max(0.82, min(1.20, 0.9 + rarity * 0.3))

    @staticmethod
    def _clamp(valor: float, minimo: float, maximo: float) -> float:
        return max(minimo, min(maximo, valor))

    def _weight_value(self, values: dict[str, object], key: str, default: float, minimo: float = 0.0, maximo: float = 3.0) -> float:
        raw = values.get(key, default)
        try:
            return self._clamp(float(raw), minimo, maximo)
        except Exception:
            return default

    def _build_custom_weights(self, values: dict[str, object], base: SearchWeights) -> SearchWeights:
        exacto = self._weight_value(values, "score_exacto", base.exacto)
        fuzzy = self._weight_value(values, "score_fuzzy", base.fuzzy)
        tfidf = self._weight_value(values, "score_semantico", base.tfidf)
        contenido = self._weight_value(values, "score_contenido", base.contenido)
        tokens = self._weight_value(values, "score_tokens", base.tokens)
        temporal = self._weight_value(values, "score_temporal", base.temporal)
        estructural = self._weight_value(values, "score_estructural", base.estructural)

        if all(v == 0 for v in [exacto, fuzzy, tfidf, contenido, tokens, temporal, estructural]):
            return base

        total = exacto + fuzzy + tfidf + contenido + tokens + temporal + estructural
        if total <= 0:
            return base
        return SearchWeights(
            exacto=exacto / total,
            fuzzy=fuzzy / total,
            tfidf=tfidf / total,
            contenido=contenido / total,
            tokens=tokens / total,
            temporal=temporal / total,
            estructural=estructural / total,
        )

    def _build_query_context(
        self,
        query: str,
        filtros: dict[str, object],
        usar_nombre: bool,
        usar_contenido: bool,
        usar_semantico: bool,
        modo: str | None,
        weights: dict[str, object] | None = None,
        auditoria: bool = False,
        profiling: bool = False,
    ) -> QueryContext:
        mode = self._normalize_mode(modo or filtros.get("modo", FLEX_MODE))
        query_norm = self._normalizar_texto(query)
        query_tokens = self._tokenizar(query_norm)
        base_weights = SearchWeights()
        if len(self.index) <= 60:
            base_weights = SearchWeights(exacto=0.24, fuzzy=0.16, tfidf=0.30, contenido=0.12, tokens=0.10, temporal=0.05, estructural=0.03)
        elif len(self.index) > 3000:
            base_weights = SearchWeights(exacto=0.27, fuzzy=0.14, tfidf=0.23, contenido=0.12, tokens=0.12, temporal=0.07, estructural=0.05)

        custom_values = weights or {}
        custom_weights = self._build_custom_weights(custom_values, base_weights)
        boost_weights = {
            "proveedor": self._weight_value(custom_values, "boost_proveedor", 1.0),
            "hospital": self._weight_value(custom_values, "boost_hospital", 1.0),
            "mes": self._weight_value(custom_values, "boost_mes", 1.0),
            "anio": self._weight_value(custom_values, "boost_anio", 1.0),
            "tipo": self._weight_value(custom_values, "boost_tipo", 1.0),
            "temporal": self._weight_value(custom_values, "boost_temporal", 1.0),
        }

        ctx = QueryContext(
            query_raw=query,
            query_norm=query_norm,
            query_tokens=query_tokens,
            filtros=filtros,
            modo=mode,
            usar_fuzzy=bool(filtros.get("fuzzy", True)),
            usar_nombre=usar_nombre,
            usar_contenido=usar_contenido,
            usar_semantico=usar_semantico or bool(filtros.get("semantico", False)),
            weights=custom_weights,
            boost_weights=boost_weights,
            include_debug=auditoria,
            profiling=profiling,
            audit_id=f"search-{datetime.now(timezone.utc).isoformat()}",
        )
        ctx.idf_query_factor = self._idf_factor_query(ctx.query_tokens)
        return ctx

    def _filtro_activo(self, value: object) -> bool:
        text = str(value or "").strip()
        return bool(text and text.upper() != "TODOS")

    def _doc_field(self, doc: DocumentoIndexado, key: str) -> str:
        mapping = {
            "tipo": doc.tipo,
            "extension": doc.extension,
            "carpeta": doc.carpeta,
            "proveedor": doc.proveedor_virtual,
            "proveedor_virtual": doc.proveedor_virtual,
            "hospital": doc.hospital_virtual,
            "hospital_virtual": doc.hospital_virtual,
            "mes": doc.mes_virtual,
            "mes_virtual": doc.mes_virtual,
            "anio": doc.anio_virtual,
            "año": doc.anio_virtual,
            "anio_virtual": doc.anio_virtual,
            "carpeta_virtual": doc.carpeta_virtual,
        }
        return str(mapping.get(key, ""))

    def _matches_filters(self, doc: DocumentoIndexado, filtros: dict[str, object]) -> bool:
        simple_filters = [
            "tipo",
            "extension",
            "carpeta",
            "proveedor",
            "proveedor_virtual",
            "hospital",
            "hospital_virtual",
            "mes",
            "mes_virtual",
            "anio",
            "año",
            "anio_virtual",
            "carpeta_virtual",
        ]
        for key in simple_filters:
            if key not in filtros:
                continue
            value = filtros.get(key)
            if not self._filtro_activo(value):
                continue
            if self._normalizar_texto(self._doc_field(doc, key)) != self._normalizar_texto(value):
                return False

        etiquetas_filtro = filtros.get("etiquetas", [])
        if isinstance(etiquetas_filtro, list) and etiquetas_filtro:
            etiquetas = {self._normalizar_texto(x) for x in doc.etiquetas}
            for tag in [self._normalizar_texto(x) for x in etiquetas_filtro if self._normalizar_texto(x)]:
                if tag not in etiquetas:
                    return False
        return True

    def _filter_candidates(self, filtros: dict[str, object]) -> list[DocumentoIndexado]:
        if not filtros:
            return list(self.index)
        return [doc for doc in self.index if self._matches_filters(doc, filtros)]

    def _score_exact(self, doc: DocumentoIndexado, query_norm: str) -> float:
        if not query_norm:
            return 0.0
        doc_id = doc.hash or doc.ruta
        nombre = self._doc_name_norm.get(doc_id, self._normalizar_texto(doc.nombre))
        if nombre == query_norm:
            return 1.0
        if query_norm in nombre:
            return 0.85
        return 0.0

    def _score_tokens(self, doc: DocumentoIndexado, query_tokens: list[str]) -> float:
        if not query_tokens:
            return 0.0
        doc_id = doc.hash or doc.ruta
        tokens = self._doc_tokens.get(doc_id, set())
        if not tokens:
            return 0.0
        shared = sum(1 for token in query_tokens if token in tokens)
        return shared / max(1, len(set(query_tokens)))

    def _score_content(self, doc: DocumentoIndexado, query_norm: str, query_tokens: list[str]) -> float:
        if not query_norm:
            return 0.0
        doc_id = doc.hash or doc.ruta
        contenido = self._doc_content_norm.get(doc_id, self._normalizar_texto(doc.contenido))
        if not contenido:
            return 0.0
        ocurrencias = sum(contenido.count(token) for token in query_tokens) if query_tokens else 0
        base = 0.35 if query_norm in contenido else 0.0
        return min(1.0, base + min(0.65, ocurrencias * 0.06))

    def _score_temporal(self, doc: DocumentoIndexado, query_tokens: list[str]) -> float:
        doc_id = doc.hash or doc.ruta
        fecha = self._doc_date.get(doc_id)
        if fecha is None:
            return 0.0
        now = datetime.now(timezone.utc)
        days = max(0.0, (now - fecha).total_seconds() / 86400.0)
        recency = math.exp(-days / 180.0)

        match_temporal = 0.0
        year = self._normalizar_texto(doc.anio_virtual)
        month = self._normalizar_texto(doc.mes_virtual)
        if year and year in query_tokens:
            match_temporal += 0.25
        if month:
            month_parts = set(self._tokenizar(month))
            if month_parts.intersection(query_tokens):
                match_temporal += 0.15
        return min(1.0, recency + match_temporal)

    def _score_structural(self, doc: DocumentoIndexado, query_tokens: list[str], filtros: dict[str, object]) -> float:
        if not query_tokens and not filtros:
            return 0.0
        doc_id = doc.hash or doc.ruta
        doc_struct = self._doc_struct_tokens.get(doc_id, set())
        query_struct_tokens = set(query_tokens)
        for key in ("proveedor", "hospital", "mes", "anio", "año", "carpeta_virtual", "carpeta", "tipo"):
            value = filtros.get(key)
            if self._filtro_activo(value):
                query_struct_tokens.update(self._tokenizar(str(value)))
        if not doc_struct or not query_struct_tokens:
            return 0.0
        inter = len(doc_struct.intersection(query_struct_tokens))
        union = len(doc_struct.union(query_struct_tokens))
        if union == 0:
            return 0.0
        return inter / union

    def _boost_contextual(
        self,
        doc: DocumentoIndexado,
        query_tokens: list[str],
        filtros: dict[str, object],
        boost_weights: dict[str, float] | None = None,
        temporal_score: float = 0.0,
    ) -> float:
        score = 1.0
        boost_weights = boost_weights or {}

        field_pairs = [
            ("proveedor", doc.proveedor_virtual, self._field_freq["proveedor"]),
            ("hospital", doc.hospital_virtual, self._field_freq["hospital"]),
            ("mes", doc.mes_virtual, self._field_freq["mes"]),
            ("anio", doc.anio_virtual, self._field_freq["anio"]),
            ("tipo", doc.tipo, self._field_freq["tipo"]),
        ]

        for key, raw_value, freq_map in field_pairs:
            value = self._normalizar_texto(raw_value)
            if not value:
                continue
            multiplier = self._clamp(boost_weights.get(key, 1.0), 0.0, 3.0)
            if multiplier == 0:
                continue

            filtro_val = filtros.get(key, filtros.get(f"{key}_virtual", ""))
            if self._filtro_activo(filtro_val) and self._normalizar_texto(filtro_val) == value:
                score += 0.14 * multiplier

            token_set = set(self._tokenizar(value))
            if token_set and token_set.intersection(query_tokens):
                score += 0.08 * multiplier

            freq = float(freq_map.get(value, 0))
            if freq > 0:
                score += min(0.06 * multiplier, 1.0 / math.sqrt(freq + 1.0) * 0.08 * multiplier)

        temporal_multiplier = self._clamp(boost_weights.get("temporal", 1.0), 0.0, 3.0)
        if temporal_multiplier > 0:
            score += min(0.12 * temporal_multiplier, temporal_score * 0.10 * temporal_multiplier)

        return max(0.8, min(1.65, score))

    def _semantic_scores(self, query: str) -> dict[str, float]:
        if not query.strip() or not self.index:
            return {}
        if self._tfidf is None or self._matriz_tfidf is None:
            self.construir_modelo_semantico()
        if self._tfidf is None or self._matriz_tfidf is None:
            return {}

        qv = self._tfidf.transform([query])
        sims = cosine_similarity(qv, self._matriz_tfidf).flatten()
        score_map: dict[str, float] = {}
        for i, score in enumerate(sims.tolist()):
            if i < len(self.index):
                score_map[self.index[i].hash] = max(0.0, float(score))
        return score_map

    def _rank_document(self, doc: DocumentoIndexado, ctx: QueryContext, semantic_scores: dict[str, float]) -> tuple[float, dict[str, float], dict[str, float]]:
        doc_id = doc.hash or doc.ruta
        component_ms = {
            "fuzzy_ms": 0.0,
            "semantic_ms": 0.0,
            "tokens_ms": 0.0,
            "temporal_ms": 0.0,
            "structural_ms": 0.0,
            "boosting_ms": 0.0,
        }

        exact_score = self._score_exact(doc, ctx.query_norm) if ctx.usar_nombre else 0.0

        t = perf_counter()
        fuzzy_score = self._safe_ratio(ctx.query_norm, self._doc_name_norm.get(doc_id, "")) if (ctx.usar_fuzzy and ctx.usar_nombre) else 0.0
        if ctx.profiling:
            component_ms["fuzzy_ms"] += (perf_counter() - t) * 1000.0

        t = perf_counter()
        token_score = self._score_tokens(doc, ctx.query_tokens)
        if ctx.profiling:
            component_ms["tokens_ms"] += (perf_counter() - t) * 1000.0

        content_score = self._score_content(doc, ctx.query_norm, ctx.query_tokens) if ctx.usar_contenido else 0.0

        t = perf_counter()
        temporal_score = self._score_temporal(doc, ctx.query_tokens)
        if ctx.profiling:
            component_ms["temporal_ms"] += (perf_counter() - t) * 1000.0

        t = perf_counter()
        structural_score = self._score_structural(doc, ctx.query_tokens, ctx.filtros)
        if ctx.profiling:
            component_ms["structural_ms"] += (perf_counter() - t) * 1000.0

        t = perf_counter()
        semantic_score = semantic_scores.get(doc.hash, 0.0) if ctx.usar_semantico else 0.0
        if ctx.profiling:
            component_ms["semantic_ms"] += (perf_counter() - t) * 1000.0

        t = perf_counter()
        boost_value = self._boost_contextual(
            doc,
            ctx.query_tokens,
            ctx.filtros,
            boost_weights=ctx.boost_weights,
            temporal_score=temporal_score,
        )
        if ctx.profiling:
            component_ms["boosting_ms"] += (perf_counter() - t) * 1000.0

        if ctx.modo == STRICT_MODE:
            # Estricta: exactitud + filtros; sin fuzzy ni semántica.
            strict_raw = (exact_score * 0.70) + (token_score * 0.30)
            return strict_raw, {
                "exact": exact_score,
                "tokens": token_score,
                "fuzzy": 0.0,
                "semantic": 0.0,
                "content": 0.0,
                "temporal": 0.0,
                "structural": 0.0,
                "boost": 1.0,
                "final": strict_raw,
            }, component_ms

        raw = (
            exact_score * ctx.weights.exacto
            + fuzzy_score * ctx.weights.fuzzy
            + semantic_score * ctx.weights.tfidf
            + content_score * ctx.weights.contenido
            + token_score * ctx.weights.tokens
            + temporal_score * ctx.weights.temporal
            + structural_score * ctx.weights.estructural
        )
        boosted = raw * boost_value * ctx.idf_query_factor
        return boosted, {
            "exact": exact_score,
            "tokens": token_score,
            "fuzzy": fuzzy_score,
            "semantic": semantic_score,
            "content": content_score,
            "temporal": temporal_score,
            "structural": structural_score,
            "boost": boost_value,
            "final": boosted,
        }, component_ms

    def indexar_documentos(self) -> None:
        """Indexa documentos con cache interno para búsquedas de alto volumen."""
        self.index = []
        self._doc_tokens.clear()
        self._doc_name_norm.clear()
        self._doc_content_norm.clear()
        self._doc_struct_tokens.clear()
        self._doc_date.clear()
        self._invalidate_semantic_cache()

        start = perf_counter()
        logger.info("Iniciando indexación documental...")
        fallidos = 0
        for i, raw in enumerate(self.documentos):
            try:
                doc = self._build_document(raw, i)
                self.index.append(doc)
                self._build_document_cache(doc)
            except Exception:
                fallidos += 1
                logger.warning("Error indexando documento #%s", i, exc_info=True)
        self._refresh_field_frequencies()
        elapsed = perf_counter() - start
        logger.info("Indexación completada: %s documentos (%s fallidos) en %.3fs", len(self.index), fallidos, elapsed)
        self._log_audit(
            {
                "evento": "indexacion",
                "documentos": len(self.index),
                "fallidos": fallidos,
                "duracion_ms": round(elapsed * 1000, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def buscar_por_nombre(self, query: str, usar_fuzzy: bool = True) -> list[dict[str, object]]:
        """Busca por nombre con coincidencia exacta, parcial y difusa."""
        q = self._normalizar_texto(query)
        if not q:
            return []
        if not self.index:
            self.indexar_documentos()
        salida: list[dict[str, object]] = []
        for doc in self.index:
            exact = self._score_exact(doc, q)
            fuzzy_score = self._safe_ratio(q, self._doc_name_norm.get(doc.hash, "")) if usar_fuzzy else 0.0
            score = max(exact, fuzzy_score)
            if score > 0:
                salida.append(self._resultado(doc, score * 100.0))
        return sorted(salida, key=lambda x: self._to_float(x.get("relevancia", 0.0)), reverse=True)

    def buscar_por_extension(self, ext: str) -> list[dict[str, object]]:
        """Filtra por extensión de archivo."""
        target = self._normalizar_texto(ext)
        if target and not target.startswith("."):
            target = f".{target}"
        return [self._resultado(doc, 100.0) for doc in self.index if self._normalizar_texto(doc.extension) == target]

    def buscar_por_carpeta(self, carpeta: str) -> list[dict[str, object]]:
        """Filtra por carpeta lógica/base."""
        target = self._normalizar_texto(carpeta)
        return [self._resultado(doc, 100.0) for doc in self.index if self._normalizar_texto(doc.carpeta) == target]

    def buscar_por_tipo(self, tipo: str) -> list[dict[str, object]]:
        """Filtra por tipo documental."""
        target = self._normalizar_texto(tipo)
        return [self._resultado(doc, 100.0) for doc in self.index if self._normalizar_texto(doc.tipo) == target]

    def buscar_por_etiquetas(self, lista: list[str]) -> list[dict[str, object]]:
        """Filtra por conjunto de etiquetas (AND lógico)."""
        tags = [self._normalizar_texto(x) for x in lista if self._normalizar_texto(x)]
        if not tags:
            return []
        salida: list[dict[str, object]] = []
        for doc in self.index:
            set_doc = {self._normalizar_texto(t) for t in doc.etiquetas}
            hits = sum(1 for t in tags if t in set_doc)
            if hits:
                salida.append(self._resultado(doc, 100.0 * (hits / max(1, len(tags)))))
        return sorted(salida, key=lambda x: self._to_float(x.get("relevancia", 0.0)), reverse=True)

    def buscar_por_contenido(self, query: str) -> list[dict[str, object]]:
        """Busca coincidencias dentro del contenido extraído."""
        q = self._normalizar_texto(query)
        if not q:
            return []
        if not self.index:
            self.indexar_documentos()
        tokens = self._tokenizar(q)
        salida: list[dict[str, object]] = []
        for doc in self.index:
            score = self._score_content(doc, q, tokens)
            if score > 0:
                salida.append(self._resultado(doc, score * 100.0))
        return sorted(salida, key=lambda x: self._to_float(x.get("relevancia", 0.0)), reverse=True)

    def construir_modelo_semantico(self) -> None:
        """Construye TF-IDF con configuración dinámica por tamaño del corpus."""
        textos = [self._semantic_vector(doc) for doc in self.index]
        if not textos:
            self._invalidate_semantic_cache()
            return
        cfg = self._compute_dynamic_tfidf_config()
        self._tfidf = TfidfVectorizer(**cfg)
        self._matriz_tfidf = self._tfidf.fit_transform(textos)
        self._idf_map = {
            term: float(self._tfidf.idf_[idx])
            for term, idx in getattr(self._tfidf, "vocabulary_", {}).items()
            if idx < len(self._tfidf.idf_)
        }
        logger.info("Modelo semántico TF-IDF construido: %s documentos", len(textos))

    def buscar_semantico(self, query: str, top_k: int = 20) -> list[dict[str, object]]:
        """Busca por similitud semántica, con fallback robusto y orden estable."""
        if not self.index:
            return []
        if self._tfidf is None or self._matriz_tfidf is None:
            self.construir_modelo_semantico()
        if self._tfidf is None or self._matriz_tfidf is None:
            return []

        qv = self._tfidf.transform([query])
        sims = cosine_similarity(qv, self._matriz_tfidf).flatten()

        docs_sem = []
        for i, score in enumerate(sims.tolist()):
            if i < len(self.index):
                docs_sem.append({"id": self.index[i].hash, "doc": self.index[i], "vector": np.array([score]), "score": score})

        salida: list[dict[str, object]] = []
        try:
            similares = buscar_similares(query, docs_sem, top_k=top_k)
            for item in similares:
                doc = item.get("doc")
                if isinstance(doc, DocumentoIndexado):
                    salida.append(self._resultado(doc, float(item.get("score", 0.0)) * 100.0))
        except Exception:
            logger.debug("Fallback a ranking semántico local", exc_info=True)

        if salida:
            return salida

        idx_sorted = np.argsort(sims)[::-1][: max(1, min(top_k, len(self.index)))]
        return [self._resultado(self.index[i], float(sims[i]) * 100.0) for i in idx_sorted if float(sims[i]) > 0]

    def combinar_resultados(self, *listas: list[dict[str, object]]) -> list[dict[str, object]]:
        """Combina listas de resultados manteniendo un score agregado por documento."""
        acc: dict[str, dict[str, object]] = {}
        score_map: dict[str, list[float]] = {}
        for lista in listas:
            for item in lista:
                key = str(item.get("id") or item.get("hash") or item.get("ruta"))
                if not key:
                    continue
                acc[key] = dict(item)
                score_map.setdefault(key, []).append(self._to_float(item.get("relevancia", 0.0)))

        for key, scores in score_map.items():
            acc[key]["relevancia"] = round(sum(scores) / max(1, len(scores)), 4)

        return sorted(acc.values(), key=lambda x: self._to_float(x.get("relevancia", 0.0)), reverse=True)

    def buscar_avanzado(
        self,
        query: str,
        filtros: dict[str, object],
        usar_nombre: bool = True,
        usar_contenido: bool = True,
        usar_semantico: bool = False,
        modo: str | None = None,
        top_k: int | None = None,
        weights: dict[str, object] | None = None,
        auditoria: bool = False,
        profiling: bool = False,
    ) -> list[dict[str, object]]:
        """Búsqueda avanzada con ranking híbrido, boosting y modo estricto/flexible."""
        if not self.index:
            self.indexar_documentos()

        ctx = self._build_query_context(
            query=query,
            filtros=filtros or {},
            usar_nombre=usar_nombre,
            usar_contenido=usar_contenido,
            usar_semantico=usar_semantico,
            modo=modo,
            weights=weights,
            auditoria=auditoria,
            profiling=profiling,
        )
        perf_components: dict[str, float] = {
            "prepare_corpus_ms": 0.0,
            "fuzzy_ms": 0.0,
            "tfidf_ms": 0.0,
            "semantic_ms": 0.0,
            "tokens_ms": 0.0,
            "temporal_ms": 0.0,
            "structural_ms": 0.0,
            "boosting_ms": 0.0,
            "ranking_ms": 0.0,
            "audit_ms": 0.0,
        }

        prepare_start = perf_counter()
        candidates = self._filter_candidates(ctx.filtros)
        if ctx.profiling:
            perf_components["prepare_corpus_ms"] += (perf_counter() - prepare_start) * 1000.0
        if not candidates:
            self._last_performance_metrics = {}
            return []

        if not ctx.query_norm:
            salida = [self._resultado(doc, 100.0) for doc in candidates]
            self._last_performance_metrics = {}
            return sorted(salida, key=lambda x: self._to_float(x.get("relevancia", 0.0)), reverse=True)

        if ctx.usar_semantico and ctx.modo != STRICT_MODE:
            tfidf_start = perf_counter()
            semantic_scores = self._semantic_scores(ctx.query_raw)
            if ctx.profiling:
                perf_components["tfidf_ms"] += (perf_counter() - tfidf_start) * 1000.0
        else:
            semantic_scores = {}

        ranked: list[tuple[DocumentoIndexado, float, dict[str, float]]] = []
        for doc in candidates:
            score_raw, components, comp_ms = self._rank_document(doc, ctx, semantic_scores)
            if ctx.profiling:
                for key in ("fuzzy_ms", "semantic_ms", "tokens_ms", "temporal_ms", "structural_ms", "boosting_ms"):
                    perf_components[key] += float(comp_ms.get(key, 0.0))
            if ctx.modo == STRICT_MODE and score_raw <= 0:
                continue
            if score_raw > 0:
                ranked.append((doc, min(1.0, score_raw), components))

        rank_start = perf_counter()
        ranked.sort(key=lambda x: x[1], reverse=True)
        if top_k and top_k > 0:
            ranked = ranked[:top_k]
        if ctx.profiling:
            perf_components["ranking_ms"] += (perf_counter() - rank_start) * 1000.0

        elapsed_ms = round((perf_counter() - ctx.started_at) * 1000, 2)
        self._log_audit(
            {
                "evento": "busqueda_avanzada",
                "audit_id": ctx.audit_id,
                "query": ctx.query_raw,
                "modo": ctx.modo,
                "filtros": dict(ctx.filtros),
                "usar_semantico": ctx.usar_semantico,
                "candidatos": len(candidates),
                "resultados": len(ranked),
                "duracion_ms": elapsed_ms,
                "idf_factor": round(ctx.idf_query_factor, 4),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.info(
            "Búsqueda '%s' modo=%s candidatos=%s resultados=%s tiempo=%.2fms",
            ctx.query_raw,
            ctx.modo,
            len(candidates),
            len(ranked),
            elapsed_ms,
        )

        salida_final: list[dict[str, object]] = []
        audit_start = perf_counter()
        for doc, score, components in ranked:
            item = self._resultado(doc, score * 100.0)
            if auditoria:
                item["score_exacto"] = round(float(components.get("exact", 0.0)) * 100.0, 4)
                item["score_fuzzy"] = round(float(components.get("fuzzy", 0.0)) * 100.0, 4)
                item["score_semantico"] = round(float(components.get("semantic", 0.0)) * 100.0, 4)
                item["score_tokens"] = round(float(components.get("tokens", 0.0)) * 100.0, 4)
                item["score_temporal"] = round(float(components.get("temporal", 0.0)) * 100.0, 4)
                item["score_estructural"] = round(float(components.get("structural", 0.0)) * 100.0, 4)
                item["score_boosting"] = round(float(components.get("boost", 0.0)), 4)
                item["score_final"] = round(float(components.get("final", score)) * 100.0, 4)
            salida_final.append(item)

        if auditoria:
            self._log_audit(
                {
                    "evento": "busqueda_auditoria",
                    "audit_id": ctx.audit_id,
                    "query": ctx.query_raw,
                    "modo": ctx.modo,
                    "weights": asdict(ctx.weights),
                    "boost_weights": dict(ctx.boost_weights),
                    "resultados": len(salida_final),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        if ctx.profiling:
            perf_components["audit_ms"] += (perf_counter() - audit_start) * 1000.0

        if ctx.profiling:
            perf_payload: dict[str, object] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version_motor": SEARCH_ENGINE_VERSION,
                "total_time_ms": round(float(elapsed_ms), 4),
                "components": {k: round(float(v), 4) for k, v in perf_components.items()},
            }
            self._last_performance_metrics = perf_payload
            self._log_audit(
                {
                    "evento": "busqueda_profiling",
                    "audit_id": ctx.audit_id,
                    "query": ctx.query_raw,
                    "performance_metrics": perf_payload,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        else:
            self._last_performance_metrics = {}

        self._last_query_context = self._ctx_to_dict(ctx)
        if ctx.profiling:
            self._last_query_context["performance_metrics"] = dict(self._last_performance_metrics)
        self._last_audited_results = list(salida_final)

        return salida_final

    def get_last_performance_metrics(self) -> dict[str, object]:
        """Retorna métricas de performance de la última búsqueda perfilada."""
        return dict(self._last_performance_metrics)

    def get_audit_log(self, limit: int = 200) -> list[dict[str, object]]:
        """Devuelve eventos de auditoría recientes de indexación y búsquedas."""
        if limit <= 0:
            return []
        return self.audit_log[-limit:]


def benchmark_busquedas(
    engine: SearchEngine,
    consultas: list[str],
    filtros: dict[str, object] | None = None,
    repeticiones: int = 3,
    modo: str = FLEX_MODE,
) -> dict[str, object]:
    """Ejecuta benchmark simple para auditoría de rendimiento de búsquedas."""
    if repeticiones < 1:
        repeticiones = 1
    filtros_eval = filtros or {"tipo": "TODOS", "extension": "TODOS", "carpeta": "TODOS", "etiquetas": [], "fuzzy": True}
    tiempos_ms: list[float] = []
    total_resultados = 0
    for _ in range(repeticiones):
        for q in consultas:
            start = perf_counter()
            out = engine.buscar_avanzado(
                q,
                filtros=filtros_eval,
                usar_nombre=True,
                usar_contenido=True,
                usar_semantico=True,
                modo=modo,
            )
            tiempos_ms.append((perf_counter() - start) * 1000.0)
            total_resultados += len(out)
    if not tiempos_ms:
        return {"consultas": 0, "media_ms": 0.0, "p95_ms": 0.0, "resultados": 0}

    media = float(np.mean(tiempos_ms))
    p95 = float(np.percentile(tiempos_ms, 95))
    return {
        "consultas": len(consultas) * repeticiones,
        "media_ms": round(media, 4),
        "p95_ms": round(p95, 4),
        "max_ms": round(float(np.max(tiempos_ms)), 4),
        "min_ms": round(float(np.min(tiempos_ms)), 4),
        "resultados": total_resultados,
    }


def construir_estadisticas_busqueda(search_logs: list[dict[str, object]]) -> dict[str, dict[str, int]]:
    """Construye estadísticas agregadas para dashboard y auditoría."""
    terminos = Counter(str(x.get("query", "")).strip().lower() for x in search_logs if str(x.get("query", "")).strip())
    tipos = Counter(str(x.get("tipo_top", "")) for x in search_logs if str(x.get("tipo_top", "")))
    carpetas = Counter(str(x.get("carpeta_top", "")) for x in search_logs if str(x.get("carpeta_top", "")))
    return {
        "terminos_mas_buscados": dict(terminos.most_common(10)),
        "tipos_mas_encontrados": dict(tipos.most_common(10)),
        "carpetas_mas_relevantes": dict(carpetas.most_common(10)),
    }
