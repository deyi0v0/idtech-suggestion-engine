export default function SampleChatBubble(
    {sender, message}: { sender: 'client' | 'server', message: string }
) {
    
    const bg_color = sender == 'client'? "bg-[#1A724B]": "bg-[#313131]";
    const text_color = sender == 'client'? "text-white": "text-white"; // "text-black";
    const side = sender == 'client'? "justify-start": "justify-end";
    const padding = sender == 'client'? "pr-8": "pl-8";
    
    return (
        <div className={"flex align-center " + side + " " + padding}>
            <div className={
                bg_color + " " + text_color + " rounded-xl flex items-center justify-left m-2"
            }>
                <p className="p-2">{message}</p>
            </div>
        </div>
    );
}