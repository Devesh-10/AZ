"""
Lambda handler for TIA LangGraph Backend
Uses Mangum to wrap FastAPI for AWS Lambda
"""

from mangum import Mangum
from app.main import app

handler = Mangum(app, lifespan="off")
