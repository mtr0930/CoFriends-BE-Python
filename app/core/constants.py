"""
Constants used throughout the application
"""

# Default menu types
DEFAULT_MENU_TYPES = [
    "한식",
    "중식",
    "일식",
    "양식",
    "분식",
    "치킨",
    "피자",
    "햄버거",
    "아시안",
    "카페/디저트"
]

# Redis key prefixes
CHAT_KEY_PREFIX = "chat:"
PLACE_KEY_PREFIX = "places:"

# Cache expiration times (in seconds)
CHAT_EXPIRATION_DAYS = 30
PLACE_EXPIRATION_DAYS = 30

