import ColorButton from "./components/ColorButton";

export default function Dashboard() {
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
            <div className="flex min-h-fit min-w-fit">
                <ColorButton color="#03A50E" onClick={() => console.log("button clicked!")}>
                    Submit
                </ColorButton>
                <ColorButton color="#DF1300" onClick={() => console.log("button clicked!")}>
                    Back
                </ColorButton>
            </div>

            {/*
            The below div will contain a table of the devices that the AI can recommend, 
            as well as attributes that the AI model uses to recommend a device.
            
            it will be fetched from the 
            */}
            <div className="flex flex-col bg-amber-300 grow-1">
                <h1 className="font-semibold text-2xl max-h-fit">hi</h1>
            </div>

        </div>
    );
}
