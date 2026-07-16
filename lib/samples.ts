/** Fixtures served from /public/samples so the demo is usable on a cold visit. */

export interface SampleCandidate {
  id: string;
  name: string;
  role: string;
  file: string;
}

export interface SampleRole {
  id: string;
  title: string;
  detail: string;
  file: string;
}

export const SAMPLE_CANDIDATES: SampleCandidate[] = [
  {
    id: "priya",
    name: "Priya Sharma",
    role: "Senior backend engineer, 3 yrs",
    file: "/samples/resume_01_priya_sharma.pdf",
  },
  {
    id: "rahul",
    name: "Rahul Verma",
    role: "Data analyst moving to backend, 2 yrs",
    file: "/samples/resume_02_rahul_verma.pdf",
  },
  {
    id: "ananya",
    name: "Ananya Patel",
    role: "Frontend engineer",
    file: "/samples/resume_03_ananya_patel.pdf",
  },
  {
    id: "vikram",
    name: "Vikram Singh",
    role: "Career switcher, bootcamp",
    file: "/samples/resume_04_vikram_singh.pdf",
  },
];

export const SAMPLE_ROLES: SampleRole[] = [
  {
    id: "backend",
    title: "Backend Engineer — Python",
    detail: "Standard, well-specified. 2–4 yrs",
    file: "/samples/jd_01_backend_python_standard.txt",
  },
  {
    id: "fintech",
    title: "Senior Backend — Fintech",
    detail: "Strict and senior. 4–7 yrs",
    file: "/samples/jd_02_senior_fintech_strict.txt",
  },
  {
    id: "junior",
    title: "Junior Developer",
    detail: "Flexible, entry level",
    file: "/samples/jd_03_junior_flexible.txt",
  },
  {
    id: "vague",
    title: "Software Developer",
    detail: "Deliberately vague — expect an escalation",
    file: "/samples/jd_04_vague_ambiguous.txt",
  },
];

export async function loadSampleFile(path: string): Promise<File> {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Could not load the sample (${response.status})`);
  const blob = await response.blob();
  return new File([blob], path.split("/").pop() ?? "sample.pdf", {
    type: "application/pdf",
  });
}

export async function loadSampleText(path: string): Promise<string> {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Could not load the sample (${response.status})`);
  return response.text();
}
