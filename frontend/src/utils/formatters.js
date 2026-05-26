export function formatTimestamp(rawTimestamp) {
  if (!rawTimestamp) {
    return "--";
  }
  const timestamp = new Date(rawTimestamp);
  if (Number.isNaN(timestamp.getTime())) {
    return "--";
  }
  return timestamp.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function truncateText(text, maxLength = 80) {
  if (!text || text.length <= maxLength) {
    return text ?? "";
  }
  return `${text.slice(0, maxLength - 1)}...`;
}

export function parseConfirmationPayload(payload) {
  const parsed = Array.isArray(payload) ? payload : [];
  return parsed.map((action) => ({
    actionId: action.action_id ?? "",
    actionType: action.action_type ?? "unknown",
    title: action.title ?? "Pending action",
    description: action.description ?? "",
  }));
}
