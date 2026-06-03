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
    <div className={featured ? "rounded-md bg-slate-50 p-3" : undefined}>
      <dt className="text-xs font-medium uppercase text-slate-500">{label}</dt>
      <dd
        className={
          featured
            ? "mt-1 text-lg font-semibold text-slate-950"
            : "mt-1 text-sm font-semibold text-slate-950"
        }
      >
        {value}
      </dd>
    </div>
  );
}
