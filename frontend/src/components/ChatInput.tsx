import { useState, useRef } from "react";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Ask about specs, compatibility, verticals…",
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const canSend = value.trim().length > 0 && !disabled;

  return (
    <div className="flex items-end gap-2 px-4 py-4 border-t border-[#0B0C0D] bg-[#0B0C0D]">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none rounded-lg px-3 py-2 text-sm placeholder:text-[#BFBFBF] leading-relaxed overflow-hidden bg-[#2B2B2B] text-[#F2F2F2] border border-[#F2F2F2] focus:outline-none disabled:opacity-50"
      />
      <button
        onClick={submit}
        disabled={!canSend}
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#03A60E] text-white transition-opacity disabled:opacity-30 hover:bg-[#84D98A] active:scale-95"
        aria-label="Send message"
        style={{ boxShadow: '0 1px 0 rgba(0,0,0,0.3)' }}
      >
        <svg width="16" height="16" viewBox="0 0 14 14" fill="none">
          <path
            d="M1.5 7h11M8 2.5L12.5 7 8 11.5"
            stroke="#F2F2F2"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </div>
  );
}