export interface Device {
  k_number: string;
  device_name: string | null;
  applicant: string | null;
  decision_date: string | null;
}

export interface PredicateLink {
  predicate_k: string;
  page: number | null;
  method: "regex" | "llm";
}

export interface SupportedCell {
  row: string;
  value: string;
  supported: true;
  chunk_id: string;
  k_number: string;
  page: number;
  evidence: string;
}

export interface UnsupportedCell {
  row: string;
  value: string;
  supported: false;
}

export type Cell = SupportedCell | UnsupportedCell;

export interface Comparison {
  predicate_k: string;
  cells: Cell[];
}
