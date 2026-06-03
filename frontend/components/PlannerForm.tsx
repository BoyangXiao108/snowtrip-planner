import type { FormEvent, ReactNode } from "react";

import { TERRAIN_OPTIONS } from "../constants";
import type { InputMode, PassType, Preference, TerrainWeights } from "../types";
import { NaturalLanguageInput } from "./NaturalLanguageInput";

export function PlannerForm({
  budget,
  days,
  error,
  isLoading,
  mode,
  naturalLanguageMessage,
  origin,
  passType,
  terrainWeights,
  onBudgetChange,
  onDaysChange,
  onModeChange,
  onNaturalLanguageMessageChange,
  onOriginChange,
  onPassTypeChange,
  onSubmit,
  onTerrainWeightChange,
}: {
  budget: string;
  days: string;
  error: string | null;
  isLoading: boolean;
  mode: InputMode;
  naturalLanguageMessage: string;
  origin: string;
  passType: PassType;
  terrainWeights: TerrainWeights;
  onBudgetChange: (value: string) => void;
  onDaysChange: (value: string) => void;
  onModeChange: (mode: InputMode) => void;
  onNaturalLanguageMessageChange: (value: string) => void;
  onOriginChange: (value: string) => void;
  onPassTypeChange: (value: PassType) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onTerrainWeightChange: (preference: Preference, value: string) => void;
}) {
  return (
    <form
      onSubmit={onSubmit}
      className="h-fit rounded-2xl border border-white/70 bg-white/85 p-5 shadow-sm shadow-slate-200/80 backdrop-blur sm:p-6"
    >
      <div className="space-y-6">
        <div>
          <p className="text-sm font-semibold text-slate-950">Plan your trip</p>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Start with natural language, or switch to structured controls.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1">
          <ModeButton active={mode === "natural"} onClick={() => onModeChange("natural")}>
            Natural Language
          </ModeButton>
          <ModeButton active={mode === "structured"} onClick={() => onModeChange("structured")}>
            Structured Form
          </ModeButton>
        </div>

        {mode === "structured" ? (
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
        ) : (
          <NaturalLanguageInput
            value={naturalLanguageMessage}
            onChange={onNaturalLanguageMessageChange}
          />
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full rounded-xl bg-teal-700 px-4 py-3 font-semibold text-white shadow-sm shadow-teal-900/10 transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isLoading ? "Building your trip advice..." : "Plan my trip"}
        </button>
        {isLoading ? (
          <p className="text-center text-sm text-slate-600">
            Building your trip advice...
          </p>
        ) : null}
        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}
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

function ModeButton({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={
        active
          ? "rounded-lg bg-white px-3 py-2 text-sm font-semibold text-teal-800 shadow-sm"
          : "rounded-lg px-3 py-2 text-sm font-semibold text-slate-600 transition hover:text-slate-950"
      }
      onClick={onClick}
    >
      {children}
    </button>
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
