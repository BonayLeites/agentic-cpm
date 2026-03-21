import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import type { WorkflowType } from "../types";

const CARD_KEYS: Record<WorkflowType, { title: string; desc: string; audience: string }> = {
  consolidation: { title: "home.case1Title", desc: "home.case1Desc", audience: "home.case1Audience" },
  performance: { title: "home.case2Title", desc: "home.case2Desc", audience: "home.case2Audience" },
};

interface WorkflowCardProps {
  workflowType: WorkflowType;
}

export default function WorkflowCard({ workflowType }: WorkflowCardProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const keys = CARD_KEYS[workflowType];

  return (
    <div className="flex flex-col rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
      <h3 className="text-lg font-semibold text-gray-900">{t(keys.title)}</h3>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-gray-500">
        {t(keys.desc)}
      </p>
      <p className="mt-3 text-xs font-medium uppercase tracking-wide text-gray-400">
        {t(keys.audience)}
      </p>
      <button
        onClick={() => navigate(`/workflow-run?workflow=${workflowType}`)}
        className="mt-5 inline-flex w-full items-center justify-center rounded-md bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
      >
        {t("home.select")} →
      </button>
    </div>
  );
}
