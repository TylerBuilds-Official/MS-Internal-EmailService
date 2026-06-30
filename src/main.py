"""FastAPI application entry point."""

import logging

from dotenv import load_dotenv

load_dotenv()

from api.build.build_api import build_api


logging.basicConfig(level=logging.INFO)

app = build_api()


