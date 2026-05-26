import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_URL;

const client = apiBaseUrl
  ? axios.create({
      baseURL: apiBaseUrl,
      timeout: 10000,
    })
  : null;

function configErrorResponse() {
  return {
    ok: false,
    message: "Missing VITE_API_URL configuration.",
    status: 500,
  };
}

function toErrorResponse(error) {
  return {
    ok: false,
    message:
      error?.response?.data?.detail ??
      error?.message ??
      "Backend request failed.",
    status: error?.response?.status ?? 500,
  };
}

export async function checkHealth() {
  if (!client) {
    return configErrorResponse();
  }
  try {
    const { data } = await client.get("/health");
    return { ok: true, data };
  } catch (error) {
    return toErrorResponse(error);
  }
}

export async function sendMessage(prompt, sessionId) {
  if (!client) {
    return configErrorResponse();
  }
  try {
    const { data } = await client.post("/chat", {
      prompt,
      session_id: sessionId ?? null,
    });
    return { ok: true, data };
  } catch (error) {
    return toErrorResponse(error);
  }
}

export async function getMemory(sessionId) {
  if (!client) {
    return configErrorResponse();
  }
  try {
    const { data } = await client.get("/memory", {
      params: sessionId ? { session_id: sessionId } : undefined,
    });
    return { ok: true, data };
  } catch (error) {
    return toErrorResponse(error);
  }
}

export async function confirmAction(actionId, actionType, approved) {
  if (!client) {
    return configErrorResponse();
  }
  try {
    const { data } = await client.post("/confirm", {
      action_id: actionId,
      action_type: actionType,
      approved,
    });
    return { ok: true, data };
  } catch (error) {
    return toErrorResponse(error);
  }
}
