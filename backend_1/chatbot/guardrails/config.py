import os


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ============================================================
# INPUT LIMITS
# ============================================================

MAX_INPUT_LENGTH = int(
    os.getenv(
        "GUARDRAIL_MAX_INPUT_LENGTH",
        "2000",
    )
)


# ============================================================
# TOPIC POLICY
# ============================================================

ENFORCE_TOPIC_POLICY = (
    os.getenv(
        "ENFORCE_TOPIC_POLICY",
        "true",
    ).lower()
    == "true"
)


ALLOWED_TOPICS = [

    # --------------------------------------------------------
    # General Health
    # --------------------------------------------------------

    "health",
    "healthcare",
    "health information",
    "health education",
    "wellness",
    "healthy living",
    "general health",
    "medical information",
    "medical education",

    # --------------------------------------------------------
    # Symptoms
    # --------------------------------------------------------

    "symptoms",
    "headache",
    "fever",
    "cough",
    "cold",
    "flu",
    "sore throat",
    "stomach pain",
    "abdominal pain",
    "nausea",
    "vomiting",
    "diarrhea",
    "fatigue",
    "dizziness",
    "body pain",
    "joint pain",
    "muscle pain",
    "skin symptoms",

    # --------------------------------------------------------
    # Diseases / Conditions
    # --------------------------------------------------------

    "diseases",
    "medical conditions",
    "diabetes",
    "hypertension",
    "high blood pressure",
    "low blood pressure",
    "asthma",
    "allergies",
    "heart disease",
    "kidney disease",
    "liver disease",
    "thyroid conditions",
    "infection",
    "viral infection",
    "bacterial infection",
    "mental health",

    # --------------------------------------------------------
    # Medicines
    # --------------------------------------------------------

    "medicine",
    "medicines",
    "medication",
    "medications",
    "drug information",
    "medicine information",
    "medicine uses",
    "medicine side effects",
    "medication side effects",
    "drug interactions",
    "medicine interactions",
    "medicine precautions",
    "medicine safety",
    "prescription medicine",
    "over the counter medicine",
    "otc medicine",
    "antibiotics",
    "painkillers",
    "vitamins",
    "supplements",

    # --------------------------------------------------------
    # Pharmacy
    # --------------------------------------------------------

    "pharmacy",
    "pharmacist",
    "pharmacy services",
    "medicine availability",
    "medicine price",
    "medicine order",
    "medicine orders",
    "prescription",
    "prescription medicine",
    "prescription information",

    # --------------------------------------------------------
    # Medication Information
    # --------------------------------------------------------

    "dosage information",
    "dose information",
    "how medicine works",
    "when to take medicine",
    "how to take medicine",
    "medicine storage",
    "medicine expiry",
    "missed dose",
    "medicine warnings",
    "medicine precautions",

    # --------------------------------------------------------
    # Medical Reports
    # --------------------------------------------------------

    "medical report",
    "medical reports",
    "lab report",
    "laboratory report",
    "blood test",
    "blood test report",
    "urine test",
    "urine test report",
    "test results",
    "medical test",
    "medical test results",
    "health report",
    "report explanation",

    # --------------------------------------------------------
    # Basic Medical Tests
    # --------------------------------------------------------

    "blood pressure",
    "blood sugar",
    "blood glucose",
    "cholesterol",
    "hemoglobin",
    "cbc",
    "blood count",
    "temperature",
    "pulse",
    "heart rate",
    "oxygen level",
    "oxygen saturation",
    "bmi",

    # --------------------------------------------------------
    # Prevention
    # --------------------------------------------------------

    "disease prevention",
    "infection prevention",
    "hygiene",
    "vaccination",
    "vaccines",
    "immunization",
    "nutrition",
    "diet",
    "exercise",
    "sleep",
    "stress management",

    # --------------------------------------------------------
    # First Aid / Safety
    # --------------------------------------------------------

    "first aid",
    "basic first aid",
    "health emergency",
    "medical emergency",
    "when to see a doctor",
    "when to see a pharmacist",
    "urgent medical care",

    # --------------------------------------------------------
    # Healthcare Professionals
    # --------------------------------------------------------

    "doctor",
    "doctors",
    "pharmacist",
    "pharmacists",
    "nurse",
    "nurses",
    "healthcare provider",
    "healthcare professional",
    "medical specialist",

    # --------------------------------------------------------
    # Account
    # --------------------------------------------------------

    "account",
    "user account",
    "patient account",
    "customer account",
    "profile",
    "patient profile",
    "account help",
    "profile help",
    "account details",
    "account information",
    "login",
    "sign in",
    "sign up",
    "registration",
    "password",
    "account settings",

    # --------------------------------------------------------
    # Pharmacy Account
    # --------------------------------------------------------

    "pharmacy account",
    "pharmacy profile",
    "pharmacy login",
    "pharmacy registration",
    "pharmacy settings",

    # --------------------------------------------------------
    # Orders
    # --------------------------------------------------------

    "orders",
    "medicine orders",
    "order status",
    "order tracking",
    "order cancellation",
    "order modification",
    "order history",
    "delivery",
    "medicine delivery",

    # --------------------------------------------------------
    # Reports
    # --------------------------------------------------------

    "reports",
    "health reports",
    "medical reports",
    "patient reports",
    "report history",

    # --------------------------------------------------------
    # Company / Application Information
    # --------------------------------------------------------

    "company information",
    "company details",
    "about the company",
    "about the application",
    "app information",
    "application information",
    "pharmacy information",
    "pharmacy services",
    "healthcare services",
    "company services",
    "company policies",
    "privacy policy",
    "terms and conditions",

    # --------------------------------------------------------
    # AI / Security Education
    # --------------------------------------------------------

    "ai",
    "artificial intelligence",
    "ai assistant",
    "health ai",
    "medical ai",
    "ai safety",
    "prompt injection",
    "ai guardrails",
    "system prompt",
    "api key",
    "security",
]


