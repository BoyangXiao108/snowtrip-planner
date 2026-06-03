import type { RetrievalDebug } from "../types";

export function RetrievalDebugPanel({
  retrievalDebug,
  isVisible,
  onToggle,
}: {
  retrievalDebug: RetrievalDebug;
  isVisible: boolean;
  onToggle: () => void;
}) {
  return (
    <section className="mb-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-950">
            Retrieval details
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            {formatMode(retrievalDebug.mode)} retrieval, top {retrievalDebug.top_k}
          </p>
        </div>
        <button
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50 sm:w-auto"
          type="button"
          onClick={onToggle}
          aria-expanded={isVisible}
        >
          {isVisible ? "Hide Retrieval Details" : "Show Retrieval Details"}
        </button>
      </div>

      {isVisible ? (
        <div className="mt-4 space-y-3">
          <dl className="grid gap-3 rounded-md bg-slate-50 p-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="font-medium text-slate-600">Mode</dt>
              <dd className="mt-1 text-slate-950">{formatMode(retrievalDebug.mode)}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-600">Top K</dt>
              <dd className="mt-1 text-slate-950">{retrievalDebug.top_k}</dd>
            </div>
          </dl>

          <div className="grid gap-3">
            {retrievalDebug.retrieved_chunks.map((chunk, index) => (
              <article
                className="rounded-md border border-slate-200 p-3"
                key={`${chunk.resort_name}-${index}`}
              >
                <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
                  <h3 className="font-semibold text-slate-950">{chunk.resort_name}</h3>
                  <p className="text-sm text-slate-600">
                    Score: {formatScore(chunk.score)}
                  </p>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-700">
                  {chunk.text_preview}
                </p>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function formatMode(mode: RetrievalDebug["mode"]) {
  return mode
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatScore(score: number | null) {
  if (score === null) {
    return "n/a";
  }

  return score.toFixed(3);
}
