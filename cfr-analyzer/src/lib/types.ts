export interface Agency {
  name: string;
  word_count: number;
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

export interface Correction {
  agency_name: string;
  title: string;
  corrective_action: string;
  error_corrected: string;
  fr_citation: string;
}

export interface SubAgencyRatio {
  name: string;
  sub_agencies: number;
  word_count: number;
  sub_agencies_per_1000_words: number;
}