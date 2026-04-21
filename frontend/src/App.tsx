import { useRef, useState } from "react";
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

  const handleSend = async (text: string) => {
    // append user message
    setMessages((prev) => [...prev, { id: Date.now().toString(), role: "user", text }]);

    // Determine next step in demo sequence
    if (demoIndex.current === -1) {
      // start sequence: ask first question
      demoIndex.current = 0;
    } else {
      // user answered previous question; advance to next
      demoIndex.current += 1;
    }

    if (demoIndex.current >= 0 && demoIndex.current < demoQuestions.length) {
      setIsTyping(true);
      await new Promise((r) => setTimeout(r, 500));
      const nextQ = demoQuestions[demoIndex.current];
      setMessages((prev) => [...prev, { ...nextQ, id: (Date.now() + 1).toString() }]);
      setIsTyping(false);
    } else if (demoIndex.current >= demoQuestions.length) {
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
      <ChatWindow messages={messages} onSend={handleSend} isTyping={isTyping} />
      <GenericButton />
    </div>
  );
}

export default App;
