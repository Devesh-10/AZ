"""
Lambda handler for MIA LangGraph Backend
Uses Mangum to wrap FastAPI for AWS Lambda
"""

from mangum import Mangum
from app.main import app

# Create Mangum handler for Lambda
handler = Mangum(app, lifespan="off")
