"use client";

import { FormEvent, useState } from "react";

import { AdvisorSummary } from "../components/AdvisorSummary";
import { NaturalSearchPanel } from "../components/NaturalSearchPanel";
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
  ParsedAdvisorResponse,
  PassType,
  Preference,
  Recommendation,
  RetrievalDebug,
  StructuredRequest,
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
  const [parsedRequest, setParsedRequest] = useState<StructuredRequest | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [advisorSummary, setAdvisorSummary] = useState<string | null>(null);
  const [retrievalDebug, setRetrievalDebug] = useState<RetrievalDebug | null>(null);
  const [showRetrievalDetails, setShowRetrievalDetails] = useState(false);
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
    setIsLoading(true);
    setError(null);
    setAdvisorSummary(null);
    setParsedRequest(null);
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
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,#dfeeed,transparent_34%),linear-gradient(180deg,#f8fbfb_0%,#eef4f3_100%)] px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="mx-auto max-w-4xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
            Snowtrip Planner
          </p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950 sm:text-6xl">
            Plan a better ski trip in one sentence.
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-slate-600">
            Plan a ski trip using your pass, budget, terrain preferences, weather,
            and resort knowledge.
          </p>
        </header>

        <section className="mt-10">
          <NaturalSearchPanel
            error={error}
            isLoading={isLoading}
            value={naturalLanguageMessage}
            onChange={setNaturalLanguageMessage}
            onSubmit={handleNaturalSubmit}
          />
        </section>

        <section aria-live="polite" className="mt-10">
          {recommendations.length === 0 && !error ? <EmptyState /> : null}

          {recommendations.length > 0 ? (
            <div className="space-y-6">
              <AdvisorSummary summary={advisorSummary} />

              {parsedRequest ? (
                <div className="mx-auto max-w-5xl">
                  <ParsedRequestPanel parsedRequest={parsedRequest} />
                </div>
              ) : null}

              <div className="grid gap-5 lg:grid-cols-3">
                {recommendations.map((recommendation, index) => (
                  <RecommendationCard
                    key={`${recommendation.name}-${recommendation.state}`}
                    recommendation={recommendation}
                    rank={index + 1}
                  />
                ))}
              </div>

              {retrievalDebug ? (
                <RetrievalDebugPanel
                  isVisible={showRetrievalDetails}
                  retrievalDebug={retrievalDebug}
                  onToggle={() =>
                    setShowRetrievalDetails((currentValue) => !currentValue)
                  }
                />
              ) : null}
            </div>
          ) : null}
        </section>

        <section className="mt-10 grid gap-6 lg:grid-cols-[1fr_minmax(360px,460px)_1fr]">
          <div className="hidden lg:block" />
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
          <div className="hidden lg:block" />
        </section>
      </div>
    </main>
  );
}

function EmptyState() {
  return (
    <div className="mx-auto max-w-4xl rounded-[1.5rem] border border-dashed border-slate-300 bg-white/50 p-8 text-center">
      <h2 className="text-xl font-semibold tracking-tight text-slate-950">
        Your trip plan will appear here.
      </h2>
      <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-slate-600">
        Describe where you are leaving from, how long you are going, your budget,
        your pass, and what kind of terrain you want. Your trip advice and ranked
        recommendations will appear here.
      </p>
    </div>
  );
}

function hasTerrainWeight(terrainWeights: TerrainWeights) {
  return Object.values(terrainWeights).some((weight) => weight > 0);
}
