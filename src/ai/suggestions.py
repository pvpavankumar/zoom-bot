
from typing import Dict, List, Optional, Any
import random

from ..core.config import settings
from ..utils.logging import get_logger
from ..utils.helpers import detect_question_type, is_interview_keyword

logger = get_logger(__name__)


class SuggestionEngine:

    def __init__(self):
        self.suggestion_templates = {
            "technical": [
                "Consider asking for a specific example of their implementation.",
                "You might want to dive deeper into their technical decision-making process.",
                "Ask about challenges they faced with this technology.",
                "Consider exploring their experience with related technologies."
            ],
            "behavioral": [
                "Follow up with 'What did you learn from that experience?'",
                "Ask about their specific role in the situation they described.",
                "Consider asking how they would handle a similar situation differently.",
                "Explore the impact of their actions on the team or project."
            ],
            "experience": [
                "Ask for specific metrics or outcomes from their work.",
                "Consider exploring their collaboration style on this project.",
                "You might want to understand their growth from this experience.",
                "Ask about the most challenging aspect of this role."
            ],
            "general": [
                "Consider asking a follow-up question to get more detail.",
                "You might want to explore this topic further.",
                "Ask for a specific example to illustrate their point.",
                "Consider how this relates to the role requirements."
            ]
        }

    async def generate_suggestion(self, context: Dict[str, Any]) -> Optional[str]:
        try:
            recent_messages = context.get("messages", [])[-3:]

            if not recent_messages:
                return None

            last_interviewer_msg = None
            for msg in reversed(recent_messages):
                if msg.get("role") == "interviewer":
                    last_interviewer_msg = msg
                    break

            if not last_interviewer_msg:
                return "Consider asking an open-ended question to encourage discussion."

            question_text = last_interviewer_msg.get("content", "")
            question_type = detect_question_type(question_text)

            suggestions = self.suggestion_templates.get(question_type, self.suggestion_templates["general"])

            return random.choice(suggestions)

        except Exception as e:
            logger.error(f"Error generating suggestion: {e}")
            return None

    def get_interview_stage_suggestions(self, stage: str) -> List[str]:
        stage_suggestions = {
            "introduction": [
                "Start with an icebreaker question to make the candidate comfortable.",
                "Ask about their background and what interests them about the role.",
                "Consider explaining the interview structure to set expectations."
            ],
            "technical": [
                "Ask them to walk through their problem-solving approach.",
                "Consider asking about their experience with specific technologies.",
                "You might want to present a technical scenario or coding challenge."
            ],
            "behavioral": [
                "Use the STAR method (Situation, Task, Action, Result) framework.",
                "Ask about specific situations that demonstrate key competencies.",
                "Focus on their decision-making process and leadership examples."
            ],
            "closing": [
                "Ask if they have any questions about the role or company.",
                "Explain the next steps in the interview process.",
                "Consider asking about their timeline and other opportunities."
            ]
        }

        return stage_suggestions.get(stage, [])


def generate_interview_suggestion(context_data: Dict[str, Any]) -> Optional[str]:
    try:
        engine = SuggestionEngine()

        messages = context_data.get("messages", [])
        if not messages:
            return "Start the interview with an open-ended question about the candidate's background."

        recent_content = " ".join([msg.get("content", "") for msg in messages[-3:]])

        if is_interview_keyword(recent_content):
            question_type = detect_question_type(recent_content)

            if question_type == "technical":
                return "Consider asking for a specific code example or technical implementation."
            elif question_type == "behavioral":
                return "Follow up with 'What was the outcome?' or 'What did you learn?'"
            elif question_type == "experience":
                return "Ask about specific challenges they faced in this role."
            else:
                return "Consider asking a follow-up question to get more specific details."

        return "Ask an open-ended question to encourage the candidate to elaborate."

    except Exception as e:
        logger.error(f"Error in suggestion generation: {e}")
        return None