# ============================================================
# NEMO GUARDRAILS
# ============================================================

# Expected structure:
#
# guardrails/
# ├── config.py
# ├── service.py
# └── nemo/
#     ├── config.yml
#     └── ...
#
# You can override this with NEMO_CONFIG_PATH in .env.

NEMO_CONFIG_PATH = os.getenv(
    "NEMO_CONFIG_PATH",
    os.path.join(
        BASE_DIR,
        "nemo",
    ),
)


# ============================================================
# NEMO CHECK MODEL
# ============================================================

NEMO_CHECK_MODEL = os.getenv(
    "NEMO_CHECK_MODEL",
    "openai/gpt-oss-20b",
)


# ============================================================
# GUARDRAILS ENABLED
# ============================================================

GUARDRAILS_ENABLED = (
    os.getenv(
        "GUARDRAILS_ENABLED",
        "true",
    ).lower()
    == "true"
)


# ============================================================
# GUARDRAIL FAILURE BEHAVIOR
# ============================================================

ALLOW_SIMPLE_RESPONSES_ON_FAILURE = (
    os.getenv(
        "ALLOW_SIMPLE_RESPONSES_ON_FAILURE",
        "true",
    ).lower()
    == "true"
)


FAIL_SAFE_MESSAGE = os.getenv(
    "FAIL_SAFE_MESSAGE",
    (
        "I couldn't process that request right now. "
        "Please try again."
    ),
)


# ============================================================
# RATE LIMITING
# ============================================================

RATE_LIMIT_ENABLED = (
    os.getenv(
        "RATE_LIMIT_ENABLED",
        "true",
    ).lower()
    == "true"
)


# ============================================================
# AUTHENTICATED USER LIMITS
# ============================================================

RATE_LIMIT_PER_MINUTE = int(
    os.getenv(
        "RATE_LIMIT_PER_MINUTE",
        "30",
    )
)


RATE_LIMIT_PER_HOUR = int(
    os.getenv(
        "RATE_LIMIT_PER_HOUR",
        "300",
    )
)


# ============================================================
# GUEST / ANONYMOUS USER LIMITS
# ============================================================

GUEST_RATE_LIMIT_PER_MINUTE = int(
    os.getenv(
        "GUEST_RATE_LIMIT_PER_MINUTE",
        "10",
    )
)


GUEST_RATE_LIMIT_PER_HOUR = int(
    os.getenv(
        "GUEST_RATE_LIMIT_PER_HOUR",
        "100",
    )
)


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

RATE_LIMIT_PER_MINUTE_ANONYMOUS = (
    GUEST_RATE_LIMIT_PER_MINUTE
)


# ============================================================
# REFUSAL MESSAGES
# ============================================================

