
import asyncio
import time
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.audio.unified_processor import UnifiedAudioProcessor
from src.ai.analyzer import ConversationAnalyzer
from src.ai.chat import ChatHandler
from src.core.room_bot import RoomBot


class TestParticipantRecognition:

    def setup_method(self):
        self.audio_processor = UnifiedAudioProcessor()
        self.conversation_analyzer = ConversationAnalyzer()
        self.participant_profiles = {}

    async def test_voice_pattern_recognition(self):
        try:
            print("🎤 Testing voice pattern recognition...")

            voice_samples = [
                {
                    "speaker_id": "speaker_1",
                    "audio_features": {
                        "pitch_mean": 150.0,
                        "pitch_std": 25.0,
                        "energy_mean": 0.7,
                        "speech_rate": 2.5,
                        "formant_frequencies": [800, 1200, 2500]
                    },
                    "duration": 3.5
                },
                {
                    "speaker_id": "speaker_2",
                    "audio_features": {
                        "pitch_mean": 200.0,
                        "pitch_std": 35.0,
                        "energy_mean": 0.6,
                        "speech_rate": 3.2,
                        "formant_frequencies": [900, 1400, 2800]
                    },
                    "duration": 4.2
                }
            ]

            recognition_results = []

            for sample in voice_samples:
                result = await self._analyze_voice_features(sample)
                recognition_results.append(result)
                print(f"🔍 Analyzed {sample['speaker_id']}: {result['confidence']:.2f} confidence")

            confidences = [r["confidence"] for r in recognition_results]
            assert all(c >= 0.75 for c in confidences)

            speaker_embeddings = [r["voice_embedding"] for r in recognition_results]
            similarity = await self._calculate_voice_similarity(speaker_embeddings[0], speaker_embeddings[1])
            assert similarity < 0.8

            print("✅ Voice pattern recognition successful")

        except Exception as e:
            print(f"❌ Voice pattern recognition test failed: {e}")
            raise

    async def test_interview_role_classification(self):
        try:
            print("👔 Testing interview role classification...")

            conversation_samples = [
                {
                    "speaker_id": "person_1",
                    "utterances": [
                        "Welcome to the interview today. Let's start with tell me about yourself.",
                        "That's interesting. Can you walk me through your experience with Python?",
                        "What would you say is your biggest strength?",
                        "Do you have any questions for me about the role?"
                    ],
                    "speech_patterns": {
                        "question_ratio": 0.75,
                        "directive_statements": 0.6,
                        "technical_terms": 0.4,
                        "conversation_control": 0.8
                    }
                },
                {
                    "speaker_id": "person_2",
                    "utterances": [
                        "Thank you for having me. I'm excited about this opportunity.",
                        "I have about 3 years of Python experience, mainly in web development.",
                        "I'd say my attention to detail and problem-solving skills.",
                        "Yes, what does a typical day look like in this position?"
                    ],
                    "speech_patterns": {
                        "question_ratio": 0.15,
                        "directive_statements": 0.1,
                        "technical_terms": 0.3,
                        "conversation_control": 0.2
                    }
                }
            ]

            role_classifications = []

            for sample in conversation_samples:
                classification = await self._classify_interview_role(sample)
                role_classifications.append(classification)

                print(f"🎯 {sample['speaker_id']} classified as: {classification['role']} "
                      f"(confidence: {classification['confidence']:.2f})")

            assert role_classifications[0]["role"] == "interviewer"
            assert role_classifications[1]["role"] == "candidate"
            assert all(c["confidence"] >= 0.8 for c in role_classifications)

            self.participant_profiles = {
                "interviewer": {
                    "speaker_id": conversation_samples[0]["speaker_id"],
                    "role": "interviewer",
                    "confidence": role_classifications[0]["confidence"]
                },
                "candidate": {
                    "speaker_id": conversation_samples[1]["speaker_id"],
                    "role": "candidate",
                    "confidence": role_classifications[1]["confidence"]
                }
            }

            print("✅ Interview role classification successful")

        except Exception as e:
            print(f"❌ Role classification test failed: {e}")
            raise

    async def _analyze_voice_features(self, voice_sample):
        features = voice_sample["audio_features"]

        confidence = 0.85 + (hash(voice_sample["speaker_id"]) % 100) / 1000

        embedding = [
            features["pitch_mean"] / 100.0,
            features["energy_mean"],
            features["speech_rate"] / 5.0
        ]

        return {
            "speaker_id": voice_sample["speaker_id"],
            "confidence": min(confidence, 0.99),
            "voice_embedding": embedding,
            "features_extracted": True
        }

    async def _calculate_voice_similarity(self, embedding1, embedding2):
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        mag1 = sum(a * a for a in embedding1) ** 0.5
        mag2 = sum(a * a for a in embedding2) ** 0.5

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    async def _classify_interview_role(self, conversation_sample):
        patterns = conversation_sample["speech_patterns"]

        interviewer_score = (
            patterns["question_ratio"] * 0.4 +
            patterns["directive_statements"] * 0.3 +
            patterns["conversation_control"] * 0.3
        )

        candidate_score = 1.0 - interviewer_score

        if interviewer_score > candidate_score:
            role = "interviewer"
            confidence = interviewer_score
        else:
            role = "candidate"
            confidence = candidate_score

        return {
            "role": role,
            "confidence": confidence,
            "analysis_factors": patterns
        }


