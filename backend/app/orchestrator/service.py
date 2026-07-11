from ..ai import get_model_router, AIRequest

# ... [rest of function context]
    model_router = get_model_router(settings)
    ai_req = AIRequest(task_type='chat', prompt=message)
    try:
        ai_resp = model_router.route(ai_req)
        out_text = ai_resp.content
    except Exception as exc:
        out_text = "[AI Router error: " + str(exc) + "]"
    # End refactor point: out_text replaces use of _call_groq_api
    raw_llm_response = out_text
# ... [rest of function context]
