interface SummaryDocumentProps {
  content: string;
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function parseMarkdown(text: string): string {
  return escapeHtml(text)
    .replace(/^### (.+)$/gm, '<h4 class="mt-5 mb-2 text-sm font-semibold text-gray-800">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="mt-6 mb-2 text-base font-bold text-gray-900">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
    .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li class="ml-4 list-decimal">$1. $2</li>');
}

function splitIntoParagraphs(html: string): string[] {
  return html
    .split(/\n{2,}/)
    .map((p) => p.replace(/\n/g, "<br />").trim())
    .filter(Boolean);
}

export default function SummaryDocument({ content }: SummaryDocumentProps) {
  const parsed = parseMarkdown(content);
  const paragraphs = splitIntoParagraphs(parsed);

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      {paragraphs.map((p, i) => (
        <div
          key={i}
          className={`px-6 py-4 ${i > 0 ? "border-t border-gray-100" : ""} ${
            i === 0 ? "border-l-4 border-l-blue-500 bg-blue-50/30" : ""
          }`}
        >
          <div
            className={`prose prose-sm max-w-none leading-relaxed ${
              i === 0 ? "text-gray-900 font-medium" : "text-gray-700"
            }`}
            dangerouslySetInnerHTML={{ __html: p }}
          />
        </div>
      ))}
    </div>
  );
}
