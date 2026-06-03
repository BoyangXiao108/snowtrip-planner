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

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const TERRAIN_OPTIONS: { value: Preference; label: string }[] = [
  { value: "trees", label: "Trees" },
  { value: "park", label: "Park" },
  { value: "groomers", label: "Groomers" },
  { value: "powder", label: "Powder" },
];

export default function Home() {
  const [origin, setOrigin] = useState("Boston");
  const [days, setDays] = useState("3");
  const [budget, setBudget] = useState("1000");
  const [passType, setPassType] = useState<PassType>("Epic");
  const [preferences, setPreferences] = useState<Preference[]>(["trees"]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    if (preferences.length === 0) {
      setIsLoading(false);
      setError("Select at least one terrain preference.");
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
          preferences,
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

  function togglePreference(preference: Preference) {
    setPreferences((currentPreferences) =>
      currentPreferences.includes(preference)
        ? currentPreferences.filter((item) => item !== preference)
        : [...currentPreferences, preference],
    );
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
            <div className="space-y-4">
              <Field label="Origin">
                <input
                  id="origin"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-950 outline-none ring-teal-600 focus:ring-2"
                  value={origin}
                  onChange={(event) => setOrigin(event.target.value)}
                  required
                />
              </Field>

              <div className="grid grid-cols-2 gap-3">
                <Field label="Days">
                  <input
                    id="days"
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-950 outline-none ring-teal-600 focus:ring-2"
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
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-950 outline-none ring-teal-600 focus:ring-2"
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
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 outline-none ring-teal-600 focus:ring-2"
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
                  Preferences
                </legend>
                <div className="grid grid-cols-2 gap-2">
                  {TERRAIN_OPTIONS.map((option) => (
                    <label
                      key={option.value}
                      className="flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
                    >
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-slate-300 text-teal-700 focus:ring-teal-600"
                        checked={preferences.includes(option.value)}
                        onChange={() => togglePreference(option.value)}
                      />
                      {option.label}
                    </label>
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
              <div className="rounded-lg border border-slate-200 bg-white p-6 text-slate-700 shadow-sm">
                Submit the form to see your top 3 resort matches.
              </div>
            ) : null}

            <div className="grid gap-4">
              {recommendations.map((recommendation) => (
                <RecommendationCard
                  key={`${recommendation.name}-${recommendation.state}`}
                  recommendation={recommendation}
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
}: {
  recommendation: Recommendation;
}) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-950">
            {recommendation.name}
          </h2>
          <p className="text-sm text-slate-600">
            {recommendation.state} · {recommendation.pass_type} pass
          </p>
        </div>
        <div className="rounded-md bg-cyan-50 px-3 py-2 text-left sm:text-right">
          <p className="text-xs font-medium uppercase text-cyan-800">Total score</p>
          <p className="text-lg font-semibold text-cyan-950">
            {recommendation.total_score.toFixed(1)}
          </p>
        </div>
      </div>

      <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Metric label="Estimated total cost" value={`$${recommendation.estimated_total_cost}`} />
        <Metric label="Drive hours" value={`${recommendation.drive_hours}`} />
        <Metric label="Pass type" value={recommendation.pass_type} />
      </dl>

      <p className="mt-4 text-sm leading-6 text-slate-700">
        {recommendation.reason}
      </p>

      {recommendation.weather ? (
        <dl className="mt-4 grid gap-3 border-t border-slate-200 pt-4 sm:grid-cols-3">
          <Metric
            label="Temperature"
            value={formatWeather(recommendation.weather.temperature_f, "F")}
          />
          <Metric
            label="Wind speed"
            value={formatWeather(recommendation.weather.wind_speed_mph, "mph")}
          />
          <Metric
            label="Snowfall"
            value={formatWeather(recommendation.weather.snowfall_inches, "in")}
          />
        </dl>
      ) : null}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm font-semibold text-slate-950">{value}</dd>
    </div>
  );
}

function formatWeather(value: number | null, unit: string) {
  return value === null ? "Unavailable" : `${value} ${unit}`;
}
