export function Metric({
  label,
  value,
  featured = false,
}: {
  label: string;
  value: string;
  featured?: boolean;
}) {
  return (
    <div
      className={
        featured
          ? "rounded-xl border border-slate-100 bg-slate-50/80 p-3"
          : undefined
      }
    >
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </dt>
      <dd
        className={
          featured
            ? "mt-1 text-base font-semibold text-slate-950"
            : "mt-1 text-sm font-semibold text-slate-950"
        }
      >
        {value}
      </dd>
    </div>
  );
}
