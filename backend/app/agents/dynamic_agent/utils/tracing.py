import json
import logging
import time
from pathlib import Path
from typing import Any, Sequence
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import (
    SpanExporter,
    SpanExportResult,
)
class LocalLoggingSpanExporter(SpanExporter):
    """
    Простой экспортёр: пишет трейс-спаны в стандартный лог.
    Крупные attributes складывает в локальный файл и подменяет на URI.
    """
    def __init__(self, payload_dir: str | None = None, debug: bool = False, **_: Any) -> None:
        self.debug = debug
        self.payload_dir = Path(payload_dir or "/tmp/blog-writer-spans")
        self.payload_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            try:
                span_dict = json.loads(span.to_json())  # type: ignore[attr-defined]
            except Exception:
                try:
                    ctx = span.get_span_context()
                    trace_id = format(ctx.trace_id, "032x")
                    span_id = format(ctx.span_id, "016x")
                except Exception:
                    trace_id = ""
                    span_id = ""
                span_dict = {
                    "name": getattr(span, "name", "") or "",
                    "context": {
                        "trace_id": trace_id,
                        "span_id": span_id,
                    },
                    "attributes": dict(getattr(span, "attributes", {}) or {}),
                    "start_time": getattr(span, "start_time", None),
                    "end_time": getattr(span, "end_time", None),
                }
            span_dict = self._process_large_attributes(span_dict)
            if self.debug:
                print(span_dict)
            self.logger.info("otel_span", extra={"span": span_dict})
        return SpanExportResult.SUCCESS
    def shutdown(self) -> None:
        """Сигнал на завершение. Совместимость с интерфейсом OTel."""
        try:
            return None
        except Exception:
            return None
    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """На случай интеграций: у нас нет буферов — возвращаем True."""
        return True
    def _process_large_attributes(self, span_dict: dict) -> dict:
        attrs = span_dict.get("attributes", {}) or {}
        try:
            payload = json.dumps(attrs, ensure_ascii=False)
        except Exception:
            payload = "{}"
        if len(payload.encode("utf-8")) > 255 * 1024:
            name = span_dict.get("name", "span")
            span_id = (span_dict.get("context") or {}).get("span_id") or ""
            ts = int(time.time())
            file_path = self.payload_dir / f"{name}_{span_id}_{ts}.json"
            try:
                file_path.write_text(payload, encoding="utf-8")
                span_dict["attributes"] = {
                    "uri_payload": f"file://{file_path}",
                    "note": "attributes saved to local file because payload > 250KB",
                }
                self.logger.info("Большой payload span сохранён локально: %s", file_path)
            except Exception as ex:
                self.logger.warning("Не удалось сохранить большой payload: %r", ex)
        return span_dict
