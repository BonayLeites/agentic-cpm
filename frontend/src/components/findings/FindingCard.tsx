import { useTranslation } from "react-i18next";
import type { Evidence, FindingResponse } from "../../types";
import ConfidenceBar from "../ConfidenceBar";
import SeverityBadge from "../SeverityBadge";

interface FindingCardProps {
  finding: FindingResponse;
  isExpanded: boolean;
  onToggle: () => void;
}

function EvidenceItem({ item, t }: { item: Evidence; t: (key: string) => string }) {
  const typeLabels: Record<string, string> = {
    data_point: t("findings.evidenceType.data"),
    document_excerpt: t("findings.evidenceType.doc"),
    rule_reference: t("findings.evidenceType.rule"),
  };

  return (
    <div className="flex gap-2 text-sm">
      <span className="shrink-0 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium uppercase text-gray-500">
        {typeLabels[item.type] ?? item.type}
      </span>
      <span className="text-gray-600">{item.label}: {item.value}</span>
    </div>
  );
}

export default function FindingCard({
  finding,
  isExpanded,
  onToggle,
}: FindingCardProps) {
  const { t } = useTranslation();
  const evidence = (finding.evidence ?? []) as Evidence[];
  const questions = (finding.suggested_questions ?? []) as string[];
  const actions = (finding.suggested_actions ?? []) as string[];

  return (
    <div className="rounded-lg border border-gray-200 bg-white transition-shadow hover:shadow-sm">
      <button
        onClick={onToggle}
        aria-expanded={isExpanded}
        className="flex w-full items-start gap-3 px-4 py-3.5 text-left"
      >
        <div className="mt-0.5">
          <SeverityBadge severity={finding.severity} />
        </div>
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-medium text-gray-900">{finding.title}</h4>
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400">
            {finding.impact_amount != null && (
              <span>
                {t("findings.impact")}: {finding.impact_currency}{" "}
                {Number(finding.impact_amount).toLocaleString()}
              </span>
            )}
            {finding.confidence != null && (
              <span className="flex items-center gap-1">
                {t("findings.confidence")}: <ConfidenceBar value={finding.confidence} />
              </span>
            )}
            {evidence.length > 0 && (
              <span>
                {t("findings.evidence")}: {evidence.length}
              </span>
            )}
          </div>
        </div>
        <svg
          className={`h-4 w-4 shrink-0 text-gray-400 transition-transform ${isExpanded ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <div
        className={`grid transition-[grid-template-rows] duration-200 ease-out ${
          isExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        }`}
      >
        <div className="overflow-hidden">
          <div className="border-t border-gray-100 px-4 py-4 space-y-4">
          {finding.description && (
            <p className="text-sm leading-relaxed text-gray-600 whitespace-pre-line">
              {finding.description}
            </p>
          )}

          <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-500">
            {finding.entity_code && (
              <span>
                {t("findings.entity")}: <span className="font-medium text-gray-700">{finding.entity_code}</span>
              </span>
            )}
            {finding.rule_triggered && (
              <span>
                {t("findings.ruleTriggered")}: <span className="font-medium text-gray-700">{finding.rule_triggered}</span>
              </span>
            )}
          </div>

          {evidence.length > 0 && (
            <div>
              <h5 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400">
                {t("findings.evidence")}
              </h5>
              <div className="space-y-1.5">
                {evidence.map((e, i) => (
                  <EvidenceItem key={i} item={e} t={t} />
                ))}
              </div>
            </div>
          )}

          {questions.length > 0 && (
            <div>
              <h5 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400">
                {t("findings.suggestedQuestions")}
              </h5>
              <ul className="space-y-1 text-sm text-gray-600">
                {questions.map((q, i) => (
                  <li key={i}>• {q}</li>
                ))}
              </ul>
            </div>
          )}

          {actions.length > 0 && (
            <div>
              <h5 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400">
                {t("findings.suggestedActions")}
              </h5>
              <ol className="space-y-1 text-sm text-gray-600">
                {actions.map((a, i) => (
                  <li key={i}>
                    {i + 1}. {a}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {finding.escalation_needed && finding.escalation_reason && (
            <div className="rounded-md bg-amber-50 p-3 text-sm text-amber-700">
              <span className="font-medium">{t("findings.escalation")}:</span>{" "}
              {finding.escalation_reason}
            </div>
          )}
        </div>
        </div>
      </div>
    </div>
  );
}
