import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router-dom";
import { getSummary, getWorkflowRun } from "../api/client";
import type { AudienceType, SummaryResponse, WorkflowRunDetailResponse } from "../types";
import Breadcrumb from "../components/Breadcrumb";
import AudienceToggle from "../components/summary/AudienceToggle";
import SummaryDocument from "../components/summary/SummaryDocument";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSkeleton from "../components/LoadingSkeleton";
import { formatConfidence } from "../utils/format";

export default function ExecutiveSummary() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const runId = params.get("run");
  const [audience, setAudience] = useState<AudienceType>("controller");
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [runData, setRunData] = useState<WorkflowRunDetailResponse | null>(null);
  const cacheRef = useRef<Partial<Record<AudienceType, SummaryResponse>>>({});
  const [error, setError] = useState<string | null>(null);

  // Load run stats for the footer
  useEffect(() => {
    if (!runId) return;
    getWorkflowRun(Number(runId)).then(setRunData).catch(() => {});
  }, [runId]);

  useEffect(() => {
    if (!runId) return;
    const cached = cacheRef.current[audience];
    if (cached) { setSummary(cached); return; }
    setLoading(true);
    getSummary(Number(runId), audience)
      .then((data) => { cacheRef.current[audience] = data; setSummary(data); setError(null); })
      .catch(() => { setSummary(null); setError(t("common.error")); })
      .finally(() => setLoading(false));
  }, [runId, audience, t]);

  if (!runId) {
    return (
      <div>
        <h1 className="text-xl font-bold text-gray-900">{t("summary.title")}</h1>
        <div className="mt-8">
          <EmptyState />
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">{t("summary.title")}</h1>
          <Breadcrumb runData={runData} />
        </div>
        <AudienceToggle audience={audience} onChange={setAudience} />
      </div>

      {!loading && <ErrorBanner message={error} />}

      <div className="mt-5">
        {loading ? (
          <LoadingSkeleton lines={10} />
        ) : summary ? (
          <>
            <SummaryDocument content={summary.summary} />
            <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
              <span>
                {runData ? (
                  <>
                    {t("audit.confidence")}: {formatConfidence(runData.overall_confidence)}
                    {" | "}
                    {runData.steps.length} {t("audit.steps").toLowerCase()}
                    {" | "}
                    {t("audit.cost")}: ${Number(runData.total_cost ?? 0).toFixed(2)}
                  </>
                ) : (
                  t("summary.confidenceFooter")
                )}
              </span>
              <Link
                to={`/audit?run=${runId}`}
                className="text-blue-600 hover:text-blue-700"
              >
                {t("nav.audit")} →
              </Link>
            </div>
          </>
        ) : (
          <EmptyState />
        )}
      </div>
    </div>
  );
}
