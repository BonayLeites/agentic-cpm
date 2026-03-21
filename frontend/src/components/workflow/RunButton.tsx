import { useTranslation } from "react-i18next";

interface RunButtonProps {
  disabled: boolean;
  loading?: boolean;
  onClick: () => void;
}

export default function RunButton({ disabled, loading, onClick }: RunButtonProps) {
  const { t } = useTranslation();

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="w-full rounded-lg bg-blue-600 px-6 py-3.5 text-base font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {loading ? t("workflow.running") : `»  ${t("workflow.runButton")}  «`}
    </button>
  );
}
