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
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-teal-700 text-sm font-semibold text-white">
            #{rank}
          </div>
          <div>
            <h2 className="text-xl font-semibold text-slate-950">
              {recommendation.name}
            </h2>
            <p className="text-sm text-slate-600">
              {recommendation.state} · {recommendation.pass_type} pass
            </p>
          </div>
        </div>
        <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-left sm:text-right">
          <p className="text-xs font-medium uppercase text-slate-500">Score</p>
          <p className="text-sm font-semibold text-slate-700">
            {recommendation.total_score.toFixed(1)}
          </p>
          {recommendation.snow_score !== null ? (
            <p className="mt-1 text-xs font-medium text-sky-700">
              Snow +{recommendation.snow_score.toFixed(1)}
            </p>
          ) : null}
        </div>
      </div>

      <dl className="mt-5 grid gap-3 sm:grid-cols-3">
        <Metric
          label="Estimated total cost"
          value={`$${recommendation.estimated_total_cost}`}
          featured
        />
        <Metric label="Drive hours" value={`${recommendation.drive_hours}`} featured />
        <Metric label="Pass type" value={recommendation.pass_type} featured />
      </dl>

      <p className="mt-4 text-sm leading-6 text-slate-700">
        {recommendation.reason}
      </p>

      {recommendation.weather ? (
        <dl className="mt-4 grid gap-3 border-t border-slate-200 pt-4 sm:grid-cols-2 lg:grid-cols-4">
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
