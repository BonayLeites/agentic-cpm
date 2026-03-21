import { useTranslation } from "react-i18next";
import type { WorkflowRunDetailResponse } from "../types";

interface BreadcrumbProps {
  runData: WorkflowRunDetailResponse | null;
}

const WORKFLOW_TITLE_KEYS: Record<string, string> = {
  consolidation: "home.case1Title",
  performance: "home.case2Title",
};

export default function Breadcrumb({ runData }: BreadcrumbProps) {
  const { t } = useTranslation();

  if (!runData) return null;

  const titleKey = WORKFLOW_TITLE_KEYS[runData.workflow_type] ?? runData.workflow_type;

  return (
    <div className="mt-1 flex items-center gap-1.5 text-xs text-gray-400">
      <span>{t(titleKey)}</span>
      <span className="text-gray-300">/</span>
      <span>Run #{runData.id}</span>
    </div>
  );
}
