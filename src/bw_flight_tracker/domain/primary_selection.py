from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from bw_flight_tracker.domain.models import FlightCandidate


@dataclass
class SelectionResult:
    candidate: FlightCandidate | None
    mode: str
    reason: str


@dataclass
class PrimarySelectionEngine:
    """Stateful automatic selector with hold time and challenger hysteresis."""

    minimum_hold_seconds: int = 15
    switch_improvement_ratio: float = 0.25
    required_challenger_cycles: int = 2
    current_icao: str | None = None
    selected_at_utc: datetime | None = None
    challenger_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def select(
        self,
        eligible: list[FlightCandidate],
        now: datetime | None = None,
    ) -> SelectionResult:
        now = now or datetime.now(UTC)
        if not eligible:
            self.current_icao = None
            self.selected_at_utc = None
            self.challenger_counts.clear()
            return SelectionResult(None, "automatic", "no eligible aircraft")

        by_icao = {candidate.aircraft.icao_hex: candidate for candidate in eligible}
        best = eligible[0]
        current = by_icao.get(self.current_icao or "")
        if current is None:
            return self._choose(best, now, "current primary ineligible or absent")

        held_for = now - (self.selected_at_utc or now)
        if held_for < timedelta(seconds=self.minimum_hold_seconds):
            self.challenger_counts.clear()
            return SelectionResult(current, "automatic", "minimum hold time active")

        current_score = current.computed.selection_score or float("inf")
        best_score = best.computed.selection_score or float("inf")
        if best.aircraft.icao_hex == current.aircraft.icao_hex:
            self.challenger_counts.clear()
            return SelectionResult(current, "automatic", "current primary remains best")

        required_score = current_score * (1 - self.switch_improvement_ratio)
        if best_score > required_score:
            self.challenger_counts.clear()
            return SelectionResult(
                current, "automatic", "challenger did not clear switch threshold"
            )

        challenger_icao = best.aircraft.icao_hex
        self.challenger_counts[challenger_icao] += 1
        for icao in list(self.challenger_counts):
            if icao != challenger_icao:
                del self.challenger_counts[icao]
        if self.challenger_counts[challenger_icao] >= self.required_challenger_cycles:
            return self._choose(best, now, "challenger cleared hysteresis")
        return SelectionResult(current, "automatic", "challenger pending hysteresis confirmation")

    def _choose(self, candidate: FlightCandidate, now: datetime, reason: str) -> SelectionResult:
        self.current_icao = candidate.aircraft.icao_hex
        self.selected_at_utc = now
        self.challenger_counts.clear()
        return SelectionResult(candidate, "automatic", reason)

    def reset(self) -> None:
        self.current_icao = None
        self.selected_at_utc = None
        self.challenger_counts.clear()
