import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Dashboard from "./pages/maintenance/Dashboard"
import HardwareManager from "./pages/maintenance/HardwareManager"
import SoftwareManager from "./pages/maintenance/SoftwareManager"
import PromptManager from "./pages/maintenance/PromptManager"
import DocManager from "./pages/maintenance/DocManager"
import ChatWindow from "./components/ChatWindow"
import type { Message, Product } from "./types/messages"
import { sendChatMessage, ChatRequest, ChatResponse } from "./api/client"
import ForceRecommendationButton from "./components/ForceRecommendationButton"

const WELCOME_MESSAGE: Message = {
  id: "welcome-1",
  role: "bot",
  text: "What business are you running today, and what kind of payment experience are you trying to offer your customers?",
};

const normalizeBotText = (raw: string): string => {
  const cleanedLines = raw
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .filter((line) => !/satisf(y|ies)\s+the\s+requirements?\s+for\s+this\s+question/i.test(line))
    .map((line) => {
      let normalized = line.replace(/^\d+\.\s*/, "");
      normalized = normalized.replace(/^"(.*)"$/, "$1");
      return normalized.trim();
    });

  return cleanedLines.join("\n\n");
};

function App() {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [isTyping, setIsTyping] = useState(false);
  const [disabled, setDisabled] = useState(false);
  const [isLightTheme, setIsLightTheme] = useState(false);

  useEffect(() => {
    document.body.classList.toggle("light-theme", isLightTheme);
  }, [isLightTheme]);

  const buildHistory = (): { role: "user" | "assistant"; content: string }[] =>
    messages.map((m) => ({ role: m.role === "user" ? "user" : "assistant", content: m.text }));

  const onSend = async (text: string) => {
    const lastBotMessage = [...messages].reverse().find((m) => m.role === "bot");
    const lastBotText = (lastBotMessage?.text ?? "").toLowerCase();
    const userText = text.trim().toLowerCase();
    const looksLikeNoHostAnswer =
      userText.includes("no host") || userText === "none" || userText === "n/a";
    const askingOutdoorOrTemp =
      lastBotText.includes("outdoor") || lastBotText.includes("temperature") || lastBotText.includes("ip rating");
    if (looksLikeNoHostAnswer && askingOutdoorOrTemp) {
      const userMsg: Message = { id: `u-${Date.now()}`, role: "user", text };
      const botMsg: Message = {
        id: `b-${Date.now()}-clarify`,
        role: "bot",
        text: "Thanks. For this question, I need the deployment environment and temperature range. Will this be indoor or outdoor, and what low/high temperatures should it support?",
        type: "multipleChoice",
        choices: [
          { id: "env-indoor", label: "Indoor (0C to 40C)" },
          { id: "env-outdoor-mild", label: "Outdoor (-20C to 65C)" },
          { id: "env-outdoor-harsh", label: "Outdoor (-30C to 70C)" },
        ],
      };
      setMessages((prev) => [...prev, userMsg, botMsg]);
      return;
    }

    const userMsg: Message = { id: `u-${Date.now()}`, role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);
    setDisabled(true);

    try {
      const req: ChatRequest = { message: text, history: buildHistory() };
      const resp = await sendChatMessage(req);

      const typedResp = resp as ChatResponse;
      const normalizedBotText = normalizeBotText(typedResp.text);

      const botMsg: Message = {
        id: `b-${Date.now()}`,
        role: "bot",
        text: normalizedBotText,
        quickReplies: typedResp.quick_replies || undefined,
      };
      if (typedResp.type === "question" || typedResp.type === "clarification") {
        botMsg.type = "multipleChoice";
        botMsg.choices = (botMsg.quickReplies || []).map((label: string, idx: number) => ({
          id: `choice-${Date.now()}-${idx}`,
          label,
        }));
      }

      let hw: any = null;
      if (typedResp.type === "recommendation" && typedResp.recommendation?.hardware_items?.length) {
        hw = typedResp.recommendation.hardware_items[0];
      }

      if (hw) {
        const product: Product = {
          name: hw.name ?? hw.model_name ?? hw.hardware_name ?? "Product",
          sku: hw.sku ?? (hw.model && hw.model.sku) ?? "",
          description: typedResp.recommendation?.explanation ?? hw.role ?? JSON.stringify(hw),
        };
        botMsg.product = product;
      }

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const errMsg: Message = { id: `e-${Date.now()}`, role: "bot", text: `Error: ${String(err)}` };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsTyping(false);
      setDisabled(false);
    }
  };

  return (
    <Router>
      <Routes>
        <Route path="/" element={
          <div className="flex flex-col items-center">
            <button
              type="button"
              onClick={() => setIsLightTheme((prev) => !prev)}
              className="fixed left-4 top-4 z-50 rounded-full border px-3 py-1 text-xs text-primary chat-bg"
              style={{ borderColor: "var(--border)" }}
            >
              {isLightTheme ? "Dark Mode" : "Light Mode"}
            </button>
            <h1 className="text-primary text-center">IDTECH Suggestion Engine</h1>
            <ChatWindow messages={messages} onSend={onSend} isTyping={isTyping} disabled={disabled} />
            {/* <div className="mt-4">
              <ForceRecommendationButton
                buildHistory={buildHistory}
                setMessages={setMessages}
                setIsTyping={setIsTyping}
                setDisabled={setDisabled}
                disabled={disabled}
              />
            </div> */}
          </div>
        } />

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
