# L9_META
# role: observability_metrics
# version: 1.0.0
# status: template_infrastructure
"""OTel metrics — counter, updown, histogram, timer. Fix-B design."""

from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager

from opentelemetry import metrics as otel_metrics
from opentelemetry.metrics import Counter, Histogram, MeterProvider, UpDownCounter


class Metrics:
    # Fix-B: set by test fixtures only. Never set in production.
    _test_provider: MeterProvider | None = None

    def __init__(self, namespace: str, *, version: str = "1.0.0") -> None:
        self._ns = namespace
        self._version = version
        self._meter: otel_metrics.Meter | None = None
        self._counters: dict[str, Counter] = {}
        self._hists: dict[str, Histogram] = {}
        self._updowns: dict[str, UpDownCounter] = {}

    def _get_meter(self) -> otel_metrics.Meter:
        if self._meter is None:
            provider = Metrics._test_provider or otel_metrics.get_meter_provider()
            self._meter = provider.get_meter(self._ns, self._version)
        return self._meter

    def _full(self, name: str) -> str:
        return f"{self._ns}.{name}"

    def count(
        self,
        name: str,
        *,
        value: int | float = 1,
        labels: dict[str, str] | None = None,
        description: str = "",
        unit: str = "{count}",
    ) -> None:
        fn = self._full(name)
        if fn not in self._counters:
            self._counters[fn] = self._get_meter().create_counter(
                fn, description=description, unit=unit
            )
        self._counters[fn].add(value, attributes=labels or {})

    def updown(
        self,
        name: str,
        *,
        value: int | float,
        labels: dict[str, str] | None = None,
        description: str = "",
        unit: str = "{item}",
    ) -> None:
        fn = self._full(name)
        if fn not in self._updowns:
            self._updowns[fn] = self._get_meter().create_up_down_counter(
                fn, description=description, unit=unit
            )
        self._updowns[fn].add(value, attributes=labels or {})

    def record(
        self,
        name: str,
        *,
        value: float,
        labels: dict[str, str] | None = None,
        description: str = "",
        unit: str = "ms",
    ) -> None:
        fn = self._full(name)
        if fn not in self._hists:
            self._hists[fn] = self._get_meter().create_histogram(
                fn, description=description, unit=unit
            )
        self._hists[fn].record(value, attributes=labels or {})

    @contextmanager
    def timer(
        self, name: str, *, labels: dict[str, str] | None = None, description: str = ""
    ) -> Generator[None, None, None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            self.record(
                name,
                value=(time.perf_counter() - start) * 1000,
                labels=labels,
                description=description,
                unit="ms",
            )
