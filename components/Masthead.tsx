import type { Health } from "@/lib/types";
import styles from "./Masthead.module.css";

const COPY: Record<string, { dot: string; text: string }> = {
  llm: { dot: styles.live, text: "Gemini + rules" },
  rule_based: { dot: styles.offline, text: "Deterministic" },
};

export default function Masthead({ health }: { health: Health | null }) {
  const state = health ? COPY[health.mode] ?? COPY.rule_based : null;

  return (
    <header className={styles.masthead}>
      <div className={styles.mark}>Quorum</div>
      <p className={styles.tagline}>Agentic resume screening</p>

      <div className={styles.mode}>
        <span
          className={`${styles.dot} ${state?.dot ?? ""}`}
          aria-hidden="true"
        />
        <span className="label" title={health?.llm_status}>
          {state?.text ?? "Connecting"}
        </span>
      </div>
    </header>
  );
}
