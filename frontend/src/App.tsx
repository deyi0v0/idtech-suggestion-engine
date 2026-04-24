import { useRef, useState, useEffect } from "react";
import ChatWindow from "./components/ChatWindow";
import type { Message, Product } from "./types/messages";
import GenericButton from "./components/GenericButton";
import ProductModal from "./components/ProductModal";

const demoQuestions: Message[] = [
  {
    id: "demo-q-1",
    role: "bot",
    text: "Which product category are you interested in?",
    type: "multipleChoice",
    choices: [
      { id: "c1", label: "Hardware" },
      { id: "c2", label: "Software" },
    ],
  },
  {
    id: "demo-q-2",
    role: "bot",
    text: "What form factor do you prefer?",
    type: "multipleChoice",
    choices: [
      { id: "c1", label: "Desktop" },
      { id: "c2", label: "Integrated" },
    ],
  },
  {
    id: "demo-q-3",
    role: "bot",
    text: "Do you need contactless payment support?",
    type: "multipleChoice",
    choices: [
      { id: "c1", label: "Yes" },
      { id: "c2", label: "No" },
    ],
  },
];

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [modalProduct, setModalProduct] = useState<Product | null>(null);
  const demoIndex = useRef<number>(-1);
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
    const prevDemo = demoIndex.current;
    const nextDemo = prevDemo === -1 ? 0 : prevDemo + 1;
    demoIndex.current = nextDemo;

    setMessages((prev) => {
      const newArr = prev.slice();

      if (prevDemo >= 0) {
        for (let i = newArr.length - 1; i >= 0; i--) {
          const m = newArr[i];
          if (
            m.role === "bot" &&
            (m.type === "multipleChoice" || (m.choices && m.choices.length > 0)) &&
            !m.answered
          ) {
            newArr[i] = { ...m, answered: true, selectedChoice: text };
            break;
          }
        }
      }

      newArr.push({ id: Date.now().toString(), role: "user", text });
      return newArr;
    });

    if (nextDemo >= 0 && nextDemo < demoQuestions.length) {
      setIsTyping(true);
      await new Promise((r) => setTimeout(r, 500));
      const nextQ = demoQuestions[nextDemo];
      setMessages((prev) => [...prev, { ...nextQ, id: (Date.now() + 1).toString() }]);
      setIsTyping(false);
    } else if (nextDemo >= demoQuestions.length) {
      setIsTyping(true);
      await new Promise((r) => setTimeout(r, 500));
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "bot",
          text: "Thanks! Based on your answers I'll narrow down some recommended products.",
          product: {
            name: "Product A",
            sku: "12345",
            description: "Covers common use-cases and matches your compatibility requirements.",
          },
        },
      ]);
      setIsTyping(false);
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
