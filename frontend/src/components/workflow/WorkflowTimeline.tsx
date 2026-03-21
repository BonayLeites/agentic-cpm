import { useTranslation } from "react-i18next";
import type { WorkflowStepResponse } from "../../types";
import StatusBadge from "../StatusBadge";
import { formatDuration } from "../../utils/format";

interface WorkflowTimelineProps {
  steps: WorkflowStepResponse[];
}

function StepIcon({ status }: { status: string }) {
  if (status === "completed") {
    return (
      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  }
  if (status === "running") {
    return (
      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-blue-600">
        <div className="h-2.5 w-2.5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }
  if (status === "failed") {
    return (
      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-red-100 text-red-600">
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
    );
  }
  return (
    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-gray-100 text-gray-400">
      <div className="h-2 w-2 rounded-full bg-gray-300" />
    </div>
  );
}

const PARALLEL_STEPS = new Set([2, 3]);

export default function WorkflowTimeline({ steps }: WorkflowTimelineProps) {
  const { t } = useTranslation();

  if (steps.length === 0) return null;

  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold text-gray-700">
        {t("workflow.timeline")}
      </h3>
      <div className="space-y-0">
        {steps.map((step, idx) => (
          <div
            key={step.id}
            className="flex items-center gap-3 rounded-md px-3 py-2 hover:bg-gray-50"
          >
            <div className="relative flex flex-col items-center">
              <StepIcon status={step.status} />
              {idx < steps.length - 1 && (
                <div className="absolute top-6 h-4 w-0.5 bg-gray-200" />
              )}
            </div>
            <span className="w-5 text-xs font-medium text-gray-400">
              {step.step_order}.
            </span>
            <span className="flex-1 text-sm text-gray-700">
              {t(`workflow.stepNames.${step.agent_name}`, step.agent_name)}
            </span>
            {PARALLEL_STEPS.has(step.step_order) && (
              <span className="rounded bg-violet-50 px-1.5 py-0.5 text-[10px] font-medium text-violet-500">
                {t("workflow.parallel")}
              </span>
            )}
            <span className="w-14 text-right text-xs tabular-nums text-gray-400">
              {formatDuration(step.duration_ms)}
            </span>
            <StatusBadge status={step.status} />
          </div>
        ))}
      </div>
    </div>
  );
}
