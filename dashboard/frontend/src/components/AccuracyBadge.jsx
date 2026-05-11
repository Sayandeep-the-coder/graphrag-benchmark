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
          ? "bg-green-500/20 text-green-400 border-green-500/50 shadow-[0_0_10px_rgba(34,197,94,0.3)]"
          : "bg-red-500/20 text-red-400 border-red-500/50 shadow-[0_0_10px_rgba(239,68,68,0.3)]"
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
