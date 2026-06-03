"use client";

import { FormEvent, ReactNode, useState } from "react";

import { AdvisorSummary } from "../components/AdvisorSummary";
import { NaturalSearchPanel } from "../components/NaturalSearchPanel";
import { PlannerForm } from "../components/PlannerForm";
import { RecommendationCard } from "../components/RecommendationCard";
import { RetrievalDebugPanel } from "../components/RetrievalDebugPanel";
import {
  API_BASE_URL,
  DEFAULT_NATURAL_LANGUAGE_MESSAGE,
  DEFAULT_TERRAIN_WEIGHTS,
} from "../constants";
import type {
  AdvisorResponse,
  ParsedAdvisorResponse,
  PassType,
  Preference,
  Recommendation,
  RetrievalDebug,
  TerrainWeights,
} from "../types";

export default function Home() {
  const [origin, setOrigin] = useState("Boston");
  const [days, setDays] = useState("3");
  const [budget, setBudget] = useState("1000");
  const [passType, setPassType] = useState<PassType>("Epic");
  const [terrainWeights, setTerrainWeights] = useState<TerrainWeights>(
    DEFAULT_TERRAIN_WEIGHTS,
  );
  const [naturalLanguageMessage, setNaturalLanguageMessage] = useState(
    DEFAULT_NATURAL_LANGUAGE_MESSAGE,
  );
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [advisorSummary, setAdvisorSummary] = useState<string | null>(null);
  const [retrievalDebug, setRetrievalDebug] = useState<RetrievalDebug | null>(null);
  const [showRetrievalDetails, setShowRetrievalDetails] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleNaturalSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (naturalLanguageMessage.trim().length === 0) {
      setError("Enter a trip request.");
      return;
    }

    await submitRequest("natural");
  }

  async function handleStructuredSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!hasTerrainWeight(terrainWeights)) {
      setError("Set at least one terrain weight above 0.");
      return;
    }

    await submitRequest("structured");
  }

  async function submitRequest(requestType: "natural" | "structured") {
    setHasSearched(true);
    setIsLoading(true);
    setError(null);
    setAdvisorSummary(null);
    setRetrievalDebug(null);
    setShowRetrievalDetails(false);

    try {
      const response = await fetch(
        `${API_BASE_URL}/${requestType === "structured" ? "advisor" : "advisor/parse"}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(buildRequestBody(requestType)),
        },
      );

      if (!response.ok) {
        throw new Error("Unable to get recommendations. Check your inputs and try again.");
      }

      const data = (await response.json()) as AdvisorResponse | ParsedAdvisorResponse;
      setRecommendations(data.recommendations);
      setAdvisorSummary(data.advisor_summary?.trim() || null);
      setRetrievalDebug(
        "retrieval_debug" in data ? data.retrieval_debug ?? null : null,
      );
    } catch (error) {
      setRecommendations([]);
      setAdvisorSummary(null);
      setRetrievalDebug(null);
      setShowRetrievalDetails(false);
      setError(error instanceof Error ? error.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  }

  function buildRequestBody(requestType: "natural" | "structured") {
    if (requestType === "natural") {
      return { message: naturalLanguageMessage, debug: true };
    }

    return {
      origin,
      days: Number(days),
      budget: Number(budget),
      pass_type: passType,
      terrain_weights: terrainWeights,
    };
  }

  function updateTerrainWeight(preference: Preference, value: string) {
    const weight = Math.min(5, Math.max(0, Number(value)));

    setTerrainWeights((currentWeights) => ({
      ...currentWeights,
      [preference]: weight,
    }));
  }

  return (
    <main className="min-h-screen bg-[#f7faf9] px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="mx-auto max-w-5xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
            Snowtrip Planner
          </p>
          <h1 className="mt-5 text-4xl font-semibold tracking-tight text-slate-950 sm:text-6xl lg:text-7xl">
            Find the right mountain for your next ski trip.
          </h1>
          <p className="mx-auto mt-5 max-w-3xl text-lg leading-8 text-slate-600">
            Plan a ski trip using your pass, budget, terrain preferences, weather,
            and resort knowledge.
          </p>
        </header>

        <section className="mt-12">
          <NaturalSearchPanel
            error={error}
            isLoading={isLoading}
            value={naturalLanguageMessage}
            onChange={setNaturalLanguageMessage}
            onSubmit={handleNaturalSubmit}
          />
        </section>

        {!hasSearched && recommendations.length === 0 ? <EmptyState /> : null}

        {recommendations.length > 0 ? (
          <section aria-live="polite" className="mt-16 space-y-12">
            <div>
              <AdvisorSummary summary={advisorSummary} />
            </div>

            <section>
              <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
                    Resort recommendations
                  </p>
                  <h2 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">
                    Ranked for this trip
                  </h2>
                </div>
                <p className="max-w-xl text-sm leading-6 text-slate-500">
                  Score blends terrain fit, pass value, budget, travel time, and
                  available snow forecast data.
                </p>
              </div>

              <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
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
        ) : null}

        <AdvancedStructuredSearch>
          <PlannerForm
            budget={budget}
            days={days}
            isLoading={isLoading}
            origin={origin}
            passType={passType}
            terrainWeights={terrainWeights}
            onBudgetChange={setBudget}
            onDaysChange={setDays}
            onOriginChange={setOrigin}
            onPassTypeChange={setPassType}
            onSubmit={handleStructuredSubmit}
            onTerrainWeightChange={updateTerrainWeight}
          />
        </AdvancedStructuredSearch>

        {retrievalDebug ? (
          <section className="mt-10">
            <RetrievalDebugPanel
              isVisible={showRetrievalDetails}
              retrievalDebug={retrievalDebug}
              onToggle={() =>
                setShowRetrievalDetails((currentValue) => !currentValue)
              }
            />
          </section>
        ) : null}
      </div>
    </main>
  );
}

function EmptyState() {
  return (
    <p className="mx-auto mt-8 max-w-xl text-center text-sm leading-6 text-slate-500">
      Describe your trip above to receive personalized recommendations.
    </p>
  );
}

function AdvancedStructuredSearch({ children }: { children: ReactNode }) {
  return (
    <section className="mx-auto mt-16 max-w-4xl">
      <details className="group rounded-[1.5rem] border border-slate-200 bg-white/85 shadow-sm shadow-slate-200/70 backdrop-blur">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-5 p-5 marker:hidden sm:p-6">
          <div>
            <p className="text-lg font-semibold tracking-tight text-slate-950">
              Advanced Structured Search
            </p>
            <p className="mt-1 text-sm leading-6 text-slate-500">
              Use exact inputs and terrain weights when you want tighter control.
            </p>
          </div>
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-slate-200 text-xl text-slate-500 transition group-open:rotate-45">
            +
          </span>
        </summary>
        <div className="border-t border-slate-100 p-5 sm:p-6">{children}</div>
      </details>
    </section>
  );
}

function hasTerrainWeight(terrainWeights: TerrainWeights) {
  return Object.values(terrainWeights).some((weight) => weight > 0);
}
