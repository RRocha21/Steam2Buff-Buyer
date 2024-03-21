from steam2buff import logger

from datetime import datetime

import asyncpg
from psycopg2 import sql

import json

import httpx

class Postgres:
    base_url = 'http://192.168.3.29:8000'

    def __init__(self, request_interval):
        self.opener = httpx.AsyncClient()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.opener.aclose()
            
    async def get_last_entry(self):
        try:
            url = f'{self.base_url}/steam2buff/last'
                        
            response = await self.opener.get(url)
            
            return response.json()
        except Exception as e:
            logger.error(f'Failed to get last entry from PostgreSQL: {e}')
            return None