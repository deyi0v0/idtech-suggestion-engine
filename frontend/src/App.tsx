import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import Dashboard from "./pages/maintenance/Dashboard"
import HardwareManager from "./pages/maintenance/HardwareManager"
import SoftwareManager from "./pages/maintenance/SoftwareManager"
import PromptManager from "./pages/maintenance/PromptManager"
import DocManager from "./pages/maintenance/DocManager"
import ChatWindow from "./components/ChatWindow"
import ProductModal from "./components/ProductModal"
import type { Message, Product } from "./types/messages"
import { sendChatMessage, forceChatMessage, ChatRequest } from "./api/client"
import ForceRecommendationButton from "./components/ForceRecommendationButton"

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [disabled, setDisabled] = useState(false);
  const [productModal, setProductModal] = useState<Product | null>(null);

  const buildHistory = (): { role: "user" | "assistant"; content: string }[] =>
    messages.map((m) => ({ role: m.role === "user" ? "user" : "assistant", content: m.text }));

  const onSend = async (text: string) => {
    const userMsg: Message = { id: `u-${Date.now()}`, role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);
    setDisabled(true);

    try {
      const req: ChatRequest = { message: text, history: buildHistory() };
      const resp = await sendChatMessage(req);

      // Map backend response to a bot message
      const botText = (resp && typeof resp === "object")
        ? (resp.explanation as string) ?? (resp.text as string) ?? JSON.stringify(resp)
        : String(resp);

      const botMsg: Message = {
        id: `b-${Date.now()}`,
        role: "bot",
        text: botText,
        quickReplies: (resp && (resp as any).quick_replies) || undefined,
      };

      setMessages((prev) => [...prev, botMsg]);

      // Open product modal only when response explicitly indicates a recommendation.
      // Backend sets `show_recommendation_modal` when a RecommendationBundle/hardware_name is present.
      let hw: any = null;
      if (resp && (resp as any).show_recommendation_modal) {
        hw = (resp as any).hardware_items?.[0] || (resp as any).hardware?.[0] || (resp as any).hardware || null;
      } else if (resp && typeof (resp as any).hardware_name === "string" && (resp as any).hardware_name.trim() !== "") {
        hw = { name: (resp as any).hardware_name.trim(), role: "Recommended", description: (resp as any).explanation ?? undefined };
      }

      if (hw) {
        const product: Product = {
          name: hw.name ?? hw.model_name ?? hw.hardware_name ?? "Product",
          sku: hw.sku ?? (hw.model && hw.model.sku) ?? "",
          description: (resp && (resp as any).explanation) ?? hw.role ?? JSON.stringify(hw),
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

  const onShowProduct = (p: Product) => setProductModal(p);

  const sampleRecommendationPrompt =
    "Please provide a hardware product recommendation (RecommendationBundle) for a payment terminal in a retail store.";
  const forceRecommendationPrompt =
    "Recommendation request: Please produce a RecommendationBundle JSON for the following scenario. Business: retail convenience store. Power: plugged into wall outlet. Card types: contact, contactless, magstripe. PIN entry: yes. Device: stand-alone unit. Host: none. Communication: Ethernet. Environment: indoor. Operating temps: 0-40C. Display: yes. Previous products: Ingenico and IDTECH. Return only valid JSON matching the RecommendationBundle schema with fields hardware_items, hardware_name, and explanation. Do not include extra text.";

  return (
    <Router>
      <Routes>
        {/* Customer Suggestion Engine */}
        <Route path="/" element={
          <div className="flex flex-col items-center">
            <h1 className="text-white text-center">IDTECH Suggestion Engine</h1>
              <ChatWindow messages={messages} onSend={onSend} isTyping={isTyping} disabled={disabled} onShowProduct={onShowProduct} />
              <div className="mt-4">
                {/* Test Recommendation removed — use ForceRecommendationButton instead */}
                <ForceRecommendationButton
                  buildHistory={buildHistory}
                  setMessages={setMessages}
                  setIsTyping={setIsTyping}
                  setDisabled={setDisabled}
                  setProductModal={setProductModal}
                  disabled={disabled}
                />
              </div>
            {productModal && <ProductModal product={productModal} onClose={() => setProductModal(null)} />}
          </div>
        } />

        {/* Maintenance Portal */}
        <Route path="/admin" element={<Dashboard />} />
        <Route path="/admin/hardware" element={<HardwareManager />} />
        <Route path="/admin/software" element={<SoftwareManager />} />
        <Route path="/admin/prompts" element={<PromptManager />} />
        <Route path="/admin/docs" element={<DocManager />} />
      </Routes>
    </Router>
  );
}

export default App;
