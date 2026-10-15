"""Monthly ADP forecasts using simple exponential smoothing of job changes.

Standard-library only. Forecasts use revised history, not release vintages.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Protocol

DEFAULT_CSV = Path(__file__).resolve().parent / "ADP_NER_history.csv"


@dataclass(frozen=True)
class EmploymentObservation:
    month: date
    employment: float


class EmploymentSource(Protocol):
    """A future ADP download source can implement the same interface."""

    def monthly_series(self, breakdown: str, category: str) -> list[EmploymentObservation]: ...


class CSVEmploymentSource:
    def __init__(self, path: str | Path = DEFAULT_CSV):
        self.path = Path(path)

    def monthly_series(self, breakdown: str = "National", category: str = "U.S.") -> list[EmploymentObservation]:
        observations = []
        with self.path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            required = {"timestep", "agg_RIS", "category", "date", "NER_SA"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError(f"CSV must contain columns: {', '.join(sorted(required))}")
            for row in reader:
                if (row["timestep"], row["agg_RIS"], row["category"]) == ("M", breakdown, category):
                    observations.append(EmploymentObservation(date.fromisoformat(row["date"]), float(row["NER_SA"])))
        if not observations:
            raise ValueError(f"No monthly series found for {breakdown!r}, {category!r}")
        return observations


def next_month(month: date) -> date:
    return date(month.year + (month.month == 12), month.month % 12 + 1, 1)


@dataclass(frozen=True)
class Forecast:
    breakdown: str
    category: str
    last_observed_month: date
    target_month: date
    last_employment: float
    predicted_change: float
    predicted_employment: float
    alpha: float
    observations_used: int
    recent_changes: tuple[tuple[date, float], ...]
    explanation: str


@dataclass(frozen=True)
class BacktestPrediction:
    origin: date
    target: date
    predicted_change: float
    actual_change: float

    @property
    def error(self) -> float:
        """Positive means overprediction."""
        return self.predicted_change - self.actual_change


@dataclass(frozen=True)
class BacktestResult:
    predictions: tuple[BacktestPrediction, ...]
    excluded_targets: tuple[date, ...]
    mae: float
    rmse: float
    bias: float


class ExponentialSmoothingForecaster:
    """Smooth seasonally adjusted monthly *changes*, then add to latest level.

    Initialize with the first observed change. Alpha is explicit and fixed;
    the default 0.8 was selected for lowest MAE in the historical weight comparison.
    """

    def __init__(self, source: EmploymentSource | None = None, alpha: float = 0.8):
        if not math.isfinite(alpha) or not 0 < alpha <= 1:
            raise ValueError("alpha must be finite and in (0, 1]")
        self.source = source if source is not None else CSVEmploymentSource()
        self.alpha = alpha

    def _series(self, breakdown: str, category: str, as_of: date | None) -> list[EmploymentObservation]:
        series = sorted(self.source.monthly_series(breakdown, category), key=lambda x: x.month)
        if as_of is not None:
            series = [x for x in series if x.month <= as_of]
        if len(series) < 2:
            raise ValueError("At least two monthly employment observations are required")
        for i, item in enumerate(series):
            if item.month.day != 1:
                raise ValueError("Monthly dates must use the first day of the month")
            if not math.isfinite(item.employment) or item.employment < 0:
                raise ValueError("Employment must be finite and nonnegative")
            if i and item.month != next_month(series[i - 1].month):
                raise ValueError("Monthly series contains duplicate or missing months")
        return series

    def forecast(self, breakdown: str = "National", category: str = "U.S.", *, as_of: date | None = None) -> Forecast:
        """As-of is an observation-month cutoff, not a historical release date."""
        series = self._series(breakdown, category, as_of)
        changes = [(b.month, b.employment - a.employment) for a, b in zip(series, series[1:])]
        smoothed = changes[0][1]
        for _, change in changes[1:]:
            smoothed = self.alpha * change + (1 - self.alpha) * smoothed
        last = series[-1]
        explanation = (
            f"Forecast for {next_month(last.month):%B %Y}: {smoothed:+,.0f} jobs. "
            f"Simple exponential smoothing of {len(changes)} monthly seasonally adjusted changes, "
            f"initialized with the first change. Each update gives the newest change "
            f"{self.alpha:.0%} weight and the previous smoothed estimate {1-self.alpha:.0%}. "
            f"The latest actual change was {changes[-1][1]:+,.0f} jobs. "
            f"Adding the forecast change to the latest employment level "
            f"({last.employment:,.0f}) gives {last.employment + smoothed:,.0f} jobs. "
            "Uses revised CSV history; no weekly inputs or additional seasonal adjustment."
        )
        return Forecast(breakdown, category, last.month, next_month(last.month), last.employment,
                        smoothed, last.employment + smoothed, self.alpha, len(series),
                        tuple(changes[-6:]), explanation)

    def backtest(self, breakdown: str = "National", category: str = "U.S.", *,
                 min_training_months: int = 60,
                 excluded_periods: Iterable[tuple[date, date]] = ((date(2020, 3, 1), date(2021, 12, 1)),)) -> BacktestResult:
        """Expanding-window one-month forecasts. Exclusions affect scoring only.

        Default pandemic scoring exclusion is a configurable project policy.
        Fixed alpha is never tuned using the target observation.
        """
        if min_training_months < 2:
            raise ValueError("min_training_months must be at least 2")
        exclusions = tuple(excluded_periods)
        if any(start > end for start, end in exclusions):
            raise ValueError("Exclusion start must not follow its end")
        series = self._series(breakdown, category, None)
        predictions, skipped = [], []
        smoothed = series[1].employment - series[0].employment
        for i in range(2, len(series)):
            actual = series[i].employment - series[i - 1].employment
            if i >= min_training_months:
                if any(start <= series[i].month <= end for start, end in exclusions):
                    skipped.append(series[i].month)
                else:
                    predictions.append(BacktestPrediction(series[i - 1].month, series[i].month, smoothed, actual))
            # Update only after predicting this target, including excluded targets.
            smoothed = self.alpha * actual + (1 - self.alpha) * smoothed
        if not predictions:
            raise ValueError("No scored predictions; reduce training length or exclusions")
        errors = [p.error for p in predictions]
        return BacktestResult(tuple(predictions), tuple(skipped),
                              sum(abs(e) for e in errors) / len(errors),
                              math.sqrt(sum(e * e for e in errors) / len(errors)),
                              sum(errors) / len(errors))
