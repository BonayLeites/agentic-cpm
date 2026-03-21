interface ErrorBannerProps {
  message: string | null;
}

export default function ErrorBanner({ message }: ErrorBannerProps) {
  if (!message) return null;
  return (
    <div className="mt-3 rounded-md bg-red-50 px-4 py-3 text-sm text-red-600">
      {message}
    </div>
  );
}
