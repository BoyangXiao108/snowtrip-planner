"use client";

import { FormEvent, useState } from "react";

type PassType = "Epic" | "Ikon" | "None";
type Preference = "trees" | "park" | "groomers" | "powder";

type Weather = {
  temperature_f: number | null;
  wind_speed_mph: number | null;
  snowfall_inches: number | null;
};

type Recommendation = {
  name: string;
  state: string;
  pass_type: PassType;
  drive_hours: number;
  estimated_total_cost: number;
  total_score: number;
  reason: string;
  weather: Weather | null;
};

type RecommendResponse = {
  recommendations: Recommendation[];
};

type TerrainWeights = Record<Preference, number>;

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const TERRAIN_OPTIONS: { value: Preference; label: string }[] = [
  { value: "trees", label: "Trees" },
  { value: "powder", label: "Powder" },
  { value: "groomers", label: "Groomers" },
  { value: "park", label: "Park" },
];
const DEFAULT_TERRAIN_WEIGHTS: TerrainWeights = {
  trees: 5,
  powder: 4,
  groomers: 2,
  park: 0,
};

export default function Home() {
  const [origin, setOrigin] = useState("Boston");
  const [days, setDays] = useState("3");
  const [budget, setBudget] = useState("1000");
  const [passType, setPassType] = useState<PassType>("Epic");
  const [terrainWeights, setTerrainWeights] = useState<TerrainWeights>(
    DEFAULT_TERRAIN_WEIGHTS,
  );
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    if (!Object.values(terrainWeights).some((weight) => weight > 0)) {
      setIsLoading(false);
      setError("Set at least one terrain weight above 0.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/recommend`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          origin,
          days: Number(days),
          budget: Number(budget),
          pass_type: passType,
          terrain_weights: terrainWeights,
        }),
      });

      if (!response.ok) {
        throw new Error("Unable to get recommendations. Check your inputs and try again.");
      }

      const data = (await response.json()) as RecommendResponse;
      setRecommendations(data.recommendations);
    } catch (error) {
      setRecommendations([]);
      setError(error instanceof Error ? error.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  }

  function updateTerrainWeight(preference: Preference, value: string) {
    const weight = Math.min(5, Math.max(0, Number(value)));

    setTerrainWeights((currentWeights) => ({
      ...currentWeights,
      [preference]: weight,
    }));
  }

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
            Snowtrip Planner
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950 sm:text-4xl">
            Find a ski trip that fits your pass, budget, and terrain.
          </h1>
        </header>

        <section className="grid gap-6 lg:grid-cols-[360px_1fr]">
          <form
            onSubmit={handleSubmit}
            className="h-fit rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="space-y-5">
              <Field label="Origin">
                <input
                  id="origin"
                  className="w-full rounded-md border border-slate-300 px-3 py-2.5 text-slate-950 outline-none ring-teal-600 focus:ring-2"
                  value={origin}
                  onChange={(event) => setOrigin(event.target.value)}
                  required
                />
              </Field>

              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-2">
                <Field label="Days">
                  <input
                    id="days"
                    className="w-full rounded-md border border-slate-300 px-3 py-2.5 text-slate-950 outline-none ring-teal-600 focus:ring-2"
                    type="number"
                    min="1"
                    value={days}
                    onChange={(event) => setDays(event.target.value)}
                    required
                  />
                </Field>

                <Field label="Budget">
                  <input
                    id="budget"
                    className="w-full rounded-md border border-slate-300 px-3 py-2.5 text-slate-950 outline-none ring-teal-600 focus:ring-2"
                    type="number"
                    min="1"
                    value={budget}
                    onChange={(event) => setBudget(event.target.value)}
                    required
                  />
                </Field>
              </div>

              <Field label="Pass Type">
                <select
                  id="pass-type"
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 text-slate-950 outline-none ring-teal-600 focus:ring-2"
                  value={passType}
                  onChange={(event) => setPassType(event.target.value as PassType)}
                >
                  <option value="Epic">Epic</option>
                  <option value="Ikon">Ikon</option>
                  <option value="None">None</option>
                </select>
              </Field>

              <fieldset>
                <legend className="mb-2 text-sm font-medium text-slate-800">
                  Terrain Weights
                </legend>
                <div className="space-y-3">
                  {TERRAIN_OPTIONS.map((option) => (
                    <div
                      key={option.value}
                      className="rounded-md border border-slate-300 bg-slate-50 p-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <label
                          htmlFor={`terrain-${option.value}`}
                          className="text-sm font-medium text-slate-900"
                        >
                          {option.label}
                        </label>
                        <input
                          id={`terrain-${option.value}`}
                          type="number"
                          min="0"
                          max="5"
                          className="w-16 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-center text-sm font-semibold text-slate-950 outline-none ring-teal-600 focus:ring-2"
                          value={terrainWeights[option.value]}
                          onChange={(event) =>
                            updateTerrainWeight(option.value, event.target.value)
                          }
                        />
                      </div>
                      <input
                        aria-label={`${option.label} weight`}
                        type="range"
                        min="0"
                        max="5"
                        step="1"
                        className="mt-2 w-full accent-teal-700"
                        value={terrainWeights[option.value]}
                        onChange={(event) =>
                          updateTerrainWeight(option.value, event.target.value)
                        }
                      />
                    </div>
                  ))}
                </div>
              </fieldset>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full rounded-md bg-teal-700 px-4 py-2.5 font-semibold text-white shadow-sm transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isLoading ? "Finding resorts..." : "Recommend"}
              </button>
            </div>
          </form>

          <section aria-live="polite">
            {error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
                {error}
              </div>
            ) : null}

            {recommendations.length === 0 && !error ? (
              <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-950">
                  Ready when you are.
                </h2>
                <p className="mt-2 max-w-xl text-sm leading-6 text-slate-700">
                  Choose your pass, budget, trip length, and one or more terrain
                  weights. Snowtrip Planner will rank three resorts that fit the
                  trip you have in mind.
                </p>
              </div>
            ) : null}

            <div className="grid gap-4">
              {recommendations.map((recommendation, index) => (
                <RecommendationCard
                  key={`${recommendation.name}-${recommendation.state}`}
                  recommendation={recommendation}
                  rank={index + 1}
                />
              ))}
            </div>
          </section>
        </section>
      </div>
    </main>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block text-sm font-medium text-slate-800">
      <span className="mb-1.5 block">{label}</span>
      {children}
    </label>
  );
}

function RecommendationCard({
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
        <dl className="mt-4 grid gap-3 border-t border-slate-200 pt-4 sm:grid-cols-3">
          <Metric
            label="Temperature"
            value={formatWeather(recommendation.weather.temperature_f, "F")}
            featured
          />
          <Metric
            label="Wind speed"
            value={formatWeather(recommendation.weather.wind_speed_mph, "mph")}
            featured
          />
          <Metric
            label="Snowfall"
            value={formatWeather(recommendation.weather.snowfall_inches, "in")}
            featured
          />
        </dl>
      ) : null}
    </article>
  );
}

function Metric({
  label,
  value,
  featured = false,
}: {
  label: string;
  value: string;
  featured?: boolean;
}) {
  return (
    <div className={featured ? "rounded-md bg-slate-50 p-3" : undefined}>
      <dt className="text-xs font-medium uppercase text-slate-500">{label}</dt>
      <dd
        className={
          featured
            ? "mt-1 text-lg font-semibold text-slate-950"
            : "mt-1 text-sm font-semibold text-slate-950"
        }
      >
        {value}
      </dd>
    </div>
  );
}

function formatWeather(value: number | null, unit: string) {
  return value === null ? "Unavailable" : `${value} ${unit}`;
}
