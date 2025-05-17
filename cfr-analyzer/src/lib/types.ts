export interface Agency {
  name: string;
  short_name: string;
  slug: string;
  cfr_references: Array<{ title: number; chapter?: string }>;
  sub_agencies: number;
  word_count: number;
}

export interface Correction {
  id: number;
  agency_name: string;
  title: number;
  correction_id: number;
  corrective_action: string;
  error_corrected: string;
  error_occurred: string;
  fr_citation: string;
  last_modified: string;
}

export interface WordCountStats {
  total_words: number;
  mean_words: number;
  median_words: number;
  std_dev: number;
}

export interface CorrectionMetric {
  name: string;
  correction_count: number;
}

export interface CorrectionRate {
  name: string;
  word_count: number;
  correction_count: number;
  corrections_per_1000_words: number;
}

export interface SubAgencyRatio {
  name: string;
  sub_agencies: number;
  word_count: number;
  sub_agencies_per_1000_words: number;
}