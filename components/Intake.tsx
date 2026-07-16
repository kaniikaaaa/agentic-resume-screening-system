"use client";

import { useRef, useState } from "react";
import {
  SAMPLE_CANDIDATES,
  SAMPLE_ROLES,
  loadSampleFile,
  loadSampleText,
} from "@/lib/samples";
import styles from "./Intake.module.css";

interface Props {
  resume: File | null;
  jd: string;
  busy: boolean;
  error: string | null;
  onResume: (file: File | null) => void;
  onJd: (text: string) => void;
  onSubmit: () => void;
  onReset: () => void;
}

export default function Intake({
  resume,
  jd,
  busy,
  error,
  onResume,
  onJd,
  onSubmit,
  onReset,
}: Props) {
  const [dragging, setDragging] = useState(false);
  const [activeRole, setActiveRole] = useState<string | null>(null);
  const [activeCandidate, setActiveCandidate] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const ready = Boolean(resume) && jd.trim().length >= 40 && !busy;

  function accept(file: File | undefined) {
    if (!file) return;
    setActiveCandidate(null);
    onResume(file);
  }

  async function pickCandidate(id: string, path: string) {
    onResume(await loadSampleFile(path));
    setActiveCandidate(id);
  }

  async function pickRole(id: string, path: string) {
    onJd(await loadSampleText(path));
    setActiveRole(id);
  }

  return (
    <form
      className={styles.intake}
      onSubmit={(event) => {
        event.preventDefault();
        if (ready) onSubmit();
      }}
    >
      <div className={styles.field}>
        <div className={styles.legend}>
          <span className={styles.ordinal}>01</span>
          <span className={styles.legendText}>The candidate</span>
          <span className={`label ${styles.hint}`}>PDF · 5MB</span>
        </div>

        <div
          className={`${styles.drop} ${dragging ? styles.dragging : ""} ${
            resume ? styles.loaded : ""
          }`}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            accept(event.dataTransfer.files[0]);
          }}
        >
          <svg
            className={styles.dropIcon}
            width="22"
            height="26"
            viewBox="0 0 22 26"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M13.5 1H3a2 2 0 0 0-2 2v20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8.5L13.5 1Z"
              stroke="currentColor"
              strokeWidth="1.2"
            />
            <path d="M13.5 1v7.5H21" stroke="currentColor" strokeWidth="1.2" />
            <path d="M5.5 14h11M5.5 18h7" stroke="currentColor" strokeWidth="1.2" />
          </svg>

          <span className={styles.dropBody}>
            <span className={styles.dropTitle}>
              {resume ? resume.name : "Drop a resume, or browse"}
            </span>
            <span className={styles.dropMeta}>
              {resume
                ? `${(resume.size / 1024).toFixed(0)} KB`
                : "Text-based PDFs only — scans need OCR"}
            </span>
          </span>

          {resume && (
            <button
              type="button"
              className={styles.clear}
              onClick={() => {
                onResume(null);
                setActiveCandidate(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
            >
              Remove
            </button>
          )}

          {!resume && (
            <input
              ref={inputRef}
              className={styles.file}
              type="file"
              accept="application/pdf,.pdf"
              aria-label="Resume PDF"
              onChange={(event) => accept(event.target.files?.[0])}
            />
          )}
        </div>

        <div className={styles.chips}>
          {SAMPLE_CANDIDATES.map((candidate) => (
            <button
              key={candidate.id}
              type="button"
              className={`${styles.chip} ${
                activeCandidate === candidate.id ? styles.chipOn : ""
              }`}
              onClick={() => pickCandidate(candidate.id, candidate.file)}
            >
              {candidate.name}
              <span className={styles.chipNote}>{candidate.role}</span>
            </button>
          ))}
        </div>
      </div>

      <div className={styles.field}>
        <div className={styles.legend}>
          <span className={styles.ordinal}>02</span>
          <span className={styles.legendText}>The role</span>
          <span className={`label ${styles.hint}`}>Plain text</span>
        </div>

        <textarea
          className={styles.textarea}
          value={jd}
          aria-label="Job description"
          placeholder="Paste the job description — responsibilities, required skills, experience band…"
          onChange={(event) => {
            onJd(event.target.value);
            setActiveRole(null);
          }}
        />

        <div className={styles.chips}>
          {SAMPLE_ROLES.map((role) => (
            <button
              key={role.id}
              type="button"
              className={`${styles.chip} ${
                activeRole === role.id ? styles.chipOn : ""
              }`}
              onClick={() => pickRole(role.id, role.file)}
            >
              {role.title}
              <span className={styles.chipNote}>{role.detail}</span>
            </button>
          ))}
        </div>
      </div>

      {error && <p className={styles.error}>{error}</p>}

      <div className={styles.actions}>
        <button type="submit" className={styles.submit} disabled={!ready}>
          {busy ? "Panel deliberating…" : "Convene the panel"}
        </button>
        <button type="button" className={styles.reset} onClick={onReset}>
          Clear
        </button>
      </div>
    </form>
  );
}
