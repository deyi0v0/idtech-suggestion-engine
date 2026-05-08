import ColorButton from "./components/ColorButton";

export default function HardwareManager() {
    return (
        <div className='flex flex-col p-0 text-black grow'>
            <div>
                <h1 className="font-semibold text-2xl max-h-fit">
                    Solution List - Hardware
                </h1>
                <p>
                    This is a list of the current devices that the AI is able to recommend,
                    as well as attributes that the AI model uses to recommend a device.
                </p>
            </div>
            <br />


            <div className="flex flex-col bg-amber-300 grow-1">
                <h1 className="font-semibold text-2xl max-h-fit">table goes here!</h1>
            </div>

            <div className="flex min-h-fit min-w-fit">
                {/* This button needs an onClick handler to open an addDevice form page */}
                <ColorButton className="mr-1" color="#03A50E" onClick={() => console.log("button clicked!")}>
                    Add Device
                </ColorButton>

                {/* This button needs an onClick handler to remove the device selected
                    by the user. The button should only be enabled if a device is selected. */}
                <ColorButton color="#DF1300" onClick={() => console.log("button clicked!")}>
                    Remove Device
                </ColorButton>
            </div>

        </div>
    );
}
