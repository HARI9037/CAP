import { useEffect, useState } from "react";

import { getMemory } from "../services/api";

const EMPTY_SUMMARY = {
  session_id: null,
  summary: "",
  message_count: 0,
  updated_at: null,
};

export default function useMemory(sessionId, enabled) {
  const [summary, setSummary] = useState(EMPTY_SUMMARY);
  const [isLoading, setIsLoading] = useState(false);

  const refresh = async () => {
    if (!enabled) {
      return { ok: false, message: "Health check is not ready." };
    }
    setIsLoading(true);
    const response = await getMemory(sessionId);
    if (response.ok) {
      setSummary(response.data?.memory ?? EMPTY_SUMMARY);
    }
    setIsLoading(false);
    return response;
  };

  useEffect(() => {
    if (!enabled) {
      return;
    }
    refresh();
  }, [sessionId, enabled]);

  return {
    summary,
    isLoading,
    refresh,
  };
}