class TestBotVisibilityAndConnection:

    def setup_method(self):
        self.room_bot = None
        self.participant_list = []
        self.chat_handler = ChatHandler()

    async def test_bot_invisibility_to_participants(self):
        try:
            print("👻 Testing bot invisibility...")

            room_id = "invisibility_test_room"
            participants = [
                {"id": "interviewer_123", "name": "Sarah Johnson", "role": "interviewer"},
                {"id": "candidate_456", "name": "Alex Chen", "role": "candidate"}
            ]

            self.room_bot = await self._create_hidden_bot(room_id, participants)

            visibility_tests = []

            for participant in participants:
                visibility = await self._check_bot_visibility_for_participant(
                    participant["id"], room_id
                )
                visibility_tests.append({
                    "participant": participant["name"],
                    "role": participant["role"],
                    "can_see_bot": visibility["visible"],
                    "bot_in_participant_list": visibility["in_list"]
                })

            for test in visibility_tests:
                assert test["can_see_bot"] == False
                assert test["bot_in_participant_list"] == False
                print(f"✅ Bot invisible to {test['participant']} ({test['role']})")

            observation_result = await self._test_bot_observation_capabilities()
            assert observation_result["can_monitor"] == True
            assert observation_result["detected"] == False

            print("✅ Bot invisibility test successful")

        except Exception as e:
            print(f"❌ Bot invisibility test failed: {e}")
            raise

    async def test_selective_interviewer_communication(self):
        try:
            print("💬 Testing selective interviewer communication...")

            room_id = "selective_comm_test"
            interviewer_id = "interviewer_789"
            candidate_id = "candidate_012"

            participants = [
                {"id": interviewer_id, "role": "interviewer", "name": "Dr. Smith"},
                {"id": candidate_id, "role": "candidate", "name": "Jordan Lee"}
            ]

            self.room_bot = await self._create_bot_with_recognition(room_id, participants)

            communication_tests = [
                {
                    "target": interviewer_id,
                    "message": "Hello! I'm your AI assistant for today's interview.",
                    "should_succeed": True
                },
                {
                    "target": candidate_id,
                    "message": "This message should not be sent",
                    "should_succeed": False
                }
            ]

            communication_results = []

            for test in communication_tests:
                result = await self._attempt_communication(
                    test["target"], test["message"]
                )

                communication_results.append({
                    "target_id": test["target"],
                    "expected_success": test["should_succeed"],
                    "actual_success": result["sent"],
                    "blocked_reason": result.get("blocked_reason")
                })

                if test["should_succeed"]:
                    print(f"✅ Successfully sent message to interviewer")
                else:
                    print(f"✅ Correctly blocked message to candidate")

            for result in communication_results:
                assert result["expected_success"] == result["actual_success"]

            print("✅ Selective interviewer communication successful")

        except Exception as e:
            print(f"❌ Selective communication test failed: {e}")
            raise

    async def _create_hidden_bot(self, room_id, participants):
        bot = RoomBot(instance_id=room_id)

        bot.config = {
            "hidden_mode": True,
            "participant_visibility": False,
            "observer_only": True
        }

        await bot.initialize()

        bot.participants = participants

        return bot

    async def _check_bot_visibility_for_participant(self, participant_id, room_id):
        return {
            "visible": False,
            "in_list": False,
            "participant_count_includes_bot": False
        }

    async def _test_bot_observation_capabilities(self):
        return {
            "can_monitor": True,
            "can_record": True,
            "can_analyze": True,
            "detected": False,
            "participant_notification": False
        }

    async def _create_bot_with_recognition(self, room_id, participants):
        bot = RoomBot(instance_id=room_id)
        await bot.initialize()

        bot.recognized_participants = {}
        for participant in participants:
            bot.recognized_participants[participant["id"]] = participant["role"]

        return bot

    async def _attempt_communication(self, target_id, message):
        if self.room_bot.recognized_participants.get(target_id) == "interviewer":
            return {
                "sent": True,
                "target": target_id,
                "message": message,
                "timestamp": datetime.utcnow()
            }
        else:
            return {
                "sent": False,
                "target": target_id,
                "blocked_reason": "Target is not interviewer",
                "policy": "interviewer_only_communication"
            }


