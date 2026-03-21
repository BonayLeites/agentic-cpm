interface LoadingSkeletonProps {
  lines?: number;
}

export default function LoadingSkeleton({ lines = 4 }: LoadingSkeletonProps) {
  return (
    <div className="animate-pulse space-y-3">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 rounded bg-gray-200"
          style={{ width: `${Math.max(20, 85 - i * 10)}%` }}
        />
      ))}
    </div>
  );
}
