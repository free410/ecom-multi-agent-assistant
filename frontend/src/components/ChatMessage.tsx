import ReactMarkdown from "react-markdown";

interface ChatMessageProps {
  role: string;
  content: string;
  streaming?: boolean;
}

export function ChatMessage({ role, content, streaming = false }: ChatMessageProps) {
  const isAssistant = role === "assistant";

  return (
    <div className={`message-row ${isAssistant ? "assistant" : "user"}`}>
      <article className={`message ${isAssistant ? "assistant" : "user"} ${streaming ? "streaming" : ""}`}>
        <div className="message-role">{isAssistant ? "AI" : "我"}</div>
        <div className="message-body">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </article>
    </div>
  );
}