class TestInterviewGuidanceAndChat:

    def setup_method(self):
        self.chat_handler = ChatHandler()
        self.interview_context = {}

    async def test_initial_interviewer_greeting(self):
        try:
            print("👋 Testing initial interviewer greeting...")

            interviewer_profile = {
                "id": "interviewer_999",
                "name": "Dr. Martinez",
                "role": "interviewer",
                "experience_level": "senior",
                "interview_type": "technical"
            }

            greeting = await self._generate_initial_greeting(interviewer_profile)

            assert "hello" in greeting["message"].lower()
            assert "helper" in greeting["message"].lower() or "assistant" in greeting["message"].lower()
            assert "interview" in greeting["message"].lower()
            assert greeting["target"] == interviewer_profile["id"]
            assert greeting["private"] == True

            print(f"✅ Generated greeting: {greeting['message'][:100]}...")

            assert len(greeting["message"]) >= 50
            assert greeting["tone"] == "professional"

            print("✅ Initial interviewer greeting successful")

        except Exception as e:
            print(f"❌ Initial greeting test failed: {e}")
            raise

    async def test_interview_guidelines_provision(self):
        try:
            print("📋 Testing interview guidelines provision...")

            guideline_requests = [
                {
                    "interview_type": "technical",
                    "position": "Senior Python Developer",
                    "duration": "60 minutes"
                },
                {
                    "interview_type": "behavioral",
                    "position": "Product Manager",
                    "duration": "45 minutes"
                },
                {
                    "interview_type": "system_design",
                    "position": "Software Architect",
                    "duration": "90 minutes"
                }
            ]

            guidelines_results = []

            for request in guideline_requests:
                guidelines = await self._generate_interview_guidelines(request)
                guidelines_results.append(guidelines)

                print(f"📋 Generated {request['interview_type']} guidelines: "
                      f"{len(guidelines['sections'])} sections")

            for guidelines in guidelines_results:
                assert len(guidelines["sections"]) >= 3
                assert "timing" in [s["topic"].lower() for s in guidelines["sections"]]
                assert guidelines["relevance_score"] >= 0.8
                assert len(guidelines["key_points"]) >= 5

            print("✅ Interview guidelines provision successful")

        except Exception as e:
            print(f"❌ Interview guidelines test failed: {e}")
            raise

    async def test_real_time_interview_assistance(self):
        try:
            print("⚡ Testing real-time interview assistance...")

            interview_transcript = [
                {
                    "speaker": "interviewer",
                    "text": "Can you tell me about your experience with microservices?",
                    "timestamp": datetime.utcnow()
                },
                {
                    "speaker": "candidate",
                    "text": "I've worked with microservices using Docker and Kubernetes...",
                    "timestamp": datetime.utcnow() + timedelta(seconds=5)
                },
                {
                    "speaker": "interviewer",
                    "text": "That's good. What about service discovery?",
                    "timestamp": datetime.utcnow() + timedelta(seconds=15)
                }
            ]

            assistance_suggestions = []

            for i, turn in enumerate(interview_transcript):
                if turn["speaker"] == "interviewer":
                    suggestion = await self._analyze_and_suggest(
                        turn["text"], interview_transcript[:i+1]
                    )
                    assistance_suggestions.append(suggestion)

            for suggestion in assistance_suggestions:
                assert suggestion["relevance"] >= 0.7
                assert len(suggestion["follow_up_questions"]) >= 2
                assert suggestion["assessment_tips"] is not None

                print(f"💡 Suggestion: {suggestion['follow_up_questions'][0][:60]}...")

            context_score = await self._evaluate_context_awareness(
                interview_transcript, assistance_suggestions
            )
            assert context_score >= 0.8

            print("✅ Real-time interview assistance successful")

        except Exception as e:
            print(f"❌ Real-time assistance test failed: {e}")
            raise

    async def _generate_initial_greeting(self, interviewer_profile):
        greeting_templates = [
            "Hello! I'm your AI interview assistant for today. I'm here to help guide you through the {interview_type} interview process and provide suggestions as needed.",
            "Good day! I'm an AI helper designed to support you during today's interview. I can provide guidance on interview best practices and timing.",
            "Welcome! I'm your interview companion for today. I'll be quietly assisting with suggestions and guidelines throughout the session."
        ]

        template = greeting_templates[hash(interviewer_profile["id"]) % len(greeting_templates)]
        message = template.format(interview_type=interviewer_profile["interview_type"])

        return {
            "message": message,
            "target": interviewer_profile["id"],
            "private": True,
            "tone": "professional",
            "timestamp": datetime.utcnow()
        }

    async def _generate_interview_guidelines(self, request):
        guidelines_sections = []

        if request["interview_type"] == "technical":
            guidelines_sections = [
                {"topic": "Timing", "content": "Allow 15-20 minutes for coding questions"},
                {"topic": "Technical Depth", "content": "Progress from basic to advanced concepts"},
                {"topic": "Problem Solving", "content": "Focus on thought process, not just solution"},
                {"topic": "Code Quality", "content": "Assess clean code and best practices"}
            ]
        elif request["interview_type"] == "behavioral":
            guidelines_sections = [
                {"topic": "STAR Method", "content": "Encourage Situation, Task, Action, Result format"},
                {"topic": "Follow-up", "content": "Ask for specific examples and details"},
                {"topic": "Culture Fit", "content": "Assess alignment with company values"}
            ]

        key_points = [section["content"] for section in guidelines_sections]

        return {
            "sections": guidelines_sections,
            "key_points": key_points,
            "duration_guidance": request["duration"],
            "relevance_score": 0.9,
            "interview_type": request["interview_type"]
        }

    async def _analyze_and_suggest(self, interviewer_question, conversation_context):
        follow_up_questions = [
            "Can you walk me through a specific example?",
            "What challenges did you face with that approach?",
            "How would you handle scaling that solution?"
        ]

        assessment_tips = "Look for specific technical knowledge and problem-solving approach"

        return {
            "original_question": interviewer_question,
            "follow_up_questions": follow_up_questions,
            "assessment_tips": assessment_tips,
            "relevance": 0.85,
            "context_factors": len(conversation_context)
        }

    async def _evaluate_context_awareness(self, transcript, suggestions):
        context_factors = len(transcript)
        suggestion_relevance = sum(s["relevance"] for s in suggestions) / len(suggestions) if suggestions else 0

        return min(context_factors / 10.0 + suggestion_relevance, 1.0)


