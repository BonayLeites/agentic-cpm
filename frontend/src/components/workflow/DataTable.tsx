// Generic table component — `any` is intentional for row-agnostic column definitions
/* eslint-disable @typescript-eslint/no-explicit-any */
interface Column<T = any> {
  key: string;
  label: string;
  align?: "left" | "right";
  format?: (value: any, row: T) => string | React.ReactNode;
  highlight?: (row: T) => boolean;
}

interface DataTableProps {
  columns: Column[];
  rows: Record<string, any>[];
  emptyMessage?: string;
}

export default function DataTable({
  columns,
  rows,
  emptyMessage = "—",
}: DataTableProps) {
  if (rows.length === 0) {
    return (
      <div className="py-8 text-center text-sm text-gray-400">{emptyMessage}</div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50 text-xs font-medium uppercase tracking-wide text-gray-500">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-4 py-2.5 ${col.align === "right" ? "text-right" : "text-left"}`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className={`border-b border-gray-100 ${i % 2 === 1 ? "bg-gray-50/50" : ""}`}
            >
              {columns.map((col) => {
                const isHighlighted = col.highlight?.(row);
                const value = col.format
                  ? col.format(row[col.key], row)
                  : String(row[col.key] ?? "—");
                return (
                  <td
                    key={col.key}
                    className={`px-4 py-2 ${col.align === "right" ? "text-right tabular-nums" : ""} ${
                      isHighlighted ? "font-medium text-red-600" : "text-gray-700"
                    }`}
                  >
                    {value}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export type { Column };
