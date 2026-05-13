import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useCallback, useEffect, useRef, useState } from 'react';
import Dashboard from "./pages/maintenance/Dashboard"
import HardwareManager from "./pages/maintenance/HardwareManager"
import SoftwareManager from "./pages/maintenance/SoftwareManager"
import PromptManager from "./pages/maintenance/PromptManager"
import DocManager from "./pages/maintenance/DocManager"
import ChatWindow from "./components/ChatWindow"
import DebugPanel from "./components/DebugPanel"
import type { Message, Product } from "./types/messages"
import { createSession, sendChatMessage, type ChatResponse } from "./api/client"

const normalizeBotText = (raw: string): string => {
  const lines = raw
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => {
      let normalized = line.replace(/^\d+\.\s*/, "");
      normalized = normalized.replace(/^"(.*)"$/, "$1");
      return normalized.trim();
    });

  return lines.join("\n\n");
};

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [disabled, setDisabled] = useState(false);
  const [isLightTheme, setIsLightTheme] = useState(true);

  // State machine tracking — accumulated structured data and current phase
  const [collectedInfo, setCollectedInfo] = useState<Record<string, unknown>>({});
  const [nextState, setNextState] = useState<string | undefined>(undefined);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);

  // Keep a ref to the latest collectedInfo so the onSend closure always has fresh data
  const collectedInfoRef = useRef(collectedInfo);
  collectedInfoRef.current = collectedInfo;

  useEffect(() => {
    document.body.classList.toggle("light-theme", isLightTheme);
  }, [isLightTheme]);

  useEffect(() => {
    const initSession = async () => {
      try {
        const session = await createSession();
        setSessionId(session.session_id);
        setNextState(session.stage);
        setMessages([
          {
            id: `welcome-${Date.now()}`,
            role: "bot",
            text: session.message,
          },
        ]);
      } catch (err) {
        setMessages([
          {
            id: `welcome-error-${Date.now()}`,
            role: "bot",
            text: `Error: ${String(err)}`,
          },
        ]);
      }
    };
    void initSession();
  }, []);

  const onSend = useCallback(async (text: string) => {
    const userMsg: Message = { id: `u-${Date.now()}`, role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);
    setDisabled(true);

    try {
      const req = {
        message: text,
        session_id: sessionId,
      };
      const resp: ChatResponse = await sendChatMessage(req);
      if (resp.session_id) {
        setSessionId(resp.session_id);
      }

      const cleanedText = normalizeBotText(resp.text);

      // Build the bot message
      const botMsg: Message = {
        id: `b-${Date.now()}`,
        role: "bot",
        text: cleanedText,
        quickReplies: resp.quick_replies || undefined,
      };

      // If it's a question or clarification, render quick replies as multiple-choice buttons
      if (resp.type === "question" || resp.type === "clarification") {
        botMsg.type = "multipleChoice";
        botMsg.choices = (botMsg.quickReplies || []).map((label: string, idx: number) => ({
          id: `choice-${Date.now()}-${idx}`,
          label,
        }));
      }

      // Merge new_info into collectedInfo (state machine data from LLM tool call)
      const mergedInfo = { ...collectedInfoRef.current };
      if (resp.new_info) {
        // Handle __state_override: if the backend overrides the state, use it directly
        const override = (resp.new_info as Record<string, unknown>)["__state_override"];
        if (typeof override === "string") {
          setNextState(override);
        }

        // Merge all extracted fields (deep merge for nested objects)
        for (const [key, value] of Object.entries(resp.new_info)) {
          if (key === "__state_override") continue;
          if (value !== null && typeof value === "object" && !Array.isArray(value)) {
            // Nested object (environment, technical_context, etc.) — merge at the sub-key level
            mergedInfo[key] = { ...(mergedInfo[key] as Record<string, unknown> || {}), ...value as Record<string, unknown> };
          } else if (value !== undefined) {
            mergedInfo[key] = value;
          }
        }
      }

      // If the backend returned a next_state, track it
      if (resp.next_state) {
        setNextState(resp.next_state);
      }

      // Update collectedInfo state
      setCollectedInfo(mergedInfo);

      // Store state info on the message for debugging / future use
      botMsg.collectedInfo = mergedInfo;
      botMsg.nextState = resp.next_state ?? nextState;

      // Build product card for recommendation responses
      if (resp.type === "recommendation" && resp.recommendation?.hardware_items?.length) {
        const hw = resp.recommendation.hardware_items[0];
        const product: Product = {
          name: hw.name ?? "Product",
          sku: (hw.technical_specs?.model_name as string) ?? "",
          description: resp.recommendation.explanation ?? hw.role,
        };
        botMsg.product = product;
      }

      // Handle ui_actions (future: show lead form, offer booking)
      if (resp.ui_actions && resp.ui_actions.length > 0) {
        console.log("[ui_actions]", resp.ui_actions);
      }

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const errMsg: Message = { id: `e-${Date.now()}`, role: "bot", text: `Error: ${String(err)}` };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsTyping(false);
      setDisabled(false);
    }
  }, [messages, nextState]);

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
      <DebugPanel collectedInfo={collectedInfo} nextState={nextState} messageCount={messages.length} />
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
