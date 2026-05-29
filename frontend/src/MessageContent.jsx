function renderInline(text) {
  const parts = [];
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let cursor = 0;
  let match;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > cursor) {
      parts.push(text.slice(cursor, match.index));
    }

    const token = match[0];
    if (token.startsWith("**")) {
      parts.push(
        <strong key={`${match.index}-bold`} className="font-semibold text-white">
          {token.slice(2, -2)}
        </strong>
      );
    } else {
      parts.push(
        <code
          key={`${match.index}-code`}
          className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[0.92em] text-slate-100"
        >
          {token.slice(1, -1)}
        </code>
      );
    }

    cursor = match.index + token.length;
  }

  if (cursor < text.length) {
    parts.push(text.slice(cursor));
  }

  return parts;
}

function normalizeContent(content) {
  return String(content)
    .replace(/\\n/g, "\n")
    .replace(/\r\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function splitBlocks(content) {
  const normalized = normalizeContent(content);
  if (!normalized) return [];

  return normalized
    .split(/\n\s*\n/)
    .map((block) => block.trim())
    .filter(Boolean);
}

function listType(lines) {
  if (lines.every((line) => /^[-*]\s+/.test(line))) return "bullet";
  if (lines.every((line) => /^\d+\.\s+/.test(line))) return "numbered";
  return null;
}

function renderBlock(block, index) {
  const lines = block
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  const type = listType(lines);

  if (type) {
    const Tag = type === "numbered" ? "ol" : "ul";
    return (
      <Tag
        key={index}
        className={`my-3 space-y-2 pl-6 ${
          type === "numbered" ? "list-decimal" : "list-disc"
        }`}
      >
        {lines.map((line, lineIndex) => (
          <li key={lineIndex} className="pl-1">
            {renderInline(line.replace(/^([-*]|\d+\.)\s+/, ""))}
          </li>
        ))}
      </Tag>
    );
  }

  if (lines.length === 1) {
    const heading = lines[0].match(/^\*\*(.+):\*\*$/);
    if (heading) {
      return (
        <h3 key={index} className="mb-2 mt-5 text-[15px] font-semibold text-white">
          {heading[1]}
        </h3>
      );
    }
  }

  return (
    <p key={index} className="my-3">
      {lines.map((line, lineIndex) => (
        <span key={lineIndex}>
          {lineIndex > 0 && <br />}
          {renderInline(line)}
        </span>
      ))}
    </p>
  );
}

export default function MessageContent({ content, compact = false }) {
  const blocks = splitBlocks(content);

  if (blocks.length === 0) return null;

  return (
    <div
      className={`message-content text-left ${
        compact ? "space-y-2" : "space-y-1"
      }`}
    >
      {blocks.map(renderBlock)}
    </div>
  );
}
