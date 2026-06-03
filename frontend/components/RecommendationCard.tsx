import type { Recommendation } from "../types";
import { Metric } from "./Metric";

export function RecommendationCard({
  recommendation,
  rank,
}: {
  recommendation: Recommendation;
  rank: number;
}) {
  return (
    <article className="rounded-2xl border border-white/70 bg-white/90 p-5 shadow-sm shadow-slate-200/70">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-teal-700 text-sm font-semibold text-white shadow-sm shadow-teal-900/10">
            #{rank}
          </div>
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
              {recommendation.name}
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {recommendation.state} · {recommendation.pass_type} pass
            </p>
          </div>
        </div>
      </div>

      <dl className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          label="Score"
          value={recommendation.total_score.toFixed(1)}
          featured
        />
        <Metric
          label="Estimated Cost"
          value={`$${recommendation.estimated_total_cost}`}
          featured
        />
        <Metric label="Drive Hours" value={`${recommendation.drive_hours}`} featured />
        <Metric
          label="Snow Score"
          value={
            recommendation.snow_score === null
              ? "Unavailable"
              : recommendation.snow_score.toFixed(1)
          }
          featured
        />
      </dl>

      <p className="mt-4 border-t border-slate-100 pt-4 text-sm leading-6 text-slate-600">
        {recommendation.reason}
      </p>

      {recommendation.weather ? (
        <dl className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Metric
            label="Temperature"
            value={formatWeather(recommendation.weather.temperature_f, "F")}
            featured
          />
          <Metric
            label="Wind"
            value={formatWeather(recommendation.weather.wind_speed_mph, "mph")}
            featured
          />
          <Metric
            label="Today Snow"
            value={formatWeather(
              recommendation.weather.snowfall_inches_today,
              "in",
            )}
            featured
          />
          <Metric
            label="3-Day Snow"
            value={formatWeather(
              recommendation.weather.snowfall_inches_next_3_days,
              "in",
            )}
            featured
          />
        </dl>
      ) : null}
    </article>
  );
}

function formatWeather(value: number | null, unit: string) {
  return value === null ? "Unavailable" : `${value} ${unit}`;
}
