import { Outlet } from "react-router";
import "./admin.css";
import IDTechLogoBlack from "./components/IDTechLogoBlack";

export default function AdminLayout() {
    return (
        <div className="flex bg-black w-screen h-screen overflow-hidden items-center">
            <div className="flex flex-col bg-white h-full flex-1 min-w-0">
                <DashboardNavbar />
                <div id="dashboard-page" className="flex flex-col p-5 bg-white flex-1 min-h-0 overflow-hidden">
                    {/* add border to this div for visualizing overflow issues */}
                    <div className="flex bg-white flex-1 min-h-0 overflow-hidden">
                        <Outlet />
                    </div>
                </div>
            </div>
            <ChatbotPlaceholder/>
        </div>
    );
}

function DashboardNavbar() {
    return (
        <nav className="flex justify-between pl-5 m-0 pr-5 bg-white w-full min-h-16 items-end border-b-2 shrink-0">
            <div className="flex items-end">
                <div className="pb-2">
                    <IDTechLogoBlack />
                </div>
                <h1 className="italic font-semibold text-4xl p-0 pl-3">Admin Portal</h1>
            </div>
            <div className="flex justify-between">
                <a href="/admin/hardware" className="pr-2 text-gray-600 text-xl hover:text-gray-900">
                    Hardware
                </a>
                <a href="/admin/software" className="text-gray-600 text-xl hover:text-gray-900">
                    Software
                </a>
            </div>
        </nav>
    );
}

function ChatbotPlaceholder() {
    return <></>;
    // return (
    //     <div className="flex flex-col bg-amber-200 h-full min-w-[400px] p-[10px] items-center justify-center">
    //         <h1 className="bg-red-100 max-w-fit max-h-fit p-[10px]">
    //             chatbot component
    //         </h1>
    //     </div>
    // );
}