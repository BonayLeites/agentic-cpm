import { useTranslation } from "react-i18next";
import type { FindingResponse } from "../../types";

interface FindingsSummaryBarProps {
  findings: FindingResponse[];
}

export default function FindingsSummaryBar({ findings }: FindingsSummaryBarProps) {
  const { t } = useTranslation();

  if (findings.length === 0) return null;

  const high = findings.filter((f) => f.severity === "high").length;
  const medium = findings.filter((f) => f.severity === "medium").length;
  const low = findings.filter((f) => f.severity === "low").length;

  const cards = [
    {
      value: findings.length,
      label: t("findings.title"),
      dot: "bg-blue-500",
      bg: "bg-blue-50 border-blue-100",
    },
    {
      value: high,
      label: t("findings.severity.high"),
      dot: "bg-red-500",
      bg: "bg-red-50 border-red-100",
    },
    {
      value: medium,
      label: t("findings.severity.medium"),
      dot: "bg-amber-500",
      bg: "bg-amber-50 border-amber-100",
    },
    {
      value: low,
      label: t("findings.severity.low"),
      dot: "bg-gray-400",
      bg: "bg-gray-50 border-gray-100",
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-3">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`rounded-lg border px-4 py-3 ${card.bg}`}
        >
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full ${card.dot}`} />
            <span className="text-lg font-semibold tabular-nums text-gray-900">
              {card.value}
            </span>
          </div>
          <p className="mt-0.5 text-xs text-gray-500">{card.label}</p>
        </div>
      ))}
    </div>
  );
}
