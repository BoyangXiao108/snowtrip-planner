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
      className="mx-auto max-w-6xl rounded-[2rem] border border-slate-200 bg-white p-4 shadow-xl shadow-slate-200/70 sm:p-6 lg:p-7"
      onSubmit={onSubmit}
    >
      <label className="block">
        <span className="sr-only">Describe your ski trip</span>
        <textarea
          className="min-h-36 w-full resize-y rounded-[1.5rem] border border-slate-200 bg-slate-50/80 px-5 py-5 text-base leading-7 text-slate-950 outline-none ring-teal-600 transition placeholder:text-slate-400 focus:border-teal-700 focus:bg-white focus:ring-2 sm:min-h-44 sm:px-6 sm:text-lg"
          placeholder="Example: I have an Epic Pass, leaving Boston for 3 days, budget $1500, and I care most about trees and powder."
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
          className="inline-flex min-h-14 w-full items-center justify-center rounded-2xl bg-teal-700 px-7 py-3 text-sm font-semibold text-white shadow-lg shadow-teal-900/15 transition hover:-translate-y-0.5 hover:bg-teal-800 hover:shadow-xl disabled:cursor-not-allowed disabled:bg-slate-400 disabled:shadow-none sm:min-w-48 sm:w-auto"
        >
          {isLoading ? "Building your trip advice..." : "Plan My Ski Trip"}
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
