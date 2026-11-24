import re
import string
from typing import List, Tuple
from .schemas import StylometricFeatures

CLICKBAIT_PATTERNS = [
    r'\bshocking\b',
    r'\bunbelievable\b',
    r'\byou won[\'’]t believe\b',
    r'\bsecret cure\b',
    r'\bmiracle cure\b',
    r'\bbig pharma\b',
    r'\bshare before (it gets|they) deleted?\b',
    r'\bmainstream media (won\'t|refuses)\b',
    r'\bwhat happened next\b',
    r'\bwill blow your mind\b',
    r'\bconspiracy\b',
    r'\bhidden truth\b',
    r'\bwake up america\b',
    r'\bwhistleblower exposes\b',
    r'\bbomb shell\b',
    r'\bbombshell\b',
    r'\bexposed\b',
    r'\beliminate (pain|cancer|disease) overnight\b',
]

JOURNALISTIC_PATTERNS = [
    r'\baccording to\b',
    r'\breported\b',
    r'\bofficials? said\b',
    r'\bspokesperson\b',
    r'\bpress release\b',
    r'\bpublished in\b',
    r'\bresearchers found\b',
    r'\bstudy conducted\b',
    r'\bdepartment of\b',
    r'\bagency\b',
    r'\bconference\b',
    r'\bstatement on\b',
    r'\bspoke on condition of anonymity\b',
]

def extract_stylometrics(title: str, text: str) -> Tuple[StylometricFeatures, List[float], List[str]]:
    """
    Extracts stylometric features, raw feature vector for LGBM, and explainability tags.
    """
    t_clean = (title or "").strip()
    b_clean = (text or "").strip()
    full_clean = f"{t_clean} {b_clean}".strip()
    
    t_words = t_clean.split()
    b_words = b_clean.split()
    
    t_len = len(t_clean)
    t_wcount = len(t_words)
    b_len = max(len(b_clean), 1)
    b_wcount = max(len(b_words), 1)
    
    # Stylometric measures
    avg_word_len = sum(len(w) for w in b_words) / b_wcount if b_words else 0.0
    upper_count = sum(1 for c in b_clean if c.isupper())
    upper_ratio = upper_count / b_len
    
    punct_count = sum(1 for c in b_clean if c in string.punctuation)
    punct_ratio = punct_count / b_len
    
    exclamation_count = b_clean.count('!') + t_clean.count('!')
    question_count = b_clean.count('?') + t_clean.count('?')
    quote_count = sum(1 for c in b_clean if c in "\"\'“”’‘")
    
    unique_words = len(set(w.lower() for w in b_words))
    lexical_diversity = unique_words / b_wcount if b_words else 0.0
    
    features = StylometricFeatures(
        title_word_count=t_wcount,
        title_char_length=t_len,
        text_word_count=b_wcount,
        text_char_length=b_len,
        avg_word_length=round(avg_word_len, 2),
        uppercase_ratio=round(upper_ratio, 4),
        punctuation_ratio=round(punct_ratio, 4),
        exclamation_count=exclamation_count,
        question_count=question_count,
        quote_count=quote_count,
        lexical_diversity=round(lexical_diversity, 4)
    )
    
    # Raw vector matching the LightGBM input (15 features)
    f0 = float(t_len)
    f1 = float(t_wcount)
    f2 = float(len(b_clean))
    f3 = float(len(b_words))
    f4 = float(avg_word_len)
    f5 = float(upper_ratio)
    f6 = float(b_clean.count('!'))
    f7 = float(b_clean.count('?'))
    f8 = float(quote_count)
    f9 = float(b_clean.count('!') / b_len)
    f10 = float(b_clean.count('?') / b_len)
    f11 = float(sum(1 for c in t_clean if c.isupper()) / max(t_len, 1.0))
    f12 = float(punct_ratio)
    f13 = float(sum(1 for c in b_clean if c.isdigit()) / b_len)
    f14 = float(lexical_diversity)
    
    raw_vector = [f0, f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12, f13, f14]
    
    # Generate human-interpretable explainability tags
    tags: List[str] = []
    
    # Check Clickbait patterns
    detected_clickbait = [p for p in CLICKBAIT_PATTERNS if re.search(p, full_clean, re.IGNORECASE)]
    if detected_clickbait:
        tags.append("Sensational Urgency / Clickbait Phrasing")
        
    detected_journalistic = [p for p in JOURNALISTIC_PATTERNS if re.search(p, full_clean, re.IGNORECASE)]
    if detected_journalistic:
        tags.append("Attributed Source References")
        
    # Title analysis
    if t_len > 110:
        tags.append("Sensational Long Title")
    elif t_len > 0 and (sum(1 for c in t_clean if c.isupper()) / max(t_len, 1)) > 0.35:
        tags.append("High Title Capitalization (Clickbait Trigger)")
        
    if exclamation_count > 3:
        tags.append(f"Excessive Exclamation Marks ({exclamation_count}x)")
    elif exclamation_count > 0:
        tags.append("Emotional Punctuation Detected")
        
    if question_count > 2:
        tags.append("Speculative Question Headline Style")
        
    if upper_ratio > 0.08:
        tags.append("Unusual Uppercase Emphasis in Body")
        
    if lexical_diversity > 0.65 and b_wcount > 80:
        tags.append("Rich Journalistic Vocabulary")
    elif lexical_diversity < 0.38 and b_wcount > 80:
        tags.append("Repetitive Vocabulary / Keyword Stuffing")
        
    if quote_count > 6:
        tags.append("Frequent Direct Quotations Cited")
    elif quote_count == 0 and b_wcount > 100:
        tags.append("Lack of Attributed Source Quotes")
        
    if b_wcount < 40:
        tags.append("Brief Summary / Headline Dispatch")
    elif b_wcount > 350:
        tags.append("In-Depth Reporting Length")
        
    if not tags:
        tags.append("Standard Editorial Style")
        
    return features, raw_vector, tags
