"use client";

import { useState } from "react";
import { verdictOf } from "@/lib/agents";
import type { ScreeningResult } from "@/lib/types";
import Trace from "./Trace";
import styles from "./Verdict.module.css";

/**
 * Mirrors DecisionAgent's cuts, so the rail shows why the call went as it did.
 *
 * The review band opens at NEAR_MISS_THRESHOLD, not REVIEW_THRESHOLD: a 62
 * scores below 65 but is still held for a recruiter, so 60 is where the
 * outcome actually changes. Drawing the line at 65 would put the marker in the
 * reject band on a case the panel did not reject.
 */
const REVIEW_AT = 60;
const INTERVIEW_AT = 85;

const ZONES = [
  { key: "reject", from: 0, to: REVIEW_AT },
  { key: "review", from: REVIEW_AT, to: INTERVIEW_AT },
  { key: "interview", from: INTERVIEW_AT, to: 100 },
] as const;

/**
 * How far the score sits from the line above it.
 *
 * A bare "64" next to a "65 review" tick reads as a rounding artefact. Saying
 * the distance out loud is what makes a near miss legible — and a near miss is
 * exactly the case a recruiter would want to look at.
 */
function distanceToNextLine(score: number): string | null {
  const line = score < REVIEW_AT ? REVIEW_AT : score < INTERVIEW_AT ? INTERVIEW_AT : null;
  if (line === null) return null;

  const gap = line - score;
  if (gap > 12) return null;

  const points = gap < 1 ? gap.toFixed(1) : Math.round(gap);
  const name = line === REVIEW_AT ? "review" : "interview";
  return `${points} ${gap === 1 ? "point" : "points"} below the ${name} line`;
}

export default function Verdict({ result }: { result: ScreeningResult }) {
  const [showRaw, setShowRaw] = useState(false);
  const tone = verdictOf(result.recommendation);
  const { skill_match: skills, experience, candidate, role } = result;

  return (
    <div className={styles.verdict}>
      <section className={`${styles.block} ${styles.ruling} ${styles[tone]}`}>
        <span className="label">The ruling</span>
        <h2 className={styles.call}>{result.recommendation}</h2>
        {result.requires_human ? (
          <span className={styles.flag}>
            <span className={styles.flagDot} aria-hidden="true" />
            Held for a recruiter — the panel will not close this alone.
          </span>
        ) : (
          <span className={styles.flag}>Decided without escalation.</span>
        )}
      </section>

      <section className={styles.block}>
        <div className={styles.scoreRow}>
          <div
            className={`${styles.numeral} ${result.scored ? "" : styles.abstained}`}
          >
            {result.scored ? Math.round(result.final_score) : "—"}
          </div>

          <div className={styles.railWrap}>
            {result.scored ? (
              <>
                {/*
                  Bands, not a fill. A bar whose length tracked the score read as
                  a progress meter — 64 looked two-thirds "full" and therefore
                  good, while the colour said Reject. The score is a position on
                  a scale, not an amount collected, so the rail shows the three
                  bands and marks where the candidate landed.
                */}
                <div className={styles.rail}>
                  {ZONES.map((z) => (
                    <span
                      key={z.key}
                      className={`${styles.zone} ${styles[`zone_${z.key}`]}`}
                      style={{ left: `${z.from}%`, width: `${z.to - z.from}%` }}
                    />
                  ))}
                  <span
                    className={`${styles.marker} ${styles[`${tone}Marker`]}`}
                    style={{ left: `${result.final_score}%` }}
                    aria-hidden="true"
                  />
                </div>

                <div className={styles.tickLabels}>
                  {ZONES.slice(1).map((z) => (
                    <span
                      key={z.key}
                      className={`label ${styles.tickLabel}`}
                      style={{ left: `${z.from}%` }}
                    >
                      {z.from} {z.key}
                    </span>
                  ))}
                </div>

                {distanceToNextLine(result.final_score) && (
                  <p className={styles.gap}>
                    {distanceToNextLine(result.final_score)}
                  </p>
                )}
              </>
            ) : (
              <p className={styles.empty}>
                The panel declined to score. A number here would imply a judgement
                it does not have the inputs to make.
              </p>
            )}
          </div>
        </div>

        <div className={styles.stats}>
          <div className={styles.stat}>
            <span className="label">Match</span>
            <span className={styles.statValue}>
              {result.match_score.toFixed(2)}
            </span>
          </div>
          <div className={styles.stat}>
            <span className="label">Confidence</span>
            <span className={styles.statValue}>
              {result.confidence.toFixed(2)}
            </span>
          </div>
          <div className={styles.stat}>
            <span className="label">Coverage</span>
            <span className={styles.statValue}>{skills.coverage}</span>
          </div>
          <div className={styles.stat}>
            <span className="label">Experience</span>
            <span className={styles.statValue}>
              {candidate.experience_years}
              <span style={{ color: "var(--ink-faint)" }}>
                /{formatBand(role.experience_required)}
              </span>
            </span>
          </div>
        </div>
      </section>

      <section className={styles.block}>
        <div className={styles.blockHead}>
          <span className="label">Reasoning</span>
        </div>
        <p className={styles.reasoning}>{result.reasoning_summary}</p>
      </section>

      <section className={styles.block}>
        <div className={styles.blockHead}>
          <span className="label">Skills</span>
          <span className={styles.empty}>
            {skills.coverage} required · {candidate.skills.length} found
          </span>
        </div>

        {skills.matched_skills.length > 0 && (
          <>
            <p className={`label ${styles.subhead}`}>Required — held</p>
            <div className={styles.skills}>
              {skills.matched_skills.map((s) => (
                <span key={s} className={`${styles.skill} ${styles.has}`}>
                  {s}
                </span>
              ))}
            </div>
          </>
        )}

        {skills.missing_skills.length > 0 && (
          <>
            <p className={`label ${styles.subhead}`}>Required — absent</p>
            <div className={styles.skills}>
              {skills.missing_skills.map((s) => (
                <span key={s} className={`${styles.skill} ${styles.lacks}`}>
                  {s}
                </span>
              ))}
            </div>
          </>
        )}

        {role.required_skills.length === 0 && (
          <p className={styles.empty}>
            The role names no concrete skills, so there was nothing to match.
          </p>
        )}

        {skills.extra_skills.length > 0 && (
          <>
            <p className={`label ${styles.subhead}`}>Beyond the brief</p>
            <div className={styles.skills}>
              {skills.extra_skills.slice(0, 14).map((s) => (
                <span key={s} className={`${styles.skill} ${styles.also}`}>
                  {s}
                </span>
              ))}
            </div>
          </>
        )}
      </section>

      <section className={styles.block}>
        <div className={styles.blockHead}>
          <span className="label">Experience</span>
        </div>
        <div className={styles.expRow}>
          <span className={styles.expStatus}>{experience.status}</span>
          <span className={styles.expReason}>{experience.reason}</span>
        </div>
      </section>

      <section className={styles.block}>
        <div className={styles.blockHead}>
          <span className="label">The record</span>
          <button
            type="button"
            className={styles.rawToggle}
            onClick={() => setShowRaw((v) => !v)}
          >
            {showRaw ? "Hide JSON" : "View JSON"}
          </button>
        </div>

        <Trace steps={result.trace} />

        {showRaw && (
          <pre className={styles.raw}>{JSON.stringify(result, null, 2)}</pre>
        )}
      </section>
    </div>
  );
}

function formatBand(band: { min: number; max: number | null } | null): string {
  if (!band) return "unstated";
  return band.max === null ? `${band.min}+` : `${band.min}–${band.max}`;
}
