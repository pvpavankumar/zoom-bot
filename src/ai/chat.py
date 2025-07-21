
import asyncio
from typing import Dict, Optional, Any
import random

from ..core.config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ChatHandler:

    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.chat_history: Dict[str, list] = {}

        self.quick_responses = {
            "help": "I can help you with interview questions, provide suggestions, or answer technical questions. Just ask!",
            "suggestions": "I'll provide interview suggestions based on the conversation flow.",
            "questions": "Here are some good interview questions you could ask...",
            "technical": "For technical questions, consider asking about their problem-solving approach.",
            "behavioral": "For behavioral questions, use the STAR method framework.",
            "how": "I'm here to assist you during the interview. I can provide real-time suggestions and answer your questions.",
            "what": "I analyze the conversation and provide helpful suggestions for conducting better interviews."
        }

    async def initialize(self):
        logger.info(f"ChatHandler initialized for instance {self.instance_id}")

    async def cleanup(self):
        self.chat_history.clear()
        logger.info(f"ChatHandler cleaned up for instance {self.instance_id}")

    async def handle_query(self, query: str, sender_id: str, context: Any) -> Optional[str]:
        try:
            query_lower = query.lower().strip()

            if sender_id not in self.chat_history:
                self.chat_history[sender_id] = []

            self.chat_history[sender_id].append({
                "query": query,
                "timestamp": asyncio.get_event_loop().time()
            })

            for keyword, response in self.quick_responses.items():
                if keyword in query_lower:
                    return f"💡 {response}"

            response = await self._generate_contextual_response(query, context)

            if response:
                return f"🤖 {response}"

            return "I'm here to help! You can ask me for interview suggestions, technical advice, or general guidance."

        except Exception as e:
            logger.error(f"Error handling chat query: {e}")
            return "Sorry, I encountered an error processing your request."

    async def _generate_contextual_response(self, query: str, context: Any) -> Optional[str]:
        query_lower = query.lower()

        if any(word in query_lower for word in ["algorithm", "code", "technical", "programming"]):
            return self._get_technical_advice(query)

        elif any(word in query_lower for word in ["behavioral", "situation", "experience", "leadership"]):
            return self._get_behavioral_advice(query)

        elif any(word in query_lower for word in ["question", "ask", "what should"]):
            return self._get_question_suggestions(context)

        elif any(word in query_lower for word in ["assess", "evaluate", "good", "performance"]):
            return self._get_assessment_advice(context)

        else:
            return self._get_general_advice(query)

    def _get_technical_advice(self, query: str) -> str:
        advice_options = [
            "Ask them to walk through their problem-solving approach step by step.",
            "Consider giving them a real-world scenario to solve.",
            "Ask about trade-offs in their technical decisions.",
            "Have them explain their code as if teaching someone else.",
            "Ask about how they would optimize or scale their solution."
        ]
        return random.choice(advice_options)

    def _get_behavioral_advice(self, query: str) -> str:
        advice_options = [
            "Use the STAR method: Situation, Task, Action, Result.",
            "Ask for specific examples rather than hypothetical scenarios.",
            "Follow up with 'What did you learn?' or 'How did it impact the team?'",
            "Focus on their decision-making process and reasoning.",
            "Ask about challenges they faced and how they overcame them."
        ]
        return random.choice(advice_options)

    def _get_question_suggestions(self, context: Any) -> str:
        suggestions = [
            "Tell me about a challenging project you worked on recently.",
            "How do you approach solving complex technical problems?",
            "Describe a time when you had to work with a difficult team member.",
            "What's your experience with [specific technology relevant to the role]?",
            "How do you stay updated with new technologies in your field?"
        ]
        return f"Here's a good question to ask: '{random.choice(suggestions)}'"

    def _get_assessment_advice(self, context: Any) -> str:
        advice_options = [
            "Look for specific examples and concrete results in their answers.",
            "Pay attention to how they structure their responses and communicate.",
            "Notice if they ask clarifying questions - it shows good problem-solving.",
            "Assess their cultural fit by asking about their work style preferences.",
            "Evaluate their learning mindset by asking about recent challenges."
        ]
        return random.choice(advice_options)

    def _get_general_advice(self, query: str) -> str:
        advice_options = [
            "Keep the conversation natural and let the candidate elaborate on interesting points.",
            "Take notes on specific examples and achievements they mention.",
            "Remember to leave time for their questions at the end.",
            "Focus on understanding their thought process, not just the final answer.",
            "Create a comfortable environment where they can showcase their best self."
        ]
        return random.choice(advice_options)


def process_chat_query(query: str, sender_id: str, context: Dict[str, Any]) -> Optional[str]:
    try:
        handler = ChatHandler("utility_instance")

        query_lower = query.lower()

        if "help" in query_lower:
            return "I can provide interview suggestions and answer your questions about the interview process."

        elif "suggestion" in query_lower:
            return "Based on the conversation, consider asking a follow-up question to get more specific details."

        elif "technical" in query_lower:
            return "For technical questions, ask them to explain their approach and reasoning behind their solutions."

        elif "behavioral" in query_lower:
            return "Use the STAR method (Situation, Task, Action, Result) for behavioral questions."

        else:
            return "I'm here to help with your interview. You can ask for suggestions or specific advice!"

    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        return "Sorry, I couldn't process your request."
