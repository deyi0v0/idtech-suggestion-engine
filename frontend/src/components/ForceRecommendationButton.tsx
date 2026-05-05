import React from "react";
import type { Message, Product } from "../types/messages";
import { forceChatMessage, ChatRequest } from "../api/client";

interface Props {
  buildHistory: () => { role: "user" | "assistant"; content: string }[];
  setMessages: (updater: (prev: Message[]) => Message[]) => void;
  setIsTyping: (v: boolean) => void;
  setDisabled: (v: boolean) => void;
  setProductModal: (p: Product | null) => void;
  disabled: boolean;
}

const forceRecommendationPrompt =
  "Recommendation request: Please produce a RecommendationBundle JSON for the following scenario. Business: retail convenience store. Power: plugged into wall outlet. Card types: contact, contactless, magstripe. PIN entry: yes. Device: stand-alone unit. Host: none. Communication: Ethernet. Environment: indoor. Operating temps: 0-40C. Display: yes. Previous products: Ingenico and IDTECH. Return only valid JSON matching the RecommendationBundle schema with fields hardware_items, hardware_name, and explanation. Do not include extra text.";

export default function ForceRecommendationButton({ buildHistory, setMessages, setIsTyping, setDisabled, setProductModal, disabled }: Props) {
  const handleClick = async () => {
    const text = forceRecommendationPrompt;
    const userMsg: Message = { id: `u-${Date.now()}`, role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);
    setDisabled(true);
    try {
      const req: ChatRequest & { force_recommendation?: boolean } = { message: text, history: buildHistory(), force_recommendation: true } as any;
      const resp = await forceChatMessage(req);

      const botText = (resp && typeof resp === "object")
        ? (resp.explanation as string) ?? (resp.text as string) ?? JSON.stringify(resp)
        : String(resp);

      const botMsg: Message = { id: `b-${Date.now()}`, role: "bot", text: botText };
      setMessages((prev) => [...prev, botMsg]);

      if (resp && (resp as any).show_recommendation_modal) {
        const hw = (resp as any).hardware_items?.[0] || (resp as any).hardware?.[0] || (resp as any).hardware || null;
        if (hw) {
          const product: Product = {
            name: hw.name ?? hw.model_name ?? hw.hardware_name ?? "Product",
            sku: hw.sku ?? hw.model?.sku ?? "",
            description: (resp as any).explanation ?? hw.role ?? JSON.stringify(hw),
          };
          setProductModal(product);
        }
      } else if (resp && typeof (resp as any).hardware_name === "string" && (resp as any).hardware_name.trim() !== "") {
        const product: Product = {
          name: (resp as any).hardware_name.trim(),
          sku: "",
          description: (resp as any).explanation ?? "",
        };
        setProductModal(product);
      }

    } catch (err) {
      const errMsg: Message = { id: `e-${Date.now()}`, role: "bot", text: `Error: ${String(err)}` };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsTyping(false);
      setDisabled(false);
    }
  };

  return (
    <button
      className="ml-3 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded"
      onClick={handleClick}
      disabled={disabled}
    >
      Force Recommendation
    </button>
  );
}
