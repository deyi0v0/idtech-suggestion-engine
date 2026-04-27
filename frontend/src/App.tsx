import { useRef, useState, useEffect } from "react";
import ChatWindow from "./components/ChatWindow";
import type { Message, Product } from "./types/messages";
import GenericButton from "./components/GenericButton";
import ProductModal from "./components/ProductModal";
import { sendChatMessage, type ChatHistoryItem } from "./api/client";

type ChatApiResponse = Record<string, unknown>;

const onboardingQuestions: Message[] = [
  {
    id: "onboard-q-1",
    role: "bot",
    text: "Which product category are you interested in?",
    type: "multipleChoice",
    choices: [
      { id: "c1", label: "Hardware" },
      { id: "c2", label: "Software" },
    ],
  },
  {
    id: "onboard-q-2",
    role: "bot",
    text: "What form factor do you prefer?",
    type: "multipleChoice",
    choices: [
      { id: "c1", label: "Desktop" },
      { id: "c2", label: "Integrated" },
    ],
  },
  {
    id: "onboard-q-3",
    role: "bot",
    text: "Do you need contactless payment support?",
    type: "multipleChoice",
    choices: [
      { id: "c1", label: "Yes" },
      { id: "c2", label: "No" },
    ],
  },
];

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object" && "label" in item && typeof item.label === "string") {
        return item.label;
      }
      return "";
    })
    .filter((item) => item.length > 0);
}

function asBoolean(value: unknown): boolean {
  return typeof value === "boolean" ? value : false;
}

function buildFallbackRecommendationMessage(): Message {
  const fallbackProduct: Product = {
    name: "ID TECH Recommended Bundle",
    sku: "Recommended",
    description:
      "We could not retrieve a live backend recommendation, so this is a temporary suggested bundle. Please review with support for final device selection.",
  };

  return {
    id: `bot-fallback-${Date.now()}`,
    role: "bot",
    text: "I have enough information to recommend a product. Open the recommendation details below.",
    product: fallbackProduct,
  };
}

