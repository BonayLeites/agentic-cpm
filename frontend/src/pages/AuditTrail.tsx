import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import { getAudit, getWorkflowRun } from "../api/client";
import type { AuditResponse, WorkflowRunDetailResponse } from "../types";
import Breadcrumb from "../components/Breadcrumb";
import TraceOverview from "../components/audit/TraceOverview";
import StepTable from "../components/audit/StepTable";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSkeleton from "../components/LoadingSkeleton";

export default function AuditTrail() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const runId = params.get("run");
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedStepId, setExpandedStepId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [runData, setRunData] = useState<WorkflowRunDetailResponse | null>(null);

  useEffect(() => {
    if (!runId) return;
    getWorkflowRun(Number(runId)).then(setRunData).catch(() => {});
  }, [runId]);

  useEffect(() => {
    if (!runId) return;
    setLoading(true);
    setError(null);
    getAudit(Number(runId))
      .then(setAudit)
      .catch(() => { setAudit(null); setError(t("common.error")); })
      .finally(() => setLoading(false));
  }, [runId, t]);

  function toggleStep(id: number) {
    setExpandedStepId((prev) => (prev === id ? null : id));
  }

  if (!runId) {
    return (
      <div>
        <h1 className="text-xl font-bold text-gray-900">{t("audit.title")}</h1>
        <div className="mt-8">
          <EmptyState />
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-xl font-bold text-gray-900">{t("audit.title")}</h1>
      <Breadcrumb runData={runData} />

      <ErrorBanner message={error} />

      <div className="mt-5 space-y-5">
        {loading ? (
          <LoadingSkeleton lines={8} />
        ) : audit ? (
          <>
            <TraceOverview audit={audit} />
            <StepTable
              steps={audit.steps}
              expandedId={expandedStepId}
              onToggle={toggleStep}
            />
          </>
        ) : (
          <EmptyState />
        )}
      </div>
    </div>
  );
}
