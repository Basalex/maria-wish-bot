import os
import json
import logging
import asyncio
from datetime import datetime
from google import genai

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("CRITICAL: GEMINI_API_KEY is NOT found in environment variables!")
            raise RuntimeError("GEMINI_API_KEY environment variable is not set")
        logger.info(f"Initializing Gemini Client with API Key starting with: {api_key[:4]}...")
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
      "type": "save_wish" | "save_date" | "save_note" | "save_gift" | "suggest_gift" | "list_wishes" | "list_notes" | "list_dates" | "show_stats",
      "wish": {{ "title": "string", "description": "string", "price_range": "string", "link": "string" }},
      "date": {{ "title": "string", "event_date": "YYYY-MM-DD", "reminder_days": integer }},
      "note": {{ "content": "string", "category": "preference" | "place" | "event" | "other" }},
      "gift": {{ "title": "string", "is_without_reason": boolean, "wish_id": integer | null }},
      "budget_request": "string"
    }}
  ]
}}

Action rules:
• "save_gift" — user says he gave a gift. 
• "show_stats" — user asks about gift statistics or last gift without reason.
• "list_dates" — user wants to see important dates.
• "save_wish", "save_date", "save_note" - as described before.

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

def _run_gemini(message_text: str, context: dict) -> dict:
    client = _get_client()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        now=now,
        wishes_text=_build_wishes_text(context.get('wishes', [])),
        dates_text=_build_dates_text(context.get('dates', [])),
        notes_text=_build_notes_text(context.get('notes', []))
    )
    
    model_name = "gemini-2.5-flash"
    try:
        logger.info(f"Sending request to Gemini model: {model_name} (Habbit scheme)")
        response = client.models.generate_content(
            model=model_name,
            contents=[system_prompt, message_text],
        )
        
        raw = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Gemini API error (model {model_name}): {e}")
        if "429" in str(e):
            return {
                "reply": "⚠️ Превышен лимит запросов к ИИ. Пожалуйста, подождите немного или попробуйте позже.",
                "actions": []
            }
        return {"reply": f"❌ Ошибка API ({model_name}): {str(e)}", "actions": []}

async def process_message(user_id: int, message_text: str, context: dict) -> dict:
    """Run Gemini in a thread pool like in habbit-bot."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_gemini, message_text, context)
