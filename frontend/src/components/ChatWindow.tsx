import { useEffect, useRef } from "react";
import ChatInput from "./ChatInput";

//types 

export interface Message {
  id: string;
  role: "bot" | "user";
  text: string;
  quickReplies?: string[];
}

interface ChatWindowProps {
  messages: Message[];
  onSend: (text: string) => void;
  isTyping?: boolean;
  disabled?: boolean;
}

//components

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2">
      <div className="rounded-2xl rounded-bl-sm bg-gray-700 px-4 py-3">
        <div className="flex gap-1 items-center h-4">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="block h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function MessageBubble({
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

//default component
export default function ChatWindow({
  messages,
  onSend,
  isTyping = false,
  disabled = false,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-8 flex flex-col min-h-[70vh] border border-gray-700 rounded-xl overflow-hidden bg-[#0B0C0D] text-gray-100">
      {/* Header */}
      <div className="flex items-center gap-2.5 px-4 py-3 border-b border-gray-700 shrink-0">
        <div>
          <p className="text-2xl font-semibold text-gray-100">IDTech AI</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-4">
        {messages.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-center text-xl text-gray-300">
              <i>Ask anything about IDTech payment hardware.</i>
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} msg={msg} onQuickReply={onSend} />
          ))
        )}
        {isTyping && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Escalation strip */}
      <div className="flex items-center gap-1 px-4 py-2 border-t border-gray-100">
        <span className="text-xs text-gray-400">Can't find what you need?</span>
        <a
          href="mailto:support@idtechproducts.com"
          className="text-xs text-blue-600 hover:underline"
        >
          Email our team →
        </a>
      </div>

      {/* Input */}
      <ChatInput onSend={onSend} disabled={disabled} />
    </div>
  );
}