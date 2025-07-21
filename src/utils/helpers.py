
import uuid
import re
from datetime import datetime
from typing import Optional, Dict, Any


def generate_uuid() -> str:
    return str(uuid.uuid4())


def format_timestamp(dt: Optional[datetime] = None) -> str:
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()


def validate_room_id(room_id: str) -> bool:
    if not room_id:
        return False

    pattern = r'^[a-zA-Z0-9\-_]+$'
    return bool(re.match(pattern, room_id)) and len(room_id) > 0


def validate_meeting_id(meeting_id: str) -> bool:
    if not meeting_id:
        return False

    pattern = r'^\d{9,11}$'
    return bool(re.match(pattern, meeting_id.replace('-', '').replace(' ', '')))


def sanitize_participant_name(name: str) -> str:
    if not name:
        return "Unknown"

    sanitized = re.sub(r'[<>"\'/\\&]', '', name.strip())
    return sanitized[:50] if len(sanitized) > 50 else sanitized


def extract_keywords_from_text(text: str, max_keywords: int = 10) -> list:
    if not text:
        return []

    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'cannot', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
        'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
    }

    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

    keywords = list(set(word for word in words if word not in stop_words))

    return keywords[:max_keywords]


def calculate_similarity(text1: str, text2: str) -> float:
    if not text1 or not text2:
        return 0.0

    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    if not union:
        return 0.0

    return len(intersection) / len(union)


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    keys = key.split('.')
    value = dictionary

    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def is_interview_keyword(text: str) -> bool:
    interview_keywords = {
        'experience', 'project', 'challenge', 'team', 'leadership', 'problem',
        'solution', 'technical', 'algorithm', 'database', 'framework', 'language',
        'skills', 'qualification', 'education', 'background', 'achievement',
        'weakness', 'strength', 'goal', 'future', 'company', 'culture',
        'question', 'answer', 'explain', 'describe', 'example', 'situation'
    }

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in interview_keywords)


def detect_question_type(text: str) -> str:
    text_lower = text.lower()

    if any(word in text_lower for word in ['tell me about', 'describe', 'explain']):
        return 'behavioral'
    elif any(word in text_lower for word in ['algorithm', 'code', 'technical', 'implement']):
        return 'technical'
    elif any(word in text_lower for word in ['experience', 'worked', 'project']):
        return 'experience'
    elif any(word in text_lower for word in ['weakness', 'strength', 'challenge']):
        return 'self_assessment'
    elif any(word in text_lower for word in ['company', 'culture', 'why', 'interested']):
        return 'company_fit'
    else:
        return 'general'


def estimate_speech_duration(text: str) -> float:
    words = len(text.split())
    words_per_second = 2.5
    return words / words_per_second


def clean_audio_transcript(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r'\s+', ' ', text)

    text = re.sub(r'\b(um|uh|ah|er|hmm)\b', '', text, flags=re.IGNORECASE)

    text = re.sub(r'\s+([.!?])', r'\1', text)

    sentences = text.split('.')
    sentences = [s.strip().capitalize() for s in sentences if s.strip()]

    return '. '.join(sentences)


def get_audio_quality_score(audio_level: float, noise_level: float = 0.0) -> float:
    if audio_level <= 0:
        return 0.0

    signal_to_noise = audio_level / max(noise_level, 0.01)
    quality = min(signal_to_noise / 10.0, 1.0)

    return quality


def parse_time_duration(duration_str: str) -> float:
    if not duration_str:
        return 0.0

    duration_str = duration_str.strip().lower()

    if duration_str.endswith('s'):
        return float(duration_str[:-1])
    elif duration_str.endswith('m'):
        return float(duration_str[:-1]) * 60
    elif duration_str.endswith('h'):
        return float(duration_str[:-1]) * 3600
    else:
        try:
            return float(duration_str)
        except ValueError:
            return 0.0
