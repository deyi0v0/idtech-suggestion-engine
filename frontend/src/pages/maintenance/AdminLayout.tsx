import { Outlet } from "react-router";

export default function AdminLayout() {
    return (
        <div className="flex bg-black w-screen h-screen items-center">
            <div className="flex flex-col bg-white h-full grow-1"> 
                <nav className="flex pl-5 m-0 bg-white w-full min-h-[64px] items-end border-b-2">
                    <h1 className="font-semibold text-4xl">Admin Portal</h1>
                </nav>
                <div id="dashboard-page" className="flex flex-col p-5 bg-white grow-1">
                    <div className="flex bg-white border grow-1">
                        <Outlet />
                    </div>
                </div>
            </div>
            <ChatbotPlaceholder/>
        </div>
    );
}

function ChatbotPlaceholder() {
    return (
        <div className="flex flex-col bg-amber-200 h-full min-w-[400px] p-[10px] items-center justify-center">
            <h1 className="bg-red-100 max-w-fit max-h-fit p-[10px]">
                chatbot component
            </h1>
        </div>
    );
}