import fastapi
from fastapi.middleware.cors import CORSMiddleware
from .models import ScriptRequest, ScriptResponse, ParagraphRequest
from .services import AnthropicService
from .config import CORS_ORIGINS
from fastapi import HTTPException


app = fastapi.FastAPI()


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Initialize Anthropic service
anthropic_service = AnthropicService()

@app.get("/")
async def root():
    return {"message": "Script Generator API"}

@app.post("/generate-script", response_model=ScriptResponse)
async def generate_script(request: ScriptRequest):
    result = await anthropic_service.generate_script(
        request.title,
        request.inspirational_transcript,
        request.word_count,
        request.forbidden_words,
        request.structure_prompt
    )
    # If not enough words, continue the story
    while not result["completed"] and result["remaining_words"] > 0:
        result = await anthropic_service.continue_script(
            request.title,
            request.inspirational_transcript,
            request.forbidden_words,
            request.structure_prompt,
            result["paragraphs"],
            result["remaining_words"]
        )
    return result


@app.post("/regenerate-segment")
async def regenerate_segment(request: dict):
    try:
        # Log the incoming request for debugging
        print("Received regenerate segment request:", request)
        
        # Validate required fields
        required_fields = ["title", "context_before", "context_after", "segment_word_count"]
        missing_fields = [field for field in required_fields if field not in request]
        if missing_fields:
            raise HTTPException(status_code=400, detail=f"Missing required fields: {', '.join(missing_fields)}")

        result = anthropic_service.regenerate_segment(
            title=request.get("title"),
            inspirational_transcript=request.get("inspirational_transcript"),
            forbidden_words=request.get("forbidden_words", []),
            structure_prompt=request.get("structure_prompt", ""),
            context_before=request.get("context_before", ""),
            context_after=request.get("context_after", ""),
            segment_word_count=request.get("segment_word_count", 500)
        )
        
        # Log the result for debugging
        print("Regenerate segment result:", result)
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("Error in regenerate_segment:", str(e))  # Add logging
        raise HTTPException(status_code=500, detail=str(e))

