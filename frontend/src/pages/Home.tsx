import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getStats } from "../api/client";
import type { StatsResponse } from "../types";
import WorkflowCard from "../components/WorkflowCard";
import LoadingSkeleton from "../components/LoadingSkeleton";

export default function Home() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto max-w-3xl py-8">
      <h1 className="text-center text-2xl font-bold text-gray-900">
        {t("home.selectWorkflow")}
      </h1>

      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2">
        <WorkflowCard workflowType="consolidation" />
        <WorkflowCard workflowType="performance" />
      </div>

      <div className="mt-8 text-center">
        {loading ? (
          <div className="mx-auto w-48">
            <LoadingSkeleton lines={1} />
          </div>
        ) : stats ? (
          <p className="text-sm text-gray-400">
            {t("home.statsTemplate", {
              entities: stats.entities,
              months: 6,
              docs: stats.documents,
            })}
          </p>
        ) : null}
      </div>
    </div>
  );
}
