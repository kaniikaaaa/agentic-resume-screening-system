import { PANEL } from "@/lib/agents";
import type { TraceStep } from "@/lib/types";
import styles from "./Trace.module.css";

/**
 * The deliberation record. While the request is in flight every agent shows as
 * pending — the pipeline runs server-side in one round trip, so claiming
 * per-agent progress before the response lands would be theatre. Real timings
 * replace it on arrival.
 */
export default function Trace({
  steps,
  active = false,
}: {
  steps: TraceStep[] | null;
  /** True only while a request is in flight; idle rows must not imply work. */
  active?: boolean;
}) {
  const rows = PANEL.map((agent, i) => ({
    agent,
    step: steps?.find((s) => s.agent === agent.id) ?? null,
    i,
  }));

  return (
    <div className={styles.trace}>
      {rows.map(({ agent, step, i }) => (
        <div key={agent.id}>
          <div
            className={`${styles.step} ${
              step ? styles.done : active ? styles.running : styles.idle
            } ${step?.status === "skipped" ? styles.skipped : ""}`}
            style={{ "--i": i } as React.CSSProperties}
          >
            <span className={styles.name}>{agent.name}</span>
            <span className={styles.remit}>{agent.remit}</span>

            <span className={styles.meta}>
              {step?.source && (
                <span
                  className={`${styles.badge} ${
                    step.source === "llm" ? styles.badgeLlm : ""
                  }`}
                >
                  {step.source === "llm" ? "Gemini" : "Rules"}
                </span>
              )}
              <span className={`num ${styles.ms}`}>
                {!step
                  ? "—"
                  : step.status === "skipped"
                    ? "not run"
                    : `${step.duration_ms} ms`}
              </span>
            </span>
          </div>

          {step?.note && <p className={styles.note}>{step.note}</p>}
        </div>
      ))}
    </div>
  );
}
