"use client";

import { FormEvent, useState } from "react";

import { AdvisorSummary } from "../components/AdvisorSummary";
import { ParsedRequestPanel } from "../components/ParsedRequestPanel";
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
  InputMode,
  ParsedAdvisorResponse,
  PassType,
  Preference,
  Recommendation,
  RetrievalDebug,
  StructuredRequest,
  TerrainWeights,
} from "../types";

export default function Home() {
  const [mode, setMode] = useState<InputMode>("structured");
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
  const [parsedRequest, setParsedRequest] = useState<StructuredRequest | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [advisorSummary, setAdvisorSummary] = useState<string | null>(null);
  const [retrievalDebug, setRetrievalDebug] = useState<RetrievalDebug | null>(null);
  const [showRetrievalDetails, setShowRetrievalDetails] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setAdvisorSummary(null);
    setParsedRequest(null);
    setRetrievalDebug(null);
    setShowRetrievalDetails(false);

    if (mode === "structured" && !hasTerrainWeight(terrainWeights)) {
      setIsLoading(false);
      setError("Set at least one terrain weight above 0.");
      return;
    }

    if (mode === "natural" && naturalLanguageMessage.trim().length === 0) {
      setIsLoading(false);
      setError("Enter a trip request.");
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/${mode === "structured" ? "advisor" : "advisor/parse"}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(buildRequestBody()),
        },
      );

      if (!response.ok) {
        throw new Error("Unable to get recommendations. Check your inputs and try again.");
      }

      const data = (await response.json()) as AdvisorResponse | ParsedAdvisorResponse;
      setRecommendations(data.recommendations);
      setAdvisorSummary(data.advisor_summary?.trim() || null);
      setParsedRequest("parsed_request" in data ? data.parsed_request : null);
      setRetrievalDebug(
        "retrieval_debug" in data ? data.retrieval_debug ?? null : null,
      );
    } catch (error) {
      setRecommendations([]);
      setAdvisorSummary(null);
      setParsedRequest(null);
      setRetrievalDebug(null);
      setShowRetrievalDetails(false);
      setError(error instanceof Error ? error.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  }

  function buildRequestBody() {
    if (mode === "natural") {
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
          <PlannerForm
            budget={budget}
            days={days}
            error={error}
            isLoading={isLoading}
            mode={mode}
            naturalLanguageMessage={naturalLanguageMessage}
            origin={origin}
            passType={passType}
            terrainWeights={terrainWeights}
            onBudgetChange={setBudget}
            onDaysChange={setDays}
            onModeChange={setMode}
            onNaturalLanguageMessageChange={setNaturalLanguageMessage}
            onOriginChange={setOrigin}
            onPassTypeChange={setPassType}
            onSubmit={handleSubmit}
            onTerrainWeightChange={updateTerrainWeight}
          />

          <section aria-live="polite">
            {recommendations.length === 0 && !error ? (
              <EmptyState />
            ) : null}

            {recommendations.length > 0 ? (
              <AdvisorSummary summary={advisorSummary} />
            ) : null}

            {parsedRequest ? <ParsedRequestPanel parsedRequest={parsedRequest} /> : null}

            {retrievalDebug ? (
              <RetrievalDebugPanel
                isVisible={showRetrievalDetails}
                retrievalDebug={retrievalDebug}
                onToggle={() =>
                  setShowRetrievalDetails((currentValue) => !currentValue)
                }
              />
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

function EmptyState() {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">Ready when you are.</h2>
      <p className="mt-2 max-w-xl text-sm leading-6 text-slate-700">
        Choose your pass, budget, trip length, and terrain weights, or describe
        the trip in natural language. Snowtrip Planner will rank three resorts
        that fit the trip you have in mind.
      </p>
    </div>
  );
}

function hasTerrainWeight(terrainWeights: TerrainWeights) {
  return Object.values(terrainWeights).some((weight) => weight > 0);
}