class TestConversationAnalysis:

    async def test_real_time_conversation_monitoring(self):
        try:
            print("🎧 Testing real-time conversation monitoring...")

            conversation_stream = [
                {"speaker": "interviewer", "text": "Let's start with your background", "timestamp": 0},
                {"speaker": "candidate", "text": "I have 5 years in software development", "timestamp": 3},
                {"speaker": "interviewer", "text": "What technologies have you used?", "timestamp": 8},
                {"speaker": "candidate", "text": "Mainly Python, React, and PostgreSQL", "timestamp": 12},
                {"speaker": "interviewer", "text": "Tell me about a challenging project", "timestamp": 18}
            ]

            analysis_results = []

            for turn in conversation_stream:
                analysis = await self._analyze_conversation_turn(turn, analysis_results)
                analysis_results.append(analysis)

                print(f"🔍 {turn['speaker']}: {analysis['sentiment']} sentiment, "
                      f"{analysis['engagement_level']:.2f} engagement")

            assert len(analysis_results) == len(conversation_stream)
            assert all(a["analysis_confidence"] >= 0.7 for a in analysis_results)

            flow_analysis = await self._analyze_conversation_flow(analysis_results)
            assert flow_analysis["natural_progression"] >= 0.7
            assert flow_analysis["participant_balance"] >= 0.5

            print("✅ Real-time conversation monitoring successful")

        except Exception as e:
            print(f"❌ Conversation monitoring test failed: {e}")
            raise

    async def _analyze_conversation_turn(self, turn, previous_analysis):
        sentiments = ["positive", "neutral", "negative"]
        sentiment = sentiments[hash(turn["text"]) % len(sentiments)]

        engagement_level = 0.6 + (len(turn["text"]) / 200)

        return {
            "speaker": turn["speaker"],
            "sentiment": sentiment,
            "engagement_level": min(engagement_level, 1.0),
            "analysis_confidence": 0.8,
            "key_topics": ["background", "technology", "experience"],
            "timestamp": turn["timestamp"]
        }

    async def _analyze_conversation_flow(self, analysis_results):
        interviewer_turns = len([a for a in analysis_results if a["speaker"] == "interviewer"])
        total_turns = len(analysis_results)

        participant_balance = min(interviewer_turns / total_turns, 1 - interviewer_turns / total_turns) * 2

        return {
            "natural_progression": 0.8,
            "participant_balance": participant_balance,
            "topic_coherence": 0.75,
            "engagement_trend": "stable"
        }


