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
  in_season: boolean;
  status_note: string;
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

export type RetrievedChunkDebug = {
  resort_name: string;
  score: number | null;
  source: string;
  text_preview: string;
};

export type RetrievalDebug = {
  mode: "qdrant" | "embedding" | "keyword_fallback";
  query: string;
  top_k: number;
  qdrant_attempted: boolean;
  qdrant_error: string | null;
  qdrant_result_count: number | null;
  retrieved_chunks: RetrievedChunkDebug[];
};

export type ParsedAdvisorResponse = AdvisorResponse & {
  parsed_request: StructuredRequest;
  retrieval_debug?: RetrievalDebug | null;
};
