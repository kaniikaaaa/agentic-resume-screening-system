"use client";

import { useEffect, useRef, useState } from "react";
import Intake from "@/components/Intake";
import Masthead from "@/components/Masthead";
import Trace from "@/components/Trace";
import Verdict from "@/components/Verdict";
import type { Health, ScreeningResult } from "@/lib/types";
import styles from "./page.module.css";

export default function Page() {
  const [health, setHealth] = useState<Health | null>(null);
  const [resume, setResume] = useState<File | null>(null);
  const [jd, setJd] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/py/health")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  async function submit() {
    if (!resume) return;

    setBusy(true);
    setError(null);
    setResult(null);

    // On mobile the panel sits below the fold; the deliberation is the
    // feedback, so bring it into view rather than leaving a dead button.
    panelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });

    const body = new FormData();
    body.append("resume", resume);
    body.append("job_description", jd);

    try {
      const response = await fetch("/api/py/screen", { method: "POST", body });
      const payload = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          payload?.detail ?? `The panel could not sit (${response.status}).`
        );
      }

      setResult(payload as ScreeningResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setResume(null);
    setJd("");
    setResult(null);
    setError(null);
  }

  return (
    <main className={styles.shell}>
      <Masthead health={health} />

      <div className={styles.deck}>
        <div className={styles.left}>
          <Intake
            resume={resume}
            jd={jd}
            busy={busy}
            error={error}
            onResume={setResume}
            onJd={setJd}
            onSubmit={submit}
            onReset={reset}
          />
        </div>

        <div className={styles.right} ref={panelRef}>
          {result ? (
            <Verdict result={result} />
          ) : busy ? (
            <div className={styles.busy}>
              <div className={styles.busyHead}>
                <span className="label">In session</span>
              </div>
              <p className={styles.busyNote}>
                Each agent is reading its own part of the file. Timings appear as
                the record closes.
              </p>
              <Trace steps={null} active />
            </div>
          ) : (
            <div className={styles.idle}>
              <div className={styles.idleHead}>
                <span className="label">No case open</span>
              </div>

              <p className={styles.statement}>
                A resume and a role go in. Six agents read them separately, and
                the panel comes back with a call it can defend.
              </p>
              <p className={styles.statementSub}>
                Every score below is traceable to the agent that produced it. When
                the inputs are too thin to judge — a role that names no
                technology, a resume it could not read — the panel abstains and
                says so, rather than inventing a number.
              </p>

              <div className={styles.rosterHead}>
                <span className="label">The panel</span>
              </div>
              <Trace steps={null} />
            </div>
          )}
        </div>
      </div>

      <footer className={styles.colophon}>
        <span className="label">Quorum</span>
        <a className={`${styles.link} ${styles.linkItem}`} href="/api/py/docs">
          API reference
        </a>
        <span className={styles.colophonNote}>
          {health?.mode === "llm"
            ? "Gemini extraction with a deterministic fallback."
            : "Running deterministically — set GEMINI_API_KEY for semantic extraction."}
        </span>
      </footer>
    </main>
  );
}
