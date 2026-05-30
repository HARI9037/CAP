const BASE_URL = import.meta.env.VITE_API_URL || "https://cap-mvp.onrender.com";

async function readJsonResponse(res) {
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        throw new Error(data.detail || data.error || `Request failed with status ${res.status}`);
    }
    return data;
}

/**
 * Sends a message to the backend within a new or ongoing session context.
 */
export async function sendMessage(message, session_id = null) {
    const res = await fetch(`${BASE_URL}/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            message,
            session_id,
        }),
    });

    return readJsonResponse(res);
}

/**
 * Checks the live engine availability state.
 */
export async function getHealth() {
    const res = await fetch(`${BASE_URL}/health`);
    return readJsonResponse(res);
}

/**
 * Loads memory and history for a prior session.
 */
export async function getMemory(sessionId) {
    const res = await fetch(`${BASE_URL}/memory?session_id=${encodeURIComponent(sessionId)}`);
    return readJsonResponse(res);
}

/**
 * Permanently removes a target session sequence from the backend database indices.
 */
export async function deleteSession(sessionId) {
    const res = await fetch(`${BASE_URL}/memory?session_id=${encodeURIComponent(sessionId)}`, {
        method: "DELETE",
    });

    return readJsonResponse(res);
}

/**
 * Approves or rejects a pending action via the CAP confirmation gate.
 */
export async function confirmAction(actionId, actionType, approved, sessionId) {
    const res = await fetch(`${BASE_URL}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            action_id: actionId,
            action_type: actionType,
            approved: approved,
            session_id: sessionId,
        }),
    });
    return readJsonResponse(res);
}