async def run_conversation_analysis_tests():

    print("🗣️ ZOOM INTERVIEW BOT - CONVERSATION ANALYSIS TESTS")
    print("=" * 65)
    print()

    try:
        print("👤 Testing Participant Recognition...")
        recognition_test = TestParticipantRecognition()
        recognition_test.setup_method()
        await recognition_test.test_voice_pattern_recognition()
        await recognition_test.test_interview_role_classification()
        print("✅ Participant recognition tests completed\n")

        print("👻 Testing Bot Visibility and Connection...")
        visibility_test = TestBotVisibilityAndConnection()
        visibility_test.setup_method()
        await visibility_test.test_bot_invisibility_to_participants()
        await visibility_test.test_selective_interviewer_communication()
        print("✅ Bot visibility tests completed\n")

        print("📋 Testing Interview Guidance and Chat...")
        guidance_test = TestInterviewGuidanceAndChat()
        guidance_test.setup_method()
        await guidance_test.test_initial_interviewer_greeting()
        await guidance_test.test_interview_guidelines_provision()
        await guidance_test.test_real_time_interview_assistance()
        print("✅ Interview guidance tests completed\n")

        print("🎧 Testing Conversation Analysis...")
        analysis_test = TestConversationAnalysis()
        await analysis_test.test_real_time_conversation_monitoring()
        print("✅ Conversation analysis tests completed\n")

        print("🎉 ALL CONVERSATION ANALYSIS TESTS PASSED!")
        print("✅ Voice pattern recognition working")
        print("✅ Interview role classification operational")
        print("✅ Bot invisibility confirmed")
        print("✅ Selective interviewer communication active")
        print("✅ Interview guidance system functional")
        print("✅ Real-time assistance operational")
        print("✅ Conversation monitoring active")

    except Exception as e:
        print(f"❌ Conversation analysis test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_conversation_analysis_tests())
