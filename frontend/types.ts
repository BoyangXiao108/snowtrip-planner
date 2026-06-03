export type PassType = "Epic" | "Ikon" | "None";
export type Preference = "trees" | "park" | "groomers" | "powder";
export type InputMode = "structured" | "natural";

export type Weather = {
  temperature_f: number | null;
  wind_speed_mph: number | null;
  snowfall_inches: number | null;
  snowfall_inches_today: number | null;
  snowfall_inches_next_3_days: number | null;
};

export type Recommendation = {
  name: string;
  state: string;
  pass_type: PassType;
  drive_hours: number;
  estimated_total_cost: number;
  total_score: number;
  snow_score: number | null;
  reason: string;
  weather: Weather | null;
};

export type TerrainWeights = Record<Preference, number>;

export type StructuredRequest = {
  origin: string;
  days: number;
  budget: number;
  pass_type: PassType;
  terrain_weights: TerrainWeights;
};

export type AdvisorResponse = {
  recommendations: Recommendation[];
  advisor_summary?: string | null;
};

export type ParsedAdvisorResponse = AdvisorResponse & {
  parsed_request: StructuredRequest;
};
