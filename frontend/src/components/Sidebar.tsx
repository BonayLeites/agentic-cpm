import { useTranslation } from "react-i18next";
import { NavLink, useSearchParams } from "react-router-dom";
import LanguageSelector from "./LanguageSelector";

const NAV_ITEMS = [
  { to: "/", labelKey: "nav.home", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4", needsRun: false },
  { to: "/workflow-run", labelKey: "nav.workflowRun", icon: "M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z", needsRun: false },
  { to: "/findings", labelKey: "nav.findings", icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4", needsRun: true },
  { to: "/summary", labelKey: "nav.summary", icon: "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z", needsRun: true },
  { to: "/audit", labelKey: "nav.audit", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z", needsRun: true },
];

export default function Sidebar() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const runId = params.get("run");

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-56 flex-col border-r border-gray-200 bg-white">
      {/* Header */}
      <div className="flex h-14 items-center border-b border-gray-200 px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-blue-600 text-xs font-bold text-white">
            CP
          </div>
          <span className="text-sm font-semibold text-gray-900 tracking-tight">
            CPM Accelerator
          </span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-0.5 px-2 py-3">
        {NAV_ITEMS.map(({ to, labelKey, icon, needsRun }) => {
          const href = needsRun && runId ? `${to}?run=${runId}` : to;
          return (
            <NavLink
              key={to}
              to={href}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-blue-50 font-medium text-blue-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`
              }
            >
              <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
              </svg>
              {t(labelKey)}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-200 px-4 py-3 space-y-3">
        <LanguageSelector />
        <p className="text-[11px] text-gray-400">{t("app.subtitle")}</p>
      </div>
    </aside>
  );
}
