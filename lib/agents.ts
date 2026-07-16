/** The panel, in the order the orchestrator convenes it. */

export interface AgentProfile {
  id: string;
  name: string;
  remit: string;
}

export const PANEL: AgentProfile[] = [
  {
    id: "ResumeParser",
    name: "Resume Parser",
    remit: "Reads the resume into structured skills and years of experience.",
  },
  {
    id: "JDParser",
    name: "Role Parser",
    remit: "Extracts what the role actually requires, and how clearly it says so.",
  },
  {
    id: "SkillMatch",
    name: "Skill Match",
    remit: "Measures the candidate's coverage of the required skills.",
  },
  {
    id: "Experience",
    name: "Experience",
    remit: "Weighs years served against the band the role asks for.",
  },
  {
    id: "Decision",
    name: "Decision",
    remit: "Weighs the signals, and abstains when the inputs are too weak.",
  },
  {
    id: "Explanation",
    name: "Explanation",
    remit: "States the reasoning in terms a recruiter can argue with.",
  },
];

export type Verdict = "proceed" | "review" | "reject";

export function verdictOf(recommendation: string): Verdict {
  const value = recommendation.toLowerCase();
  if (value.includes("interview")) return "proceed";
  if (value.includes("review")) return "review";
  return "reject";
}
