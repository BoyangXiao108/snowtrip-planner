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
    <section className="mb-4 rounded-2xl border border-slate-200 bg-slate-950/95 p-4 text-slate-100 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-mono text-sm font-semibold uppercase tracking-wide text-slate-200">
            Retrieval details
          </h2>
          <p className="mt-1 font-mono text-xs text-slate-400">
            {formatMode(retrievalDebug.mode)} retrieval, top {retrievalDebug.top_k}
          </p>
        </div>
        <button
          className="w-full rounded-lg border border-slate-700 px-3 py-2 font-mono text-xs font-medium text-slate-100 hover:bg-slate-800 sm:w-auto"
          type="button"
          onClick={onToggle}
          aria-expanded={isVisible}
        >
          {isVisible ? "Hide Retrieval Details" : "Show Retrieval Details"}
        </button>
      </div>

      {isVisible ? (
        <div className="mt-4 space-y-3">
          <dl className="grid gap-3 rounded-xl border border-slate-800 bg-slate-900 p-3 font-mono text-xs sm:grid-cols-2">
            <div>
              <dt className="font-medium text-slate-500">Mode</dt>
              <dd className="mt-1 text-slate-100">{formatMode(retrievalDebug.mode)}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Top K</dt>
              <dd className="mt-1 text-slate-100">{retrievalDebug.top_k}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Qdrant Attempted</dt>
              <dd className="mt-1 text-slate-100">
                {retrievalDebug.qdrant_attempted ? "Yes" : "No"}
              </dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Qdrant Results</dt>
              <dd className="mt-1 text-slate-100">
                {retrievalDebug.qdrant_result_count ?? "n/a"}
              </dd>
            </div>
          </dl>

          {retrievalDebug.qdrant_error ? (
            <p className="rounded-xl border border-amber-700/50 bg-amber-950/50 p-3 font-mono text-xs leading-6 text-amber-100">
              {retrievalDebug.qdrant_error}
            </p>
          ) : null}

          <div className="grid gap-3">
            {retrievalDebug.retrieved_chunks.map((chunk, index) => (
              <article
                className="rounded-xl border border-slate-800 bg-slate-900 p-3"
                key={`${chunk.resort_name}-${index}`}
              >
                <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
                  <h3 className="font-mono text-sm font-semibold text-slate-100">
                    {chunk.resort_name}
                  </h3>
                  <p className="font-mono text-xs text-slate-400">
                    Score: {formatScore(chunk.score)}
                  </p>
                </div>
                <p className="mt-2 font-mono text-xs leading-6 text-slate-300">
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
