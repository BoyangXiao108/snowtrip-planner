import type { FormEvent } from "react";

export function NaturalSearchPanel({
  error,
  isLoading,
  value,
  onChange,
  onSubmit,
}: {
  error: string | null;
  isLoading: boolean;
  value: string;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form
      className="mx-auto max-w-5xl rounded-[1.75rem] border border-white/80 bg-white/90 p-4 shadow-xl shadow-slate-200/60 backdrop-blur sm:p-6"
      onSubmit={onSubmit}
    >
      <label className="block">
        <span className="sr-only">Describe your ski trip</span>
        <textarea
          className="min-h-44 w-full resize-y rounded-2xl border border-slate-200 bg-slate-50/70 px-5 py-4 text-base leading-7 text-slate-950 outline-none ring-teal-600 placeholder:text-slate-400 focus:bg-white focus:ring-2 sm:text-lg"
          placeholder="Example: I have an Epic Pass, leaving from Boston for 3 days, budget $1500, and I care most about trees and powder."
          value={value}
          onChange={(event) => onChange(event.target.value)}
          required
        />
      </label>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm leading-6 text-slate-500">
          Include your pass, origin, trip length, budget, and terrain style.
        </p>
        <button
          type="submit"
          disabled={isLoading}
          className="inline-flex min-h-12 items-center justify-center rounded-2xl bg-teal-700 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-teal-900/15 transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400 sm:min-w-44"
        >
          {isLoading ? "Building your trip advice..." : "Plan my ski trip"}
        </button>
      </div>

      {error ? (
        <p className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      ) : null}
    </form>
  );
}
