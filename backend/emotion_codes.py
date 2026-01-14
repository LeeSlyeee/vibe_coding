
# 60-Class Emotion Mapping for Ultra-Fine-Grained Analysis
# Based on AI Hub 'Sensitivity Dialogue Corpus' (감성대화말뭉치)
# Labels inferred from data inspection.

EMOTION_CODE_MAP = {
    # --- 분노 (Anger) Group ---
    "E10": "분노 (노여움/억울)",  # Unfairness, Boss, Rules
    "E11": "짜증 (불쾌함)",       # Annoyance, Noise, Rudeness
    "E32": "분노 (부당대우)",     # Unfair treatment, Discrimination
    "E41": "짜증 (성가심)",       # Jealousy, Envy, Petty annoyance
    "E42": "배신감",             # Betrayal, Scammed, Let down
    "E46": "분노 (희생강요)",     # Forced sacrifice, Unappreciated
    "E47": "분노 (억울함)",       # Wrongly accused, Unfair result
    "E51": "불안 (당혹/난처)",    # Awkward, Sudden trouble (Also anger trigger)
    "E52": "걱정 (신체/건강)",    # Health worry, Aging (Data shows worry/shame)
    "E57": "혐오 (불쾌)",         # Disgust, Dislike, Rejection

    # --- 슬픔 (Sadness) Group ---
    "E12": "슬픔 (비통함)",       # Grief, Loss, Deep sadness
    "E13": "외로움 (고독)",       # Loneliness, Isolation
    "E14": "무기력 (허무)",       # Lethargy, Lack of motivation, Burnout
    "E35": "후회 (자책)",         # Regret, Guilt, Self-blame
    "E30": "슬픔 (낙담)",         # Disappointment, Failure (Exam)
    "E31": "슬픔 (가난/불행)",    # Poverty, Hardship, Misery
    "E33": "슬픔 (좌절)",         # Frustration, Obstacles
    "E34": "슬픔 (상실감)",       # Loss of something/someone
    "E36": "슬픔 (눈물)",         # Crying, Overwhelmed
    "E37": "슬픔 (한탄)",         # Lamenting, Complaining about life
    "E38": "슬픔 (진로고민)",     # Career worry, Future sadness
    "E39": "슬픔 (질병/고통)",    # Sickness, Physical pain
    "E40": "슬픔 (스트레스)",     # Stress, Overworked
    "E43": "슬픔 (소외감)",       # Left out, Unmarried alone
    "E44": "충격 (실망)",         # Shock, Disappointment (Company bankruptcy)
    "E45": "비참함 (비교)",       # Misery from comparison, Relative poverty
    "E48": "괴로움 (경제)",       # Financial suffering, Debt
    "E49": "외로움 (방치)",       # Abandoned, Neglected
    "E53": "지침 (피로)",         # Exhaustion, Tired of life
    "E54": "열등감",             # Inferiority, Comparison
    "E55": "죄책감",             # Guilt, Apology
    "E56": "부끄러움 (수치)",     # Shame, Embarrassment (Job/Status)
    "E58": "한심함 (자괴감)",     # Self-loathing, Pathetic feeling

    # --- 불안 (Anxiety) Group ---
    "E15": "불안 (걱정)",         # General Worry, Anxiety
    "E16": "당황 (곤란)",         # Flustered, Predicament
    "E17": "두려움 (공포)",       # Fear, Scary situation
    "E18": "혼란",               # Confusion, Chaos
    "E19": "불안 (압박)",         # Pressure, Deadline
    "E20": "불안 (불확실)",       # Uncertainty, Waiting
    "E21": "불안 (위협)",         # Threat, Danger
    "E22": "불안 (초조)",         # Nervousness, Restless
    "E23": "불안 (의심)",         # Suspicion, Doubt
    "E24": "긴장",               # Tension, Nervous
    "E25": "걱정 (자녀/가족)",    # Family worry
    "E26": "불안 (대인관계)",     # Social anxiety
    "E27": "걱정 (노후)",         # Old age worry
    "E28": "불안 (건강염려)",     # Hypochondria
    "E29": "불안 (경제)",         # Financial anxiety
    "E50": "당황 (당혹)",         # Taken aback, Flustered (Sudden event)
    "E59": "당황 (오해)",         # Misunderstanding, Mistaken identity

    # --- 기쁨 (Happiness) Group ---
    "E60": "기쁨 (환희)",         # Joy, Birth, Huge Success
    "E61": "감사",               # Gratitude, Thankful
    "E62": "뿌듯함 (성취)",       # Achievement, Trust
    "E63": "편안함 (안정)",       # Comfort, Stability, Relationship
    "E64": "만족 (직장/환경)",    # Satisfaction with job/life
    "E65": "설렘 (사랑/합격)",    # Fluttering, Love, Success
    "E66": "홀가분함 (안도)",     # Relief, Freedom (Quitting job)
    "E67": "기쁨 (합격/성공)",    # Job success, Goal reached
    "E68": "신남 (칭찬)",         # Excited, Praised
    "E69": "자신감 (확신)"        # Confidence, Optimism
}

# Inverse map for label lookups if needed
LABEL_TO_CODE = {v: k for k, v in EMOTION_CODE_MAP.items()}