REFUSAL_MESSAGES = {

    # --------------------------------------------------------
    # Prompt injection
    # --------------------------------------------------------

    "prompt_injection": (
        "I can't help with requests that attempt to "
        "override my instructions."
    ),

    # --------------------------------------------------------
    # Policy
    # --------------------------------------------------------

    "policy": (
        "I'm unable to help with that request. "
        "I can help with health, medicines, symptoms, "
        "medical reports, pharmacy services, and "
        "general healthcare information."
    ),

    # --------------------------------------------------------
    # Service failure
    # --------------------------------------------------------

    "service_failure": (
        "I couldn't process that request right now. "
        "Please try again."
    ),

    # --------------------------------------------------------
    # Off topic
    # --------------------------------------------------------

    "off_topic": (
        "I'm built to help with health, medicines, "
        "symptoms, medical reports, pharmacy services, "
        "and general healthcare information. "
        "I can't help with that request."
    ),

    # --------------------------------------------------------
    # Input too long
    # --------------------------------------------------------

    "input_too_long": (
        "Your message is too long. Please shorten it."
    ),

    # --------------------------------------------------------
    # Invalid input
    # --------------------------------------------------------

    "invalid_input": (
        "Please provide a valid message."
    ),

    # --------------------------------------------------------
    # Output secret
    # --------------------------------------------------------

    "output_secret": (
        "I can't provide that response because it may "
        "contain protected system information or secrets."
    ),

    # --------------------------------------------------------
    # Unsafe medical request
    # --------------------------------------------------------

    "unsafe_medical_request": (
        "I can't provide instructions that could seriously "
        "harm someone. I can provide general health and "
        "medication safety information instead."
    ),

    # --------------------------------------------------------
    # Dangerous medication request
    # --------------------------------------------------------

    "dangerous_medication": (
        "I can't provide instructions for unsafe medication "
        "use, overdose, misuse, or intentionally harmful use. "
        "I can provide general medication safety information."
    ),

    # --------------------------------------------------------
    # Diagnosis
    # --------------------------------------------------------

    "diagnosis": (
        "I can't confirm a medical diagnosis from a chat alone. "
        "I can provide general health information and explain "
        "when professional medical care may be appropriate."
    ),

    # --------------------------------------------------------
    # Emergency
    # --------------------------------------------------------

    "emergency": (
        "If this may be a medical emergency or someone is in "
        "immediate danger, please seek urgent medical attention "
        "or contact your local emergency service."
    ),

    # --------------------------------------------------------
    # Unsafe dosage
    # --------------------------------------------------------

    "unsafe_dosage": (
        "I can't provide a personalized medication dose without "
        "the necessary clinical information. Please follow the "
        "prescribed or labeled directions and consult a doctor "
        "or pharmacist if you're unsure."
    ),

    # --------------------------------------------------------
    # Private health information
    # --------------------------------------------------------

    "private_health_information": (
        "I can't provide another person's private health "
        "information or confidential medical records."
    ),
}


# ============================================================
# OFF-TOPIC RESPONSE
# ============================================================

OFF_TOPIC_RESPONSE = REFUSAL_MESSAGES["off_topic"]


# ============================================================
# DEBUG
# ============================================================

GUARDRAIL_DEBUG = (
    os.getenv(
        "GUARDRAIL_DEBUG",
        "true",
    ).lower()
    == "true"
)


# ============================================================
# GROQ API KEY
# ============================================================

# Keep the actual key in your environment/.env file.
# NEVER hard-code the API key here.

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    "",
)


# ============================================================
# OPTIONAL CONFIGURATION VALIDATION
# ============================================================

NEMO_CONFIG_EXISTS = os.path.isdir(
    NEMO_CONFIG_PATH
)


# ============================================================
# DEBUG INFORMATION
# ============================================================

if GUARDRAIL_DEBUG:

    print("\n" + "=" * 70)
    print("HEALTH AI GUARDRAIL CONFIGURATION")
    print("=" * 70)

    print(
        "Guardrails enabled :",
        GUARDRAILS_ENABLED,
    )

    print(
        "Topic policy       :",
        ENFORCE_TOPIC_POLICY,
    )

    print(
        "Max input length   :",
        MAX_INPUT_LENGTH,
    )

    print(
        "NeMo config path   :",
        NEMO_CONFIG_PATH,
    )

    print(
        "NeMo config exists :",
        NEMO_CONFIG_EXISTS,
    )

    print(
        "NeMo check model   :",
        NEMO_CHECK_MODEL,
    )

    print(
        "Groq API key set   :",
        bool(GROQ_API_KEY),
    )

    print(
        "Allowed topics     :",
        len(ALLOWED_TOPICS),
    )

    print("=" * 70 + "\n")