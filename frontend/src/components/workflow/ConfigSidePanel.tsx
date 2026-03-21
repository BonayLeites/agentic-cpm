import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { getConfig } from "../../api/client";
import type { ConfigResponse, EntityResponse } from "../../types";
import LoadingSkeleton from "../LoadingSkeleton";

interface ConfigSidePanelProps {
  isOpen: boolean;
  onClose: () => void;
  workflowType: string;
}

function EntityTree({ entities }: { entities: EntityResponse[] }) {
  const parent = entities.find((e) => e.parent_id == null);
  const children = entities.filter((e) => e.parent_id != null);

  return (
    <ul className="space-y-1 text-sm">
      {parent && (
        <li>
          <span className="font-medium text-gray-900">{parent.code}</span>
          <span className="ml-1.5 text-gray-500">
            {parent.name} ({parent.currency})
          </span>
          {children.length > 0 && (
            <ul className="ml-4 mt-1 space-y-1 border-l border-gray-200 pl-3">
              {children.map((c) => (
                <li key={c.id} className="text-gray-600">
                  <span className="font-medium text-gray-800">{c.code}</span>
                  <span className="ml-1.5">
                    {c.name} ({c.currency}
                    {c.ownership_pct != null && `, ${c.ownership_pct}%`})
                  </span>
                </li>
              ))}
            </ul>
          )}
        </li>
      )}
    </ul>
  );
}

function DatasetCounts({ counts }: { counts: ConfigResponse["dataset_counts"] }) {
  const items = [
    { label: "trial_balances", value: counts.trial_balances },
    { label: "intercompany_transactions", value: counts.intercompany_transactions },
    { label: "exchange_rates", value: counts.exchange_rates },
    { label: "journal_entries", value: counts.journal_entries },
    { label: "budgets", value: counts.budgets },
    { label: "kpis", value: counts.kpis },
    { label: "documents", value: counts.documents },
  ].filter((i) => i.value > 0);

  return (
    <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
      {items.map((i) => (
        <div key={i.label} className="flex justify-between text-gray-500">
          <span>{i.label.replace(/_/g, " ")}</span>
          <span className="font-medium text-gray-700 tabular-nums">
            {i.value}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function ConfigSidePanel({
  isOpen,
  onClose,
  workflowType,
}: ConfigSidePanelProps) {
  const { t } = useTranslation();
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const loadedForRef = useRef<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    if (loadedForRef.current === workflowType && config !== null) return;
    setLoading(true);
    getConfig(workflowType)
      .then((data) => { loadedForRef.current = workflowType; setConfig(data); })
      .catch(() => setConfig(null))
      .finally(() => setLoading(false));
  // Deps exclude loadedForRef — only refetch when panel opens or workflow changes
  }, [isOpen, workflowType]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isOpen) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  return (
    <>
      {/* Overlay */}
      <div
        className={`fixed inset-0 z-40 bg-black/20 transition-opacity ${
          isOpen ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className={`fixed inset-y-0 right-0 z-50 w-[400px] transform overflow-y-auto border-l border-gray-200 bg-white shadow-xl transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
          <h2 className="text-base font-semibold text-gray-900">
            {t("config.title")}
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="divide-y divide-gray-100 px-5">
          {loading ? (
            <div className="py-6">
              <LoadingSkeleton lines={8} />
            </div>
          ) : config ? (
            <>
              {/* Entities + Data */}
              <section className="py-4">
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                  {t("config.connectedData")}
                </h3>
                <EntityTree entities={config.entities} />
                <DatasetCounts counts={config.dataset_counts} />
              </section>

              {/* Knowledge Packs */}
              <section className="py-4">
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                  {t("config.knowledgePacks")}
                </h3>
                <ul className="space-y-1">
                  {config.knowledge_packs.map((kp) => (
                    <li
                      key={kp.title}
                      className="flex items-center gap-2 text-sm text-gray-600"
                    >
                      <svg className="h-3.5 w-3.5 shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                      </svg>
                      {kp.title}
                      {kp.doc_type && (
                        <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">
                          {kp.doc_type}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </section>

              {/* Business Rules */}
              <section className="py-4">
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                  {t("config.businessRules")}
                </h3>
                <ul className="space-y-1.5">
                  {Object.keys(config.business_rules).map((key) => (
                    <li key={key} className="text-sm text-gray-600">
                      {t(`config.rules.${key}`, config.business_rules[key])}
                    </li>
                  ))}
                </ul>
              </section>

              {/* Tools */}
              <section className="py-4">
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                  {t("config.enabledTools")}
                </h3>
                <ul className="space-y-2">
                  {config.tools.map((tool) => (
                    <li key={tool.name}>
                      <span className="text-sm font-medium text-gray-700">
                        {tool.name}
                      </span>
                      <p className="text-xs text-gray-400">
                        {t(`config.tools.${tool.name}`, tool.description)}
                      </p>
                    </li>
                  ))}
                </ul>
              </section>
            </>
          ) : null}
        </div>
      </div>
    </>
  );
}
