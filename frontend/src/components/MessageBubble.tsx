import type { Message, Product } from "../types/messages";
import GenericButton from "./GenericButton";

export default function MessageBubble({
  msg,
  onQuickReply,
  onShowProduct,
}: {
  msg: Message;
  onQuickReply: (label: string) => void;
  onShowProduct?: (product: Product) => void;
}) {
  const isBot = msg.role === "bot";

  return (
    <div className={`flex flex-col gap-2 ${isBot ? "items-start" : "items-end"}`}>
      {isBot ? (
        <div className="w-full">
          <p className="w-full px-3 py-2 text-sm leading-relaxed text-primary">
            {msg.text}
          </p>
        </div>
      ) : (
        <div className="self-end max-w-[75%] inline-block">
          <p className="inline-block rounded-2xl px-3 py-2 text-sm leading-relaxed bubble-user-bg">
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

      {isBot && msg.product && onShowProduct && (
        <GenericButton onClick={() => onShowProduct(msg.product!)}>
          View Recommended Products
        </GenericButton>
      )}
    </div>
  );
}
