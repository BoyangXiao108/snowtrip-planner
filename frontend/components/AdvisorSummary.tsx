export function AdvisorSummary({ summary }: { summary: string | null }) {
  return (
    <section className="mb-4 rounded-lg border border-teal-100 bg-teal-50 p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-teal-950">Trip advice</h2>
      <p className="mt-2 text-sm leading-6 text-teal-950">
        {summary ??
          "Advisor summary is unavailable, but your ranked resort recommendations are ready below."}
      </p>
    </section>
  );
}
