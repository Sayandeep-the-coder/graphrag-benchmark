/**
 * AccuracyBadge — PASS/FAIL pill badge for LLM-Judge verdicts.
 *
 * Props:
 *   verdict: "PASS" | "FAIL"
 */
export default function AccuracyBadge({ verdict }) {
  const isPASS = verdict === "PASS";

  return (
    <span
      className={`badge-premium gap-1.5 ${
        isPASS
          ? "bg-accent-neon/10 text-accent-neon border-accent-neon/30 shadow-[0_0_15px_rgba(0,255,163,0.15)]"
          : "bg-accent-warning/10 text-accent-warning border-accent-warning/30 shadow-[0_0_15px_rgba(255,138,0,0.15)]"
      }`}
    >
      {isPASS ? (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      )}
      {verdict}
    </span>
  );
}
