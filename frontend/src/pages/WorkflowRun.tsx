import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams, Navigate, Link } from "react-router-dom";
import type { WorkflowType } from "../types";
import { useWorkflow } from "../hooks/useWorkflow";
import RunButton from "../components/workflow/RunButton";
import WorkflowTimeline from "../components/workflow/WorkflowTimeline";
import ActivityLog from "../components/workflow/ActivityLog";
import ConfigSidePanel from "../components/workflow/ConfigSidePanel";
import DataExplorer from "../components/workflow/DataExplorer";
import StatusBadge from "../components/StatusBadge";
import LoadingSkeleton from "../components/LoadingSkeleton";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";
import { formatDuration } from "../utils/format";

const WORKFLOW_TITLE_KEYS: Record<WorkflowType, string> = {
  consolidation: "home.case1Title",
  performance: "home.case2Title",
};

export default function WorkflowRun() {
  const { t, i18n } = useTranslation();
  const [params] = useSearchParams();
  const workflowType = params.get("workflow");
  const [configOpen, setConfigOpen] = useState(false);
  const [dataOpen, setDataOpen] = useState(false);

  const {
    run,
    timelineSteps,
    completedCount,
    totalCount,
    displayStatus,
    events,
    sseStatus,
    isRunning,
    loading,
    error,
    triggerRun,
  } = useWorkflow(workflowType, i18n.language);

  if (!workflowType) {
    return <Navigate to="/" replace />;
  }

  const titleKey =
    WORKFLOW_TITLE_KEYS[workflowType as WorkflowType] ?? "home.case1Title";

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">{t(titleKey)}</h1>
        <div className="flex gap-2">
          <button
          onClick={() => setDataOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-600 transition-colors hover:bg-gray-50"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 0v1.5c0 .621-.504 1.125-1.125 1.125" />
          </svg>
          {t("dataExplorer.viewData")}
        </button>
        <button
          onClick={() => setConfigOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-600 transition-colors hover:bg-gray-50"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75"
            />
          </svg>
          {t("workflow.viewConfig")}
        </button>
        </div>
      </div>

      <div className="mt-5">
        <RunButton
          disabled={isRunning}
          loading={isRunning}
          onClick={triggerRun}
        />
      </div>

      <ErrorBanner message={error} />

      {sseStatus === "reconnecting" && (
        <div className="mt-3 rounded-md bg-amber-50 px-4 py-2 text-sm text-amber-600">
          {t("workflow.sse.reconnecting")}
        </div>
      )}

      {displayStatus && (
        <div className="mt-4 flex items-center gap-4 text-sm">
          <span className="text-gray-500">{t("workflow.statusLabel")}:</span>
          <StatusBadge status={displayStatus} />
          <span className="text-gray-400">
            {t("workflow.stepsCompleted", {
              completed: completedCount,
              total: totalCount,
            })}
          </span>
          {run?.total_duration_ms != null && (
            <span className="text-gray-400">
              {t("workflow.totalTime")}:{" "}
              {formatDuration(run.total_duration_ms)}
            </span>
          )}
        </div>
      )}

      <div className="mt-6 space-y-6">
        {loading && !isRunning ? (
          <LoadingSkeleton lines={6} />
        ) : timelineSteps.length > 0 ? (
          <>
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <WorkflowTimeline steps={timelineSteps} />
            </div>
            <ActivityLog events={events} />

            {run?.status === "completed" && (
              <div className="flex gap-3">
                <Link
                  to={`/findings?run=${run.id}`}
                  className="inline-flex items-center rounded-md bg-white px-4 py-2 text-sm font-medium text-blue-600 border border-blue-200 hover:bg-blue-50 transition-colors"
                >
                  {t("workflow.viewFindings")} →
                </Link>
                <Link
                  to={`/summary?run=${run.id}`}
                  className="inline-flex items-center rounded-md bg-white px-4 py-2 text-sm font-medium text-blue-600 border border-blue-200 hover:bg-blue-50 transition-colors"
                >
                  {t("workflow.viewSummary")} →
                </Link>
              </div>
            )}
          </>
        ) : (
          <EmptyState />
        )}
      </div>

      <ConfigSidePanel
        isOpen={configOpen}
        onClose={() => setConfigOpen(false)}
        workflowType={workflowType}
      />

      <DataExplorer
        isOpen={dataOpen}
        onClose={() => setDataOpen(false)}
        workflowType={workflowType}
      />
    </div>
  );
}
