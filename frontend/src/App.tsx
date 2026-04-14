import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import type { Message } from "./components/ChatWindow";

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = async (text: string) => {
    setMessages((prev) => [...prev, { id: Date.now().toString(), role: "user", text }]);
    setIsTyping(true);

    await new Promise((r) => setTimeout(r, 500));
    const reply = `Demo assistant: Based on your input, I recommend Product A (SKU: 12345) — it covers common use-cases and matches compatibility requirements.`;

    setMessages((prev) => [...prev, { id: (Date.now() + 1).toString(), role: "bot", text: reply }]);
    setIsTyping(false);
  };

  return (
    <div className="flex flex-col items-center w-full">
      <h1 className="text-white text-center">IDTECH Suggestion Engine</h1>
      <ChatWindow messages={messages} onSend={handleSend} isTyping={isTyping} />
    </div>
  );
}

export default App;
