import type { FormEvent, ReactNode } from "react";

import { TERRAIN_OPTIONS } from "../constants";
import type { PassType, Preference, TerrainWeights } from "../types";

export function PlannerForm({
  budget,
  days,
  isLoading,
  origin,
  passType,
  terrainWeights,
  onBudgetChange,
  onDaysChange,
  onOriginChange,
  onPassTypeChange,
  onSubmit,
  onTerrainWeightChange,
}: {
  budget: string;
  days: string;
  isLoading: boolean;
  origin: string;
  passType: PassType;
  terrainWeights: TerrainWeights;
  onBudgetChange: (value: string) => void;
  onDaysChange: (value: string) => void;
  onOriginChange: (value: string) => void;
  onPassTypeChange: (value: PassType) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onTerrainWeightChange: (preference: Preference, value: string) => void;
}) {
  return (
    <form onSubmit={onSubmit}>
      <div className="space-y-6">
        <div>
          <p className="text-base font-semibold tracking-tight text-slate-950">
            Exact inputs
          </p>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Prefer exact inputs? Tune the same recommendation engine manually.
          </p>
        </div>

        <StructuredFields
          budget={budget}
          days={days}
          origin={origin}
          passType={passType}
          terrainWeights={terrainWeights}
          onBudgetChange={onBudgetChange}
          onDaysChange={onDaysChange}
          onOriginChange={onOriginChange}
          onPassTypeChange={onPassTypeChange}
          onTerrainWeightChange={onTerrainWeightChange}
        />

        <button
          type="submit"
          disabled={isLoading}
          className="w-full rounded-2xl border border-teal-700 bg-white px-4 py-3 font-semibold text-teal-800 shadow-sm transition hover:-translate-y-0.5 hover:bg-teal-50 disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
        >
          {isLoading ? "Building your trip advice..." : "Search with structured inputs"}
        </button>
      </div>
    </form>
  );
}

function StructuredFields({
  budget,
  days,
  origin,
  passType,
  terrainWeights,
  onBudgetChange,
  onDaysChange,
  onOriginChange,
  onPassTypeChange,
  onTerrainWeightChange,
}: {
  budget: string;
  days: string;
  origin: string;
  passType: PassType;
  terrainWeights: TerrainWeights;
  onBudgetChange: (value: string) => void;
  onDaysChange: (value: string) => void;
  onOriginChange: (value: string) => void;
  onPassTypeChange: (value: PassType) => void;
  onTerrainWeightChange: (preference: Preference, value: string) => void;
}) {
  return (
    <>
      <Field label="Origin">
        <input
          id="origin"
          className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-slate-950 shadow-sm outline-none ring-teal-600 focus:ring-2"
          value={origin}
          onChange={(event) => onOriginChange(event.target.value)}
          required
        />
      </Field>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-2">
        <Field label="Days">
          <input
            id="days"
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-slate-950 shadow-sm outline-none ring-teal-600 focus:ring-2"
            type="number"
            min="1"
            value={days}
            onChange={(event) => onDaysChange(event.target.value)}
            required
          />
        </Field>

        <Field label="Budget">
          <input
            id="budget"
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-slate-950 shadow-sm outline-none ring-teal-600 focus:ring-2"
            type="number"
            min="1"
            value={budget}
            onChange={(event) => onBudgetChange(event.target.value)}
            required
          />
        </Field>
      </div>

      <Field label="Pass Type">
        <select
          id="pass-type"
          className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-slate-950 shadow-sm outline-none ring-teal-600 focus:ring-2"
          value={passType}
          onChange={(event) => onPassTypeChange(event.target.value as PassType)}
        >
          <option value="Epic">Epic</option>
          <option value="Ikon">Ikon</option>
          <option value="None">None</option>
        </select>
      </Field>

      <TerrainWeightControls
        terrainWeights={terrainWeights}
        onChange={onTerrainWeightChange}
      />
    </>
  );
}

function TerrainWeightControls({
  terrainWeights,
  onChange,
}: {
  terrainWeights: TerrainWeights;
  onChange: (preference: Preference, value: string) => void;
}) {
  return (
    <fieldset>
      <legend className="mb-3 text-sm font-medium text-slate-800">
        Terrain Weights
      </legend>
      <div className="space-y-3">
        {TERRAIN_OPTIONS.map((option) => (
          <div
            key={option.value}
            className="rounded-xl border border-slate-200 bg-slate-50/80 p-3"
          >
            <div className="flex items-center justify-between gap-3">
              <label
                htmlFor={`terrain-${option.value}`}
                className="text-sm font-medium text-slate-900"
              >
                {option.label}
              </label>
              <input
                id={`terrain-${option.value}`}
                type="number"
                min="0"
                max="5"
                className="w-16 shrink-0 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-center text-sm font-semibold text-slate-950 outline-none ring-teal-600 focus:ring-2"
                value={terrainWeights[option.value]}
                onChange={(event) => onChange(option.value, event.target.value)}
              />
            </div>
            <input
              aria-label={`${option.label} weight`}
              type="range"
              min="0"
              max="5"
              step="1"
              className="mt-3 w-full accent-teal-700"
              value={terrainWeights[option.value]}
              onChange={(event) => onChange(option.value, event.target.value)}
            />
          </div>
        ))}
      </div>
    </fieldset>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block text-sm font-medium text-slate-800">
      <span className="mb-2 block">{label}</span>
      {children}
    </label>
  );
}
