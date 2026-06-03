import type { StructuredRequest } from "../types";
import { Metric } from "./Metric";

export function ParsedRequestPanel({
  parsedRequest,
}: {
  parsedRequest: StructuredRequest;
}) {
  return (
    <section className="mb-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-sm font-semibold uppercase text-slate-500">
        Parsed request
      </h2>
      <dl className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Origin" value={parsedRequest.origin} />
        <Metric label="Days" value={`${parsedRequest.days}`} />
        <Metric label="Budget" value={`$${parsedRequest.budget}`} />
        <Metric label="Pass" value={parsedRequest.pass_type} />
      </dl>
      <div className="mt-3 rounded-md bg-slate-50 p-3">
        <p className="text-xs font-medium uppercase text-slate-500">
          Terrain weights
        </p>
        <p className="mt-1 text-sm font-semibold text-slate-950">
          Trees {parsedRequest.terrain_weights.trees} · Powder{" "}
          {parsedRequest.terrain_weights.powder} · Groomers{" "}
          {parsedRequest.terrain_weights.groomers} · Park{" "}
          {parsedRequest.terrain_weights.park}
        </p>
      </div>
    </section>
  );
}
