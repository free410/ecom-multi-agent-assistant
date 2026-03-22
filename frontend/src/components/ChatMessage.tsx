import ReactMarkdown from "react-markdown";

interface ChatMessageProps {
  role: string;
  content: string;
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  return (
    <article className={`message ${role === "assistant" ? "assistant" : "user"}`}>
      <div className="message-role">{role === "assistant" ? "AI" : "我"}</div>
      <div className="message-body">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </article>
  );
}

