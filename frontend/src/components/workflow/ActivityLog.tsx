import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import type { ActivityEvent, SSEEventType } from "../../types";
import { formatDuration } from "../../utils/format";
import EmptyState from "../EmptyState";

interface ActivityLogProps {
  events: ActivityEvent[];
}

const timeFmt = new Intl.DateTimeFormat(undefined, {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});
function formatTime(d: Date): string {
  return timeFmt.format(d);
}

const TYPE_COLORS: Record<SSEEventType, string> = {
  step_started: "text-blue-500",
  step_completed: "text-emerald-600",
  step_failed: "text-red-500",
  step_escalated: "text-amber-500",
  run_completed: "text-emerald-700 font-medium",
};

const TYPE_ICONS: Record<SSEEventType, string> = {
  step_started: "▶",
  step_completed: "✓",
  step_failed: "✗",
  step_escalated: "⚠",
  run_completed: "★",
};

function EventLine({ event }: { event: ActivityEvent }) {
  const { t } = useTranslation();
  const name = event.step_name
    ? t(`workflow.stepNames.${event.step_name}`, event.step_name)
    : "";

  let message: string;
  switch (event.type) {
    case "step_started":
      message = `${name} — ${t("workflow.sse.started")}`;
      break;
    case "step_completed":
      message = `${name} — ${t("workflow.sse.completed", {
        duration: formatDuration(event.data.duration_ms as number | null),
        findings: event.data.finding_count as number,
      })}`;
      break;
    case "step_failed":
      message = `${name} — ${t("workflow.sse.failed", { error: event.data.error as string })}`;
      break;
    case "step_escalated":
      message = `${name} — ${t("workflow.sse.escalated", { reason: event.data.reason as string })}`;
      break;
    case "run_completed":
      message = t("workflow.sse.runCompleted", {
        duration: formatDuration(event.data.total_duration_ms as number | null),
        findings: event.data.total_findings as number,
      });
      break;
  }

  return (
    <div className="flex gap-3 px-3 py-1 text-xs hover:bg-gray-50">
      <span className="shrink-0 tabular-nums text-gray-400">
        {formatTime(event.timestamp)}
      </span>
      <span className={TYPE_COLORS[event.type]}>
        <span className="mr-1.5 inline-block w-3 text-center">{TYPE_ICONS[event.type]}</span>
        {message}
      </span>
    </div>
  );
}

export default function ActivityLog({ events }: ActivityLogProps) {
  const { t } = useTranslation();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold text-gray-700">
        {t("workflow.activityLog")}
      </h3>
      <div className="h-48 overflow-y-auto rounded-lg border border-gray-200 bg-white">
        {events.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="py-1">
            {events.map((e) => (
              <EventLine key={e.id} event={e} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  );
}
