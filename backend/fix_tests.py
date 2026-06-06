import os
import re

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replacements for missing user_id args in tests
    content = content.replace('memory_store.ensure_session(session_id=', 'memory_store.ensure_session(user_id="test-user", session_id=')
    content = content.replace('memory_store.ensure_session("', 'memory_store.ensure_session(user_id="test-user", session_id="')
    content = content.replace('memory_store.store_pending_actions(session_id, ', 'memory_store.store_pending_actions(session_id, "test-user", ')
    content = content.replace('memory_store.store_pending_actions("', 'memory_store.store_pending_actions("')
    # manual regex for store_pending_actions to add test-user
    content = re.sub(r'memory_store\.store_pending_actions\(([^,]+),\s*\[', r'memory_store.store_pending_actions(\1, "test-user", [', content)
    
    content = re.sub(r'memory_store\.append_message\(([^,]+),\s*([^,]+),\s*([^)]+)\)', r'memory_store.append_message(\1, \2, \3, "test-user")', content)
    
    # manual replace for chat route
    content = re.sub(r'client\.post\(\s*"/chat"', r'client.post("/chat", headers={"Authorization": "Bearer test_clerk_token_123"}', content)
    content = re.sub(r'client\.post\(\s*"/confirm"', r'client.post("/confirm", headers={"Authorization": "Bearer test_clerk_token_123"}', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

for root, _, files in os.walk('tests'):
    for file in files:
        if file.endswith('.py'):
            process_file(os.path.join(root, file))
print("Tests updated")
