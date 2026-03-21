import { useTranslation } from "react-i18next";
import type { AuditResponse } from "../../types";
import ConfidenceBar from "../ConfidenceBar";
import { formatDuration } from "../../utils/format";

interface TraceOverviewProps {
  audit: AuditResponse;
}

export default function TraceOverview({ audit }: TraceOverviewProps) {
  const { t } = useTranslation();

  const avgConfidence =
    audit.steps.length > 0
      ? audit.steps.reduce(
          (sum, s) => sum + Number(s.confidence_score ?? 0),
          0,
        ) / audit.steps.length
      : 0;

  const metrics: { label: string; value: string | number }[] = [
    { label: t("audit.duration"), value: formatDuration(audit.total_duration_ms) },
    { label: t("audit.steps"), value: audit.steps.length },
    { label: t("findings.title"), value: audit.total_findings },
    { label: t("audit.cost"), value: audit.total_cost != null ? `$${Number(audit.total_cost).toFixed(2)}` : "—" },
  ];

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-400">
        {t("audit.overview")}
      </h3>
      <div className="grid grid-cols-5 gap-4">
        {metrics.map((m) => (
          <div key={m.label} className="text-center">
            <p className="text-lg font-semibold tabular-nums text-gray-900">
              {m.value}
            </p>
            <p className="mt-0.5 text-xs text-gray-400">{m.label}</p>
          </div>
        ))}
        <div className="text-center">
          <div className="flex justify-center">
            <ConfidenceBar value={avgConfidence} />
          </div>
          <p className="mt-1.5 text-xs text-gray-400">{t("audit.confidence")}</p>
        </div>
      </div>
    </div>
  );
}
