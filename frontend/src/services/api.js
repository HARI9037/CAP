const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

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

    return await res.json();
}

export async function getHealth() {
    const res = await fetch(`${BASE_URL}/health`);
    return await res.json();
}

export async function getReady() {
    const res = await fetch(`${BASE_URL}/ready`);
    return await res.json();
}