import { useTranslation } from "react-i18next";
import type { AudienceType } from "../../types";

interface AudienceToggleProps {
  audience: AudienceType;
  onChange: (audience: AudienceType) => void;
}

export default function AudienceToggle({
  audience,
  onChange,
}: AudienceToggleProps) {
  const { t } = useTranslation();

  return (
    <div className="inline-flex rounded-lg border border-gray-200 bg-white p-1">
      <button
        onClick={() => onChange("controller")}
        className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
          audience === "controller"
            ? "bg-blue-600 text-white"
            : "text-gray-500 hover:text-gray-700"
        }`}
      >
        {t("summary.audience.controller")}
      </button>
      <button
        onClick={() => onChange("executive")}
        className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
          audience === "executive"
            ? "bg-emerald-600 text-white"
            : "text-gray-500 hover:text-gray-700"
        }`}
      >
        {t("summary.audience.executive")}
      </button>
    </div>
  );
}
