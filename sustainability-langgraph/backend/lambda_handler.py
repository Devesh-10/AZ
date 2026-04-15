"""
AWS Lambda handler for Sustainability Insight Agent
Uses Mangum to adapt FastAPI to Lambda
"""

from mangum import Mangum
from main import app

handler = Mangum(app, lifespan="off")
