import { useTranslation } from "react-i18next";

const COLORS: Record<string, string> = {
  completed: "bg-emerald-100 text-emerald-700",
  running: "bg-blue-100 text-blue-700",
  queued: "bg-gray-100 text-gray-500",
  pending: "bg-gray-100 text-gray-500",
  failed: "bg-red-100 text-red-700",
  escalated: "bg-amber-100 text-amber-700",
};

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const { t } = useTranslation();

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${COLORS[status] ?? "bg-gray-100 text-gray-500"}`}
    >
      {t(`workflow.status.${status}`, status)}
    </span>
  );
}
