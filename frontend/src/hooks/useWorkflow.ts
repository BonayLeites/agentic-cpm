import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createWorkflowRun,
  getLatestWorkflow,
  getWorkflowRun,
} from "../api/client";
import type {
  LiveStep,
  SSEEventType,
  StepStatus,
  WorkflowRunDetailResponse,
  WorkflowStepResponse,
} from "../types";
import { useSSE } from "./useSSE";

const CONSOLIDATION_STEPS = [
  "load_data",
  "ic_check",
  "anomaly_detect",
  "doc_search",
  "analysis",
  "narrative",
  "quality_gate",
];

const PERFORMANCE_STEPS = [
  "load_data",
  "variance_analysis",
  "kpi_analysis",
  "doc_search",
  "analysis",
  "narrative",
  "quality_gate",
];

function getStepNames(workflowType: string): string[] {
  return workflowType === "performance"
    ? PERFORMANCE_STEPS
    : CONSOLIDATION_STEPS;
}

function liveStepsToResponse(steps: LiveStep[]): WorkflowStepResponse[] {
  return steps.map((s, i) => ({
    id: -(i + 1),
    step_order: s.step_order,
    agent_name: s.step_name,
    status: s.status,
    started_at: null,
    completed_at: null,
    duration_ms: s.duration_ms,
    finding_count: s.finding_count,
    confidence_score: s.confidence_score,
    cost: null,
    error_message: null,
  }));
}

export function useWorkflow(workflowType: string | null, language: string = "en") {
  const [run, setRun] = useState<WorkflowRunDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sseRunId, setSseRunId] = useState<number | null>(null);

  const {
    events,
    status: sseStatus,
    isCompleted,
    reset: resetSSE,
  } = useSSE(sseRunId);

  const isRunning = sseRunId !== null && !isCompleted;

  useEffect(() => {
    if (!workflowType) return;
    setLoading(true);
    getLatestWorkflow(workflowType)
      .then(setRun)
      .catch(() => setRun(null))
      .finally(() => setLoading(false));
  }, [workflowType]);

  useEffect(() => {
    if (isCompleted && sseRunId) {
      getWorkflowRun(sseRunId)
        .then((fullRun) => {
          setRun(fullRun);
          setSseRunId(null);
        })
        .catch(() => setSseRunId(null));
    }
  }, [isCompleted, sseRunId]);

  const triggerRun = useCallback(async () => {
    if (!workflowType || isRunning) return;
    setError(null);
    resetSSE();
    try {
      const { run_id } = await createWorkflowRun(workflowType, language);
      setRun(null);
      setSseRunId(run_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start workflow");
    }
  }, [workflowType, isRunning, resetSSE, language]);

  const liveSteps: LiveStep[] = useMemo(() => {
    if (!isRunning || !workflowType) return [];
    const stepNames = getStepNames(workflowType);
    const stepsMap = new Map<number, LiveStep>();

    stepNames.forEach((name, i) => {
      stepsMap.set(i + 1, {
        step_order: i + 1,
        step_name: name,
        status: "queued" as StepStatus,
        duration_ms: null,
        finding_count: 0,
        confidence_score: null,
      });
    });

    for (const event of events) {
      const order = event.step_order;
      if (!order) continue;
      const step = stepsMap.get(order);
      if (!step) continue;

      switch (event.type as SSEEventType) {
        case "step_started":
          step.status = "running";
          break;
        case "step_completed":
          step.status = "completed";
          step.duration_ms = (event.data.duration_ms as number) ?? null;
          step.finding_count = (event.data.finding_count as number) ?? 0;
          step.confidence_score =
            (event.data.confidence_score as number) ?? null;
          break;
        case "step_failed":
          step.status = "failed";
          break;
        case "step_escalated":
          step.status = "escalated";
          break;
      }
    }

    return Array.from(stepsMap.values());
  }, [events, isRunning, workflowType]);

  const timelineSteps: WorkflowStepResponse[] = useMemo(
    () => (isRunning ? liveStepsToResponse(liveSteps) : (run?.steps ?? [])),
    [isRunning, liveSteps, run?.steps],
  );

  const completedCount = useMemo(
    () => timelineSteps.filter((s) => s.status === "completed").length,
    [timelineSteps],
  );

  const totalCount = timelineSteps.length;

  const displayStatus = isRunning ? "running" : (run?.status ?? null);

  return {
    run,
    timelineSteps,
    completedCount,
    totalCount,
    displayStatus,
    events,
    sseStatus,
    isRunning,
    loading,
    error,
    triggerRun,
  };
}
