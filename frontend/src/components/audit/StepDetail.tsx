import { useTranslation } from "react-i18next";
import type { AuditStepResponse } from "../../types";

interface StepDetailProps {
  step: AuditStepResponse;
}

function JsonBlock({ data }: { data: unknown }) {
  if (data == null) return <span className="text-gray-400">—</span>;
  return (
    <pre className="max-h-40 overflow-auto rounded bg-gray-50 p-2 text-xs text-gray-600">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

export default function StepDetail({ step }: StepDetailProps) {
  const { t } = useTranslation();

  return (
    <div className="space-y-3 bg-gray-50 px-4 py-3 text-sm">
      {/* Tools */}
      {step.tools_used != null && (
        <div>
          <h5 className="mb-1 text-xs font-semibold text-gray-500">
            {t("audit.toolCalls")}
          </h5>
          <JsonBlock data={step.tools_used} />
        </div>
      )}

      {/* LLM Calls */}
      {step.llm_calls != null && (
        <div>
          <h5 className="mb-1 text-xs font-semibold text-gray-500">
            {t("audit.llmCalls")}
          </h5>
          <JsonBlock data={step.llm_calls} />
        </div>
      )}

      {/* Output */}
      {step.output_data != null && (
        <div>
          <h5 className="mb-1 text-xs font-semibold text-gray-500">
            {t("audit.output")}
          </h5>
          <JsonBlock data={step.output_data} />
        </div>
      )}

      {/* Retries & Error */}
      <div className="flex gap-6 text-xs text-gray-500">
        <span>
          {t("audit.retries")}: {step.retry_count}
        </span>
        {step.error_message && (
          <span className="text-red-600">
            {t("audit.error")}: {step.error_message}
          </span>
        )}
      </div>
    </div>
  );
}
