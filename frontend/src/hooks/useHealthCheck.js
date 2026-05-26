import { useEffect, useRef, useState } from "react";

import { checkHealth } from "../services/api";

const RETRY_MS = 2000;

export default function useHealthCheck() {
  const [status, setStatus] = useState("checking");
  const [errorMessage, setErrorMessage] = useState("");
  const timerRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    const probe = async () => {
      const result = await checkHealth();
      if (cancelled) {
        return;
      }

      if (result.ok && result.data?.ok) {
        setStatus("ready");
        setErrorMessage("");
        return;
      }

      setStatus("checking");
      setErrorMessage(result.message ?? "Backend is still warming up.");
      timerRef.current = window.setTimeout(probe, RETRY_MS);
    };

    probe();
    return () => {
      cancelled = true;
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
      }
    };
  }, []);

  return {
    isReady: status === "ready",
    status,
    errorMessage,
  };
}
