import { useRef, useState, useEffect } from "react";
import ChatWindow from "./components/ChatWindow";
import type { Message } from "./types/messages";
import GenericButton from "./components/GenericButton";

// Demo multiple-choice questions sequence
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
  // -1 means demo not started, otherwise index of last asked question
  const demoIndex = useRef<number>(-1);
  const [theme, setTheme] = useState<"dark" | "light">("light");

  // apply theme class to body
  const applyTheme = (t: "dark" | "light") => {
    if (t === "light") {
      document.body.classList.add("light-theme");
    } else {
      document.body.classList.remove("light-theme");
    }
  };

  // initialize theme
  useEffect(() => {
    applyTheme(theme);
  }, []);

  const handleSend = async (text: string) => {
    const prevDemo = demoIndex.current;
    const nextDemo = prevDemo === -1 ? 0 : prevDemo + 1;
    demoIndex.current = nextDemo;

    // Mark the most recent unanswered multiple-choice bot message as answered and append the user message
    setMessages((prev) => {
      const newArr = prev.slice();

      if (prevDemo >= 0) {
        // find last bot multiple-choice message that is not answered
        for (let i = newArr.length - 1; i >= 0; i--) {
          const m = newArr[i] as Message;
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
      // finished sequence: show final summary reply
      setIsTyping(true);
      await new Promise((r) => setTimeout(r, 500));
      const reply = `Thanks! Based on your answers I'll narrow down some recommended products.`;
      setMessages((prev) => [...prev, { id: (Date.now() + 1).toString(), role: "bot", text: reply }]);
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
      <ChatWindow messages={messages} onSend={handleSend} isTyping={isTyping} />
    </div>
  );
}

export default App;
