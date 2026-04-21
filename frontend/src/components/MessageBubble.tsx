import type { Message } from "../types/messages";

export default function MessageBubble({
  msg,
  onQuickReply,
}: {
  msg: Message;
  onQuickReply: (label: string) => void;
}) {
  const isBot = msg.role === "bot";

  return (
    <div className={`flex flex-col gap-2 ${isBot ? "items-start" : "items-end"}`}>
      {isBot ? (
        <div className="w-full">
          <p className="w-full px-3 py-2 text-sm leading-relaxed text-gray-200">
            {msg.text}
          </p>
        </div>
      ) : (
        <div className="self-end max-w-[75%] inline-block">
          <p className="inline-block rounded-2xl px-3 py-2 text-sm leading-relaxed bg-[#2B2B2B] text-white">
            {msg.text}
          </p>
        </div>
      )}

      {isBot && msg.quickReplies && msg.quickReplies.length > 0 && (
        <div className="flex flex-wrap gap-2 pl-9">
          {msg.quickReplies.map((label) => (
            <button
              key={label}
              onClick={() => onQuickReply(label)}
              className="rounded-full border border-gray-200 bg-white px-3 py-1 text-xs text-blue-600 hover:bg-blue-50 transition-colors"
            >
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
