export type Mode = "llm" | "rule_based" | "mixed";

export type Source = "llm" | "rule_based";

export interface TraceStep {
  agent: string;
  description: string;
  duration_ms: number;
  source: Source | null;
  note: string | null;
}

export interface SkillMatch {
  score: number;
  matched_skills: string[];
  missing_skills: string[];
  extra_skills: string[];
  coverage: string;
}

export interface ExperienceVerdict {
  score: number;
  status: string;
  reason: string;
}

export interface ScreeningResult {
  match_score: number;
  recommendation: string;
  requires_human: boolean;
  confidence: number;
  reasoning_summary: string;
  mode: Mode;
  final_score: number;
  /** False when the panel declined to score — an abstention, not a zero. */
  scored: boolean;
  candidate: {
    skills: string[];
    experience_years: number;
    projects: string[];
    source: Source;
  };
  role: {
    required_skills: string[];
    experience_required: { min: number; max: number | null } | null;
    clarity: "clear" | "vague";
    source: Source;
  };
  skill_match: SkillMatch;
  experience: ExperienceVerdict;
  trace: TraceStep[];
}

export interface Health {
  status: string;
  mode: Mode;
  llm_status: string;
  model: string | null;
}
