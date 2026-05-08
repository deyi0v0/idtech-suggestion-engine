import { useNavigate } from "react-router-dom";
import ColorButton from "./components/ColorButton";

export default function AddHardware() {
    const navigate = useNavigate();

    return (
        <div className="flex flex-col p-0 text-black grow gap-3">
            <div>
                <h1 className="font-semibold text-2xl">Add Device</h1>
                <p className="text-gray-600 text-sm">
                    Add a new hardware device to the recommendation database.
                </p>
            </div>

            <div className="flex flex-col grow items-center justify-center text-gray-400">
                <p>Form coming soon.</p>
            </div>

            <div className="flex min-h-fit min-w-fit">
                <ColorButton color="#6B7280" onClick={() => navigate("/admin")}>
                    Back
                </ColorButton>
            </div>
        </div>
    );
}