function mapApiResponseToMessage(response: ChatApiResponse): Message {
  const content = typeof response.content === "string" ? response.content : "";
  const choices = asStringArray(response.choices);

  if (content) {
    return {
      id: `bot-${Date.now()}`,
      role: "bot",
      text: content,
      type: choices.length > 0 ? "multipleChoice" : "text",
      choices: choices.length > 0 ? choices.map((label, index) => ({ id: `choice-${index}`, label })) : undefined,
    };
  }

  const hardwareName = typeof response.hardware_name === "string" ? response.hardware_name : "";
  if (hardwareName) {
    const softwareName = typeof response.software_name === "string" ? response.software_name : "";
    const highlights = asStringArray(response.highlights);
    const explanation =
      typeof response.explanation === "string"
        ? response.explanation
        : "Your recommendation is ready.";

    const details = [softwareName ? `Software: ${softwareName}` : "", ...highlights]
      .filter(Boolean)
      .join(" | ");

    return {
      id: `bot-${Date.now()}`,
      role: "bot",
      text: explanation,
      product: {
        name: hardwareName,
        sku: "Recommended",
        description: details || explanation,
      },
    };
  }

  const explanation =
    typeof response.explanation === "string" ? response.explanation : "I can help with that. Tell me more.";

  return {
    id: `bot-${Date.now()}`,
    role: "bot",
    text: explanation,
  };
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { ...onboardingQuestions[0], id: `onboard-initial-${Date.now()}` },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [modalProduct, setModalProduct] = useState<Product | null>(null);
  const historyRef = useRef<ChatHistoryItem[]>([
    { role: "assistant", content: onboardingQuestions[0].text },
  ]);
  const [onboardingIndex, setOnboardingIndex] = useState(0);
  const [onboardingComplete, setOnboardingComplete] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("light");

  const applyTheme = (t: "dark" | "light") => {
    if (t === "light") {
      document.body.classList.add("light-theme");
    } else {
      document.body.classList.remove("light-theme");
    }
  };

  useEffect(() => {
    applyTheme(theme);
  }, []);

  const handleSend = async (text: string) => {
    if (!text.trim() || isSending) return;

    const priorHistory = historyRef.current;

    setMessages((prev) => {
      const updated = prev.slice();

      for (let i = updated.length - 1; i >= 0; i--) {
        const message = updated[i];
        if (
          message.role === "bot" &&
          (message.type === "multipleChoice" || (message.choices && message.choices.length > 0)) &&
          !message.answered
        ) {
          updated[i] = { ...message, answered: true, selectedChoice: text };
          break;
        }
      }

      updated.push({ id: `user-${Date.now()}`, role: "user", text });
      return updated;
    });

    if (!onboardingComplete) {
      if (onboardingIndex < onboardingQuestions.length - 1) {
        setIsTyping(true);
        await new Promise((resolve) => setTimeout(resolve, 350));

        const nextQuestion = onboardingQuestions[onboardingIndex + 1];
        const nextQuestionMessage: Message = {
          ...nextQuestion,
          id: `onboard-${onboardingIndex + 1}-${Date.now()}`,
        };

        setMessages((prev) => [...prev, nextQuestionMessage]);
        historyRef.current = [
          ...priorHistory,
          { role: "user", content: text },
          { role: "assistant", content: nextQuestionMessage.text },
        ];
        setOnboardingIndex((prev) => prev + 1);
        setIsTyping(false);
        return;
      }

      setOnboardingComplete(true);
    }

    setIsSending(true);
    setIsTyping(true);

    try {
      const response = await sendChatMessage({
        message: text,
        history: priorHistory,
      });

      const botMessage = mapApiResponseToMessage(response);

      setMessages((prev) => [...prev, botMessage]);
      if (botMessage.product && asBoolean(response.show_recommendation_modal)) {
        setModalProduct(botMessage.product);
      }
      historyRef.current = [
        ...priorHistory,
        { role: "user", content: text },
        { role: "assistant", content: botMessage.text },
      ];
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      const shouldFallbackToRecommendation = onboardingComplete;

      if (shouldFallbackToRecommendation) {
        const fallbackMessage = buildFallbackRecommendationMessage();
        setMessages((prev) => [...prev, fallbackMessage]);
        setModalProduct(fallbackMessage.product ?? null);
        historyRef.current = [
          ...priorHistory,
          { role: "user", content: text },
          { role: "assistant", content: fallbackMessage.text },
        ];
      } else {
        const errorText = `Backend request failed: ${message}`;
        setMessages((prev) => [
          ...prev,
          {
            id: `bot-error-${Date.now()}`,
            role: "bot",
            text: errorText,
          },
        ]);
        historyRef.current = [
          ...priorHistory,
          { role: "user", content: text },
          { role: "assistant", content: errorText },
        ];
      }
    } finally {
      setIsTyping(false);
      setIsSending(false);
    }
  };

  return (
    <div className="flex flex-col items-center w-full">
      <div className="w-full flex justify-end px-8 py-4">
        <GenericButton
          onClick={() => {
            const next = theme === "dark" ? "light" : "dark";
            setTheme(next);
            applyTheme(next);
          }}
          className="rounded-md bg-green-700 px-3 py-1"
        >
          {theme === "dark" ? "Light" : "Dark"}
        </GenericButton>
      </div>
      <div className="flex flex-row w-full">
        <div className="flex-1 border-4 border-r-0 flex items-center justify-around" style={{ borderColor: "var(--border)" }}>
          <p className="italic text-gray-500">IDTECH Products Website Content</p>
        </div>
        <ChatWindow
          messages={messages}
          onSend={handleSend}
          isTyping={isTyping}
          disabled={isSending}
          onShowProduct={(product) => setModalProduct(product)}
        />
      </div>
      {modalProduct && (
        <ProductModal product={modalProduct} onClose={() => setModalProduct(null)} />
      )}
    </div>
  );
}

export default App;
