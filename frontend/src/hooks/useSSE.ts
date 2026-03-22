import { useCallback, useEffect, useRef, useState } from "react";
import type { ActivityEvent, SSEEventType } from "../types";
import { API_BASE } from "../api/client";

const RECONNECT_DELAY = 3000;
const MAX_RECONNECTS = 5;

const SSE_TYPES: SSEEventType[] = [
  "step_started",
  "step_completed",
  "step_failed",
  "step_escalated",
  "run_completed",
];

export type ConnectionStatus = "idle" | "connected" | "reconnecting" | "closed";

export function useSSE(runId: number | null) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>("idle");
  const [isCompleted, setIsCompleted] = useState(false);
  const eventIdRef = useRef(0);
  const reconnectCountRef = useRef(0);
  const esRef = useRef<EventSource | null>(null);
  const completedRef = useRef(false);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const close = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    esRef.current?.close();
    esRef.current = null;
    setStatus("closed");
  }, []);

  const reset = useCallback(() => {
    close();
    setEvents([]);
    setIsCompleted(false);
    completedRef.current = false;
    eventIdRef.current = 0;
    reconnectCountRef.current = 0;
    setStatus("idle");
  }, [close]);

  useEffect(() => {
    if (!runId) return;

    function connect() {
      const token = localStorage.getItem("demoToken");
      const tokenParam = token ? `?token=${encodeURIComponent(token)}` : "";
      const es = new EventSource(`${API_BASE}/api/workflows/${runId}/stream${tokenParam}`);
      esRef.current = es;

      es.onopen = () => {
        setStatus("connected");
        reconnectCountRef.current = 0;
      };

      function addEvent(type: SSEEventType, data: Record<string, unknown>) {
        setEvents((prev) => [
          ...prev,
          {
            id: ++eventIdRef.current,
            timestamp: new Date(),
            type,
            step_name: data.step_name as string | undefined,
            step_order: data.step_order as number | undefined,
            data,
          },
        ]);
      }

      for (const eventType of SSE_TYPES) {
        es.addEventListener(eventType, (e: MessageEvent) => {
          const data = JSON.parse(e.data) as Record<string, unknown>;
          addEvent(eventType, data);
          if (eventType === "run_completed") {
            completedRef.current = true;
            setIsCompleted(true);
            es.close();
            esRef.current = null;
            setStatus("closed");
          }
        });
      }

      // Empty listener: heartbeat only keeps the connection alive
      es.addEventListener("heartbeat", () => {});

      es.onerror = () => {
        es.close();
        esRef.current = null;
        if (reconnectCountRef.current < MAX_RECONNECTS && !completedRef.current) {
          setStatus("reconnecting");
          reconnectTimerRef.current = setTimeout(() => {
            reconnectCountRef.current++;
            connect();
          }, RECONNECT_DELAY);
        } else {
          setStatus("closed");
        }
      };
    }

    connect();

    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      esRef.current?.close();
      esRef.current = null;
    };
  // Deps intentionally limited to runId — connect is a stable closure over refs
  }, [runId]); // eslint-disable-line react-hooks/exhaustive-deps

  return { events, status, isCompleted, close, reset };
}
