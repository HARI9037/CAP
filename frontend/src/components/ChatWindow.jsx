import MessageBubble from "./MessageBubble";

function ChatWindow({ messages }) {
  return (
    <section className="flex h-[60vh] flex-col gap-3 overflow-y-auto rounded-md border border-slate-800 bg-slate-900 p-4">
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          role={message.role}
          content={message.content}
          timestamp={message.timestamp}
        />
      ))}
    </section>
  );
}

export default ChatWindow;
