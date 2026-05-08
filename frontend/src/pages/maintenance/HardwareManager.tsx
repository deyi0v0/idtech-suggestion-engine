import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ColorButton from "./components/ColorButton";
import DataTable, { ColumnDef } from "./components/DataTable";

type HardwareDevice = {
    id: number;
    model_name: string;
    operate_temperature: string | null;
    input_power: string | null;
    ip_rating: string | null;
    ik_rating: string | null;
    interface: string | null;
};

const COLUMNS: ColumnDef<HardwareDevice>[] = [
    { header: "Model Name", key: "model_name" },
    { header: "Operating Temp.", key: "operate_temperature" },
    { header: "Input Power", key: "input_power" },
    { header: "IP Rating", key: "ip_rating" },
    { header: "IK Rating", key: "ik_rating" },
    { header: "Interface", key: "interface" },
];

export default function HardwareManager() {
    const navigate = useNavigate();
    const [devices, setDevices] = useState<HardwareDevice[]>([]);
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);

    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetch("http://localhost:8000/api/maintenance/hardware/")
            .then((res) => {
                if (!res.ok) throw new Error(`Server error: ${res.status}`);
                return res.json();
            })
            .then((data) => {
                if (!Array.isArray(data)) throw new Error("Unexpected response format");
                setDevices(data);
            })
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    function handleRemove() {
        console.log("Remove device:", selectedId);
    }

    return (
        <div className="flex flex-col p-0 text-black grow gap-3 min-h-0">
            <div>
                <h1 className="font-semibold text-2xl">Devices</h1>
                <p className="text-gray-600 text-sm">
                    This is a list of the current devices that the AI is able to recommend,
                    as well as attributes that the AI model uses to recommend a device.
                </p>
                <p className="text-gray-600 text-sm">
                    The table can be scrolled, and individual cells can be scrolled if the text overflows.
                </p>
                <p className="text-gray-600 text-sm">
                    To remove a device, select the row and click "Remove Device." To add a device, click "Add Device."
                </p>
            </div>

            <div className="flex flex-col grow min-h-0 overflow-hidden">
                {loading ? (
                    <p className="text-gray-400 text-sm">Loading...</p>
                ) : error ? (
                    <p className="text-red-500 text-sm">Failed to load devices: {error}</p>
                ) : (
                    <DataTable
                        columns={COLUMNS}
                        data={devices}
                        selectedId={selectedId}
                        onSelectRow={setSelectedId}
                    />
                )}
            </div>

            <div className="flex min-h-fit min-w-fit">
                <ColorButton
                    className="mr-1"
                    color="#03A50E"
                    onClick={() => navigate("/admin/hardware/add")}
                >
                    Add New Device
                </ColorButton>
                <ColorButton
                    color="#DF1300"
                    disabled={selectedId === null}
                    onClick={handleRemove}
                >
                    Remove a Device
                </ColorButton>
            </div>
        </div>
    );
}
