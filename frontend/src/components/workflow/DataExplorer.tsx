import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getTrialBalances, getICTransactions, getKPIs } from "../../api/client";
import type { TrialBalanceRow, ICTransactionRow, KPIRow } from "../../types";
import DataTable from "./DataTable";
import type { Column } from "./DataTable";
import LoadingSkeleton from "../LoadingSkeleton";

interface DataExplorerProps {
  isOpen: boolean;
  onClose: () => void;
  workflowType: string;
}

type Tab = "trial_balances" | "ic_transactions" | "kpis";

const PERIOD = "2026-02";

function fmtNum(v: unknown): string {
  return Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 });
}

export default function DataExplorer({ isOpen, onClose, workflowType }: DataExplorerProps) {
  const { t } = useTranslation();
  const isConsolidation = workflowType === "consolidation";

  const tabs: { key: Tab; label: string }[] = isConsolidation
    ? [
        { key: "trial_balances", label: t("dataExplorer.trialBalances") },
        { key: "ic_transactions", label: t("dataExplorer.icTransactions") },
      ]
    : [
        { key: "trial_balances", label: t("dataExplorer.trialBalances") },
        { key: "kpis", label: t("dataExplorer.kpis") },
      ];

  const [activeTab, setActiveTab] = useState<Tab>(tabs[0].key);
  const [tbData, setTbData] = useState<TrialBalanceRow[]>([]);
  const [icData, setIcData] = useState<ICTransactionRow[]>([]);
  const [kpiData, setKpiData] = useState<KPIRow[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    const promises: Promise<void>[] = [
      getTrialBalances(PERIOD).then(setTbData),
    ];
    if (isConsolidation) {
      promises.push(getICTransactions(PERIOD).then(setIcData));
    } else {
      promises.push(getKPIs(PERIOD).then(setKpiData));
    }
    Promise.all(promises)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isOpen, workflowType]);

  if (!isOpen) return null;

  const tbColumns: Column<TrialBalanceRow>[] = [
    { key: "entity_code", label: t("dataExplorer.entity") },
    { key: "account_code", label: t("dataExplorer.account") },
    { key: "account_name", label: t("dataExplorer.type") },
    {
      key: "debit",
      label: t("dataExplorer.debit"),
      align: "right",
      format: (v) => fmtNum(v),
    },
    {
      key: "credit",
      label: t("dataExplorer.credit"),
      align: "right",
      format: (v) => fmtNum(v),
    },
  ];

  const icColumns: Column<ICTransactionRow>[] = [
    { key: "from_entity", label: t("dataExplorer.from") },
    { key: "to_entity", label: t("dataExplorer.to") },
    { key: "transaction_type", label: t("dataExplorer.type") },
    {
      key: "amount",
      label: t("dataExplorer.amount"),
      align: "right",
      format: (v) => fmtNum(v),
    },
    { key: "currency", label: t("dataExplorer.currency") },
    { key: "invoice_date", label: t("dataExplorer.invoiceDate") },
    { key: "recorded_date", label: t("dataExplorer.recordedDate") },
    {
      key: "mismatch",
      label: t("dataExplorer.mismatch"),
      align: "right",
      format: (v) => fmtNum(v),
      highlight: (row) => row.mismatch > 0,
    },
  ];

  const kpiColumns: Column<KPIRow>[] = [
    { key: "entity_code", label: t("dataExplorer.entity") },
    { key: "kpi_name", label: t("dataExplorer.kpiName") },
    {
      key: "value",
      label: t("dataExplorer.value"),
      align: "right",
      format: (v) => String(v),
      highlight: (row) => row.target != null && Math.abs(Number(row.value) - Number(row.target)) / Number(row.target) > 0.2,
    },
    {
      key: "target",
      label: t("dataExplorer.target"),
      align: "right",
      format: (v) => v != null ? String(v) : "—",
    },
    { key: "unit", label: t("dataExplorer.unit") },
  ];

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/20" onClick={onClose} />
      <div className="fixed inset-y-0 right-0 z-50 flex w-[700px] flex-col bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {t("dataExplorer.title")}
            </h2>
            <p className="mt-0.5 text-xs text-gray-400">
              {t("dataExplorer.period", { period: PERIOD })}
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex gap-1 border-b border-gray-200 px-5">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2.5 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "border-b-2 border-blue-600 text-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-5">
              <LoadingSkeleton lines={8} />
            </div>
          ) : (
            <>
              {activeTab === "trial_balances" && (
                <DataTable columns={tbColumns} rows={tbData} />
              )}
              {activeTab === "ic_transactions" && (
                <DataTable columns={icColumns} rows={icData} />
              )}
              {activeTab === "kpis" && (
                <DataTable columns={kpiColumns} rows={kpiData} />
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
