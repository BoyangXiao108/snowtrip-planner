import type { Preference, TerrainWeights } from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export const TERRAIN_OPTIONS: { value: Preference; label: string }[] = [
  { value: "trees", label: "Trees" },
  { value: "powder", label: "Powder" },
  { value: "groomers", label: "Groomers" },
  { value: "park", label: "Park" },
];

export const DEFAULT_TERRAIN_WEIGHTS: TerrainWeights = {
  trees: 5,
  powder: 4,
  groomers: 2,
  park: 0,
};

export const DEFAULT_NATURAL_LANGUAGE_MESSAGE =
  "I have an Epic Pass, leaving from Boston for 3 days, budget $1500, and I care most about trees and powder.";
