import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Settings
API_HOST = "0.0.0.0"
API_PORT = 8000
DEBUG = True

# CORS Settings
CORS_ORIGINS = [
    "https://word-generator-frontend.vercel.app/"
]

# Anthropic API Settings
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY environment variable is not set. "
        "Please set it in your .env file or environment variables."
    ) 