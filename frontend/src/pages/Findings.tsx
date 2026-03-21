import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import { getFindings, getWorkflowRun } from "../api/client";
import type { FindingResponse, Severity, WorkflowRunDetailResponse } from "../types";
import Breadcrumb from "../components/Breadcrumb";
import FindingsSummaryBar from "../components/findings/FindingsSummaryBar";
import SeverityFilter from "../components/findings/SeverityFilter";
import FindingCard from "../components/findings/FindingCard";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSkeleton from "../components/LoadingSkeleton";

type FilterValue = Severity | "all";

export default function Findings() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const runId = params.get("run");
  const [findings, setFindings] = useState<FindingResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeSeverity, setActiveSeverity] = useState<FilterValue>("all");
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
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
    getFindings(Number(runId))
      .then(setFindings)
      .catch(() => { setFindings([]); setError(t("common.error")); })
      .finally(() => setLoading(false));
  }, [runId, t]);

  const filtered =
    activeSeverity === "all"
      ? findings
      : findings.filter((f) => f.severity === activeSeverity);

  function toggleExpand(id: number) {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  if (!runId) {
    return (
      <div>
        <h1 className="text-xl font-bold text-gray-900">{t("findings.title")}</h1>
        <div className="mt-8">
          <EmptyState />
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-xl font-bold text-gray-900">{t("findings.title")}</h1>
      <Breadcrumb runData={runData} />

      {!loading && findings.length > 0 && (
        <div className="mt-4">
          <FindingsSummaryBar findings={findings} />
        </div>
      )}

      <div className="mt-4">
        <SeverityFilter
          findings={findings}
          active={activeSeverity}
          onChange={setActiveSeverity}
        />
      </div>

      <ErrorBanner message={error} />

      <div className="mt-5 space-y-3">
        {loading ? (
          <LoadingSkeleton lines={6} />
        ) : filtered.length === 0 ? (
          <EmptyState />
        ) : (
          filtered.map((f) => (
            <FindingCard
              key={f.id}
              finding={f}
              isExpanded={expandedIds.has(f.id)}
              onToggle={() => toggleExpand(f.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
