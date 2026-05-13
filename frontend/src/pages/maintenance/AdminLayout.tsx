import { Outlet } from "react-router";
import "./admin.css";
import IDTechLogo from "./components/IDTechLogo";

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
        <nav className="flex justify-between pl-5 m-0 pr-5 bg-[#02AF6E] w-full min-h-12 items-center border-b-2 border-[#00955D] shrink-0">
            <div className="flex items-center">
                <div className="">
                    <IDTechLogo />
                </div>
                <h1 className="italic font-semibold text-2xl text-white p-0 pl-3">Admin Portal</h1>
            </div>
            <div className="flex justify-between">
                <a href="/admin/hardware" className="pr-2 text-white text-xl hover:text-gray-200">
                    Hardware
                </a>
                <a href="/admin/software" className="pr-2 text-white text-xl hover:text-gray-200">
                    Software
                </a>
                <a href="/admin/categories" className="pr-2 text-white text-xl hover:text-gray-200">
                    Categories
                </a>
                <a href="/admin/use-cases" className="text-white text-xl hover:text-gray-200">
                    Use Cases
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