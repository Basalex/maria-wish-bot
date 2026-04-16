import os
import json
import logging
from datetime import datetime
from google import genai

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set")
        _client = genai.Client(api_key=api_key)
    return _client

_SYSTEM_PROMPT_TEMPLATE = """You are a "Wife Concierge" bot. You help a husband track what his wife Maria wants, remember important dates, and save notes about her preferences.

Current date/time: {now}

─── SAVED WISHES ───
{wishes_text}

─── IMPORTANT DATES ───
{dates_text}

─── PREFERENCE NOTES ───
{notes_text}

Respond ONLY with valid JSON using this exact schema:
{{
  "reply": "string — message to send the user",
  "actions": [
    {{
      "type": "save_wish" | "save_date" | "save_note" | "suggest_gift" | "list_wishes" | "list_notes" | "list_all",
      "wish": {{
        "title": "string",
        "description": "string",
        "price_range": "string",
        "link": "string"
      }},
      "date": {{
        "title": "string",
        "event_date": "YYYY-MM-DD",
        "reminder_days": integer
      }},
      "note": {{
        "content": "string",
        "category": "preference" | "place" | "event" | "other"
      }},
      "budget_request": "string"
    }}
  ]
}}

Action rules:
• "save_wish" — user mentions something Maria wants. If user sends a list, create multiple "save_wish" actions in the "actions" array.
• "save_date" — user mentions an important date.
• "save_note" — user mentions a preference or useful info.
• "suggest_gift" — user asks for ideas based on history or budget.
• "list_wishes" — user wants to see the list of wishes.
• "list_notes" — user wants to see the list of notes.
• "list_all" — user wants to see everything.

If the user just asks to "show wishes" or "what does she want?", use "list_wishes".
If the user sends a list like "1. Dress 2. Shoes 3. Flowers", create THREE "save_wish" actions.

Always be supportive and helpful."""

def _build_wishes_text(wishes: list) -> str:
    if not wishes: return "(no wishes saved yet)"
    return "\n".join([f"• [ID: {w['id']}] {w['title']} ({w.get('price_range', 'unknown price')})" for w in wishes])

def _build_dates_text(dates: list) -> str:
    if not dates: return "(no important dates saved yet)"
    return "\n".join([f"• {d['title']}: {d['event_date']}" for d in dates])

def _build_notes_text(notes: list) -> str:
    if not notes: return "(no notes saved yet)"
    return "\n".join([f"• [ID: {n['id']}] {n['content']} (category: {n.get('category', 'other')})" for n in notes])

async def process_message(user_id: int, message_text: str, context: dict) -> dict:
    client = _get_client()
    
    prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        now=datetime.now().strftime("%Y-%m-%d %H:%M"),
        wishes_text=_build_wishes_text(context.get('wishes', [])),
        dates_text=_build_dates_text(context.get('dates', [])),
        notes_text=_build_notes_text(context.get('notes', []))
    )
    
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents=message_text,
        config={
            'system_instruction': prompt,
            'response_mime_type': 'application/json'
        }
    )
    
    try:
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Failed to parse AI response: {response.text}")
        return {"reply": "Sorry, I had trouble processing that.", "actions": []}
