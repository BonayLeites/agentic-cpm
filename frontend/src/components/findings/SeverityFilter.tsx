import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { FindingResponse, Severity } from "../../types";

type FilterValue = Severity | "all";

interface SeverityFilterProps {
  findings: FindingResponse[];
  active: FilterValue;
  onChange: (value: FilterValue) => void;
}

const FILTERS: { value: FilterValue; colorActive: string; colorInactive: string }[] = [
  { value: "all", colorActive: "bg-blue-600 text-white", colorInactive: "text-gray-600 hover:bg-gray-100" },
  { value: "high", colorActive: "bg-red-600 text-white", colorInactive: "text-red-600 hover:bg-red-50" },
  { value: "medium", colorActive: "bg-amber-500 text-white", colorInactive: "text-amber-600 hover:bg-amber-50" },
  { value: "low", colorActive: "bg-gray-500 text-white", colorInactive: "text-gray-500 hover:bg-gray-100" },
];

export default function SeverityFilter({
  findings,
  active,
  onChange,
}: SeverityFilterProps) {
  const { t } = useTranslation();

  const counts = useMemo(() => {
    const result: Record<FilterValue, number> = { all: findings.length, high: 0, medium: 0, low: 0 };
    for (const f of findings) {
      if (f.severity in result) result[f.severity as Severity]++;
    }
    return result;
  }, [findings]);

  return (
    <div className="flex gap-2">
      {FILTERS.map(({ value, colorActive, colorInactive }) => (
        <button
          key={value}
          onClick={() => onChange(value)}
          className={`inline-flex items-center rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
            active === value
              ? colorActive
              : `border border-gray-200 ${colorInactive}`
          }`}
        >
          {value === "all"
            ? t("findings.all")
            : t(`findings.severity.${value}`)}
          <span className="ml-1.5 tabular-nums">({counts[value]})</span>
        </button>
      ))}
    </div>
  );
}
