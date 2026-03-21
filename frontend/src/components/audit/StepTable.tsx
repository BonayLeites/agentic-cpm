import { useTranslation } from "react-i18next";
import type { AuditStepResponse } from "../../types";
import ConfidenceBar from "../ConfidenceBar";
import StatusBadge from "../StatusBadge";
import StepDetail from "./StepDetail";
import { formatDuration } from "../../utils/format";

interface StepTableProps {
  steps: AuditStepResponse[];
  expandedId: number | null;
  onToggle: (id: number) => void;
}

export default function StepTable({
  steps,
  expandedId,
  onToggle,
}: StepTableProps) {
  const { t } = useTranslation();

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
            <th className="w-12 px-4 py-2.5">#</th>
            <th className="px-4 py-2.5">{t("audit.steps")}</th>
            <th className="w-24 px-4 py-2.5 text-right">{t("audit.duration")}</th>
            <th className="w-24 px-4 py-2.5 text-right">{t("audit.confidence")}</th>
            <th className="w-28 px-4 py-2.5 text-center">{t("workflow.statusLabel")}</th>
          </tr>
        </thead>
        <tbody>
          {steps.map((step) => (
            <tr key={step.id}>
              <td
                colSpan={5}
                className="p-0"
              >
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => onToggle(step.id)}
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onToggle(step.id); } }}
                  aria-expanded={expandedId === step.id}
                  className={`flex w-full cursor-pointer items-center text-left transition-colors hover:bg-gray-50 ${
                    step.step_order % 2 === 0 ? "bg-gray-50/50" : ""
                  }`}
                >
                  <span className="w-12 px-4 py-2.5 text-xs tabular-nums text-gray-400">
                    {step.step_order}
                  </span>
                  <span className="flex-1 px-4 py-2.5 font-medium text-gray-700">
                    {step.agent_name}
                  </span>
                  <span className="w-24 px-4 py-2.5 text-right text-xs tabular-nums text-gray-500">
                    {formatDuration(step.duration_ms)}
                  </span>
                  <span className="w-28 px-4 py-2.5 text-right">
                    <ConfidenceBar value={step.confidence_score} />
                  </span>
                  <span className="w-28 px-4 py-2.5 text-center">
                    <StatusBadge status={step.status} />
                  </span>
                </div>
                {expandedId === step.id && <StepDetail step={step} />}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
