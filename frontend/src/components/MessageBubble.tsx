import { useState } from "react";
import type { Message } from "../types/messages";
import GenericButton from "./GenericButton";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { downloadRecommendationPDF, RecommendationBundle } from "../api/client";

export default function MessageBubble({
  msg,
  onQuickReply,
}: {
  msg: Message;
  onQuickReply: (label: string) => void;
}) {
  const isBot = msg.role === "bot";
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadPDF = async () => {
    if (!msg.product) return;
    setIsDownloading(true);
    try {
      const bundle: RecommendationBundle = {
        hardware_name: msg.product.name,
        hardware_items: [
          {
            name: msg.product.name,
            sku: msg.product.sku,
            role: "Recommended",
          },
        ],
        explanation: msg.product.description,
        highlights: [],
      };
      const blob = await downloadRecommendationPDF(bundle);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
      window.addEventListener("unload", () => URL.revokeObjectURL(url), { once: true });
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className={`flex flex-col gap-2 ${isBot ? "items-start" : "items-end"}`}>
      {isBot ? (
        <div className="w-full">
          <div className="w-full px-3 py-2 text-sm leading-relaxed text-primary prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {msg.text}
            </ReactMarkdown>
          </div>
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

      {isBot && msg.product && (
        <div className="w-full rounded-xl border border-gray-200 bg-white/80 p-4">
          <p className="text-xs uppercase tracking-wide text-secondary">Recommended Hardware</p>
          <p className="mt-1 text-base font-semibold text-primary">{msg.product.name}</p>
          {msg.product.sku && <p className="mt-1 text-xs text-secondary">SKU: {msg.product.sku}</p>}
          <p className="mt-2 text-sm text-secondary">{msg.product.description}</p>
          <div className="mt-3">
            <GenericButton onClick={handleDownloadPDF} disabled={isDownloading} className="btn-accent text-primary">
              {isDownloading ? "Generating PDF..." : "Download Recommendation PDF"}
            </GenericButton>
          </div>
        </div>
      )}
    </div>
  );
}
