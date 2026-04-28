import sys
sys.stdout.reconfigure(encoding='utf-8')
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from store.chatbot_orchestrator import HybridChatbotOrchestrator
from store.chatbot_service import ChatbotService

orch = HybridChatbotOrchestrator()
cs = ChatbotService()

class FakeSession(dict):
    modified = False

# Step 1: Compare
print('=== STEP 1: So sanh iPhone Air vs iPhone 15 ===')
session = FakeSession()
msg1 = 'so sanh iphone air va iphone 15'
intent1 = cs.detect_intent(msg1)
products1 = cs.detect_product_names(msg1)
print(f'  intent={intent1}, products={products1}')
result1 = orch.process_message(msg1, session=session)
print(f'  engine={result1.get("engine")}, source={result1.get("source")}')
lines = result1.get('message', '').split('\n')
for l in lines[:6]:
    print(f'  | {l[:120]}')
print(f'  [session keys: {list(session.keys())}]')
print(f'  last_recommended: {session.get("qh_chatbot_last_recommended")}')
print(f'  focused_product: {session.get("qh_chatbot_focused_product")}')
print()

# Step 2: Follow-up question
print('=== STEP 2: Tai sao iPhone Air dat hon? ===')
session2 = FakeSession(session)  # copy
msg2 = 'tai sao iphone air dat hon vay? explain'
intent2 = cs.detect_intent(msg2)
products2 = cs.detect_product_names(msg2)
print(f'  intent={intent2}, products={products2}')
result2 = orch.process_message(msg2, session=session2)
print(f'  engine={result2.get("engine")}, source={result2.get("source")}')
lines2 = result2.get('message', '').split('\n')
for l in lines2[:6]:
    print(f'  | {l[:120]}')
print()

# Step 3: Confirm
print('=== STEP 3: Muon mua iPhone Air ===')
session3 = FakeSession(session)  # continue from compare session
msg3 = 'vay lay iphone air'
intent3 = cs.detect_intent(msg3)
products3 = cs.detect_product_names(msg3)
print(f'  intent={intent3}, products={products3}')
result3 = orch.process_message(msg3, session=session3)
print(f'  engine={result3.get("engine")}, source={result3.get("source")}')
lines3 = result3.get('message', '').split('\n')
for l in lines3[:5]:
    print(f'  | {l[:120]}')
