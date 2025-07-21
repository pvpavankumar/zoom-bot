
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import openai

print("0000000000000")
from ..core.config import settings
from ..utils.logging import get_logger
print("completed p1")
from ..utils.helpers import extract_keywords_from_text, detect_question_type, is_interview_keyword

logger = get_logger(__name__)
print("1111111111111")


class ConversationAnalyzer:

    def __init__(self, instance_id: str):
        print("2222222222222")
        self.instance_id = instance_id
        self.openai_client = None
        print("completed p2")

        self.context_window = settings.context_window_size
        self.min_analysis_length = 50
        print("3333333333333")

        self.conversation_history: List[Dict[str, Any]] = []
        self.current_topic: Optional[str] = None
        self.interview_stage = "introduction"
        print("completed p3")
        self.participant_insights: Dict[str, Dict[str, Any]] = {}

        logger.info(f"ConversationAnalyzer initialized for instance {instance_id}")

    async def initialize(self):
        self.openai_client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_org_id
        )
        logger.info("ConversationAnalyzer OpenAI client initialized")

    async def cleanup(self):
        if self.openai_client:
            await self.openai_client.close()

        self.conversation_history.clear()
        self.participant_insights.clear()

        logger.info("ConversationAnalyzer cleaned up")

    async def analyze_transcript(self, transcript: str, participant_id: str, participant_role: str) -> Dict[str, Any]:
        try:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "participant_id": participant_id,
                "role": participant_role,
                "transcript": transcript,
                "word_count": len(transcript.split())
            }

            self.conversation_history.append(entry)

            self._trim_conversation_history()

            insights = self._extract_basic_insights(transcript, participant_role)

            if len(transcript.split()) >= self.min_analysis_length:
                ai_analysis = await self._perform_ai_analysis(transcript, participant_role)
                insights.update(ai_analysis)

            self._update_participant_insights(participant_id, insights)

            await self._update_conversation_context(transcript, participant_role)

            return insights

        except Exception as e:
            logger.error(f"Error analyzing transcript: {e}")
            return {"error": str(e)}

    async def generate_suggestion(self, context: Any, participants: Dict[str, Any]) -> Optional[str]:
        try:
            conversation_context = self._prepare_conversation_context()

            if not conversation_context:
                return None

            suggestion = await self._generate_ai_suggestion(conversation_context, participants)

            if suggestion:
                from ..utils.logging import log_ai_event
                log_ai_event(
                    "suggestion_generated",
                    self.instance_id,
                    suggestion=suggestion
                )

            return suggestion

        except Exception as e:
            logger.error(f"Error generating suggestion: {e}")
            return None

    async def get_conversation_summary(self) -> Dict[str, Any]:
        if not self.conversation_history:
            return {"summary": "No conversation data available"}

        try:
            total_messages = len(self.conversation_history)
            interviewer_messages = len([m for m in self.conversation_history if m["role"] == "interviewer"])
            candidate_messages = len([m for m in self.conversation_history if m["role"] == "candidate"])

            total_words = sum(m["word_count"] for m in self.conversation_history)

            recent_conversation = self.conversation_history[-10:]
            conversation_text = "\n".join([
                f"{m['role']}: {m['transcript']}" for m in recent_conversation
            ])

            ai_summary = await self._generate_conversation_summary(conversation_text)

            return {
                "total_messages": total_messages,
                "interviewer_messages": interviewer_messages,
                "candidate_messages": candidate_messages,
                "total_words": total_words,
                "current_stage": self.interview_stage,
                "current_topic": self.current_topic,
                "ai_summary": ai_summary,
                "participant_insights": self.participant_insights
            }

        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return {"error": str(e)}

    def _extract_basic_insights(self, transcript: str, participant_role: str) -> Dict[str, Any]:
        insights = {
            "word_count": len(transcript.split()),
            "keywords": extract_keywords_from_text(transcript),
            "contains_interview_keywords": is_interview_keyword(transcript),
            "role": participant_role
        }

        if participant_role == "interviewer":
            insights["question_type"] = detect_question_type(transcript)
            insights["is_question"] = "?" in transcript
        else:
            insights["response_length"] = "long" if len(transcript.split()) > 50 else "short"
            insights["contains_technical_terms"] = self._contains_technical_terms(transcript)

        return insights

    async def _perform_ai_analysis(self, transcript: str, participant_role: str) -> Dict[str, Any]:
        if not self.openai_client:
            return {}

        try:
            prompt = self._create_analysis_prompt(transcript, participant_role)

            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that analyzes interview conversations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )

            analysis_text = response.choices[0].message.content

            return self._parse_ai_analysis(analysis_text)

        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {}

    async def _generate_ai_suggestion(self, context: str, participants: Dict[str, Any]) -> Optional[str]:
        if not self.openai_client:
            return None

        try:
            prompt = self._create_suggestion_prompt(context, participants)

            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant helping interviewers conduct better interviews. Provide concise, actionable suggestions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.4
            )

            suggestion = response.choices[0].message.content.strip()

            if suggestion.startswith("Suggestion:"):
                suggestion = suggestion[11:].strip()

            return suggestion if len(suggestion) > 10 else None

        except Exception as e:
            logger.error(f"Error generating AI suggestion: {e}")
            return None

    async def _generate_conversation_summary(self, conversation_text: str) -> str:
        if not self.openai_client:
            return "AI summary not available"

        try:
            prompt = f"""
            Summarize the following interview conversation in 2-3 sentences:

            {conversation_text}

            Focus on the key topics discussed and the overall flow of the interview.
            """

            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that creates concise interview summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return "Summary generation failed"

    def _create_analysis_prompt(self, transcript: str, participant_role: str) -> str:
        if participant_role == "interviewer":
            return f"""
            Analyze this interviewer question/statement:
            "{transcript}"

            Provide analysis in this format:
            Question Type: [behavioral/technical/experience/other]
            Clarity: [clear/unclear/confusing]
            Follow-up Needed: [yes/no]
            Tone: [formal/casual/encouraging/intimidating]
            """
        else:
            return f"""
            Analyze this candidate response:
            "{transcript}"

            Provide analysis in this format:
            Response Quality: [excellent/good/adequate/poor]
            Completeness: [complete/partial/incomplete]
            Confidence Level: [high/medium/low]
            Technical Depth: [high/medium/low/none]
            """

    def _create_suggestion_prompt(self, context: str, participants: Dict[str, Any]) -> str:

    def _parse_ai_analysis(self, analysis_text: str) -> Dict[str, Any]:
        analysis = {}

        lines = analysis_text.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                analysis[key] = value

        return analysis

    def _prepare_conversation_context(self) -> str:
        if not self.conversation_history:
            return ""

        recent_messages = self.conversation_history[-5:]

        context_lines = []
        for msg in recent_messages:
            role = msg["role"].capitalize()
            transcript = msg["transcript"][:200]
            context_lines.append(f"{role}: {transcript}")

        return "\n".join(context_lines)

    def _update_participant_insights(self, participant_id: str, insights: Dict[str, Any]):
        if participant_id not in self.participant_insights:
            self.participant_insights[participant_id] = {
                "message_count": 0,
                "total_words": 0,
                "keywords": set(),
                "question_types": [],
                "response_quality": []
            }

        participant_data = self.participant_insights[participant_id]
        participant_data["message_count"] += 1
        participant_data["total_words"] += insights.get("word_count", 0)

        if insights.get("keywords"):
            participant_data["keywords"].update(insights["keywords"])

        if insights.get("question_type"):
            participant_data["question_types"].append(insights["question_type"])

        if insights.get("response_quality"):
            participant_data["response_quality"].append(insights["response_quality"])

    async def _update_conversation_context(self, transcript: str, participant_role: str):
        transcript_lower = transcript.lower()

        if any(word in transcript_lower for word in ["introduce", "tell me about yourself", "background"]):
            self.interview_stage = "introduction"
        elif any(word in transcript_lower for word in ["technical", "code", "algorithm", "implement"]):
            self.interview_stage = "technical"
        elif any(word in transcript_lower for word in ["situation", "challenge", "team", "leadership"]):
            self.interview_stage = "behavioral"
        elif any(word in transcript_lower for word in ["questions", "ask me", "closing", "thank you"]):
            self.interview_stage = "closing"

        keywords = extract_keywords_from_text(transcript)
        if keywords:
            self.current_topic = keywords[0]

    def _contains_technical_terms(self, text: str) -> bool:
        technical_terms = {
            'api', 'database', 'algorithm', 'framework', 'library', 'function',
            'class', 'method', 'variable', 'array', 'object', 'sql', 'json',
            'rest', 'microservice', 'docker', 'kubernetes', 'aws', 'cloud',
            'javascript', 'python', 'java', 'react', 'angular', 'node'
        }

        text_lower = text.lower()
        return any(term in text_lower for term in technical_terms)

    def _trim_conversation_history(self):
        total_words = sum(msg["word_count"] for msg in self.conversation_history)

        while total_words > self.context_window and len(self.conversation_history) > 1:
            removed_msg = self.conversation_history.pop(0)
            total_words -= removed_msg["word_count"]


def analyze_conversation_segment(transcript: str, participants: Dict[str, Any]) -> Dict[str, Any]:
    try:
        analyzer = ConversationAnalyzer("celery_task")

        insights = {
            "word_count": len(transcript.split()),
            "keywords": extract_keywords_from_text(transcript),
            "contains_interview_keywords": is_interview_keyword(transcript),
            "question_indicators": transcript.count("?"),
            "timestamp": datetime.utcnow().isoformat()
        }

        for participant_id, participant_data in participants.items():
            role = participant_data.get("role", "unknown")
            if role == "interviewer":
                insights["question_type"] = detect_question_type(transcript)

        return insights

    except Exception as e:
        logger.error(f"Error in conversation segment analysis: {e}")
        return {"error": str(e)}
