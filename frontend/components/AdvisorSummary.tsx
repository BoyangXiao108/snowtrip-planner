export function AdvisorSummary({ summary }: { summary: string | null }) {
  const lines = parseSummary(summary);

  return (
    <section className="mx-auto max-w-5xl rounded-[1.5rem] border border-teal-100 bg-teal-50/80 p-5 shadow-sm shadow-teal-900/5 sm:p-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
          Trip advice
        </p>
        <h2 className="mt-1 text-xl font-semibold tracking-tight text-teal-950">
          Your recommended plan
        </h2>
      </div>

      {lines.length > 0 ? (
        <dl className="mt-5 grid gap-3 md:grid-cols-2">
          {lines.map((line) => (
            <div
              key={line.label}
              className="rounded-xl border border-teal-100 bg-white/70 p-3"
            >
              <dt className="text-xs font-semibold uppercase tracking-wide text-teal-700">
                {line.label}
              </dt>
              <dd className="mt-1 text-sm leading-6 text-slate-800">{line.value}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="mt-3 text-sm leading-6 text-teal-950">
          Advisor summary is unavailable, but your ranked resort recommendations
          are ready below.
        </p>
      )}
    </section>
  );
}

function parseSummary(summary: string | null) {
  if (!summary) {
    return [];
  }

  return summary
    .split("\n")
    .map((line) => {
      const [label, ...valueParts] = line.split(":");

      return {
        label: label.trim(),
        value: valueParts.join(":").trim(),
      };
    })
    .filter((line) => line.label && line.value);
}
