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

          <div className="mt-3 flex flex-col gap-2">
            {/* Primary: View on ID TECH website */}
            {msg.product.product_url && (
              <a
                href={msg.product.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
              >
                View on ID TECH website →
              </a>
            )}

            {/* Supplementary: Installation/docs links from Confluence */}
            {msg.product.installation_docs && msg.product.installation_docs.length > 0 && (
              <div className="mt-1">
                <p className="text-xs text-secondary mb-1">Installation Guides & Docs:</p>
                <div className="flex flex-wrap gap-2">
                  {msg.product.installation_docs.map((doc, i) => (
                    <a
                      key={i}
                      href={doc.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:text-blue-800 underline"
                    >
                      {doc.title}
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Secondary: Download PDF */}
            <GenericButton onClick={handleDownloadPDF} disabled={isDownloading} className="btn-accent text-primary text-xs mt-1 self-start">
              {isDownloading ? "Generating PDF..." : "Download PDF"}
            </GenericButton>
          </div>
        </div>
      )}
    </div>
  );
}
