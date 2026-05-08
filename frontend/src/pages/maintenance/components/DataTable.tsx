export type ColumnDef<T> = {
    header: string;
    key: keyof T;
};

type DataTableProps<T extends { id: number }> = {
    columns: ColumnDef<T>[];
    data: T[];
    selectedId: number | null;
    onSelectRow: (id: number) => void;
};

export default function DataTable<T extends { id: number }>({
    columns,
    data,
    selectedId,
    onSelectRow,
}: DataTableProps<T>) {
    return (
        <div className="w-full h-full overflow-y-auto border border-gray-200 rounded">
            <table className="table-fixed w-full border-collapse text-sm text-left">
                <thead>
                    <tr className="bg-gray-100 border-b border-gray-300 sticky top-0 z-10">
                        {columns.map((col) => (
                            <th
                                key={String(col.key)}
                                className="px-4 py-3 font-semibold text-gray-700"
                            >
                                {col.header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, index) => {
                        const isSelected = row.id === selectedId;
                        return (
                            <tr
                                key={row.id}
                                onClick={() => onSelectRow(row.id)}
                                className={[
                                    "cursor-pointer border-b border-gray-200",
                                    isSelected
                                        ? "bg-indigo-600 text-white"
                                        : index % 2 === 0
                                        ? "bg-white text-gray-800 hover:bg-gray-50"
                                        : "bg-gray-50 text-gray-800 hover:bg-gray-100",
                                ].join(" ")}
                            >
                                {columns.map((col) => (
                                    <td
                                        key={String(col.key)}
                                        className="px-4 py-3 max-w-0"
                                    >
                                        <div className="cell-scroll overflow-x-auto whitespace-nowrap">
                                            {String(row[col.key] ?? "—")}
                                        </div>
                                    </td>
                                ))}
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
