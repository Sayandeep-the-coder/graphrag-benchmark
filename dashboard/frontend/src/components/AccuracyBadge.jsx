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
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold tracking-wide ${
        isPASS
          ? "bg-green-500/15 text-green-400 border border-green-500/30"
          : "bg-red-500/15 text-red-400 border border-red-500/30"
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
