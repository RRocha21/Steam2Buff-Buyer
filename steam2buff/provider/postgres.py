from steam2buff import logger

from datetime import datetime

import asyncpg
from psycopg2 import sql

import json

import httpx

from urllib.parse import unquote

class Postgres:
    base_url = 'http://192.168.3.29:8000'

    def __init__(self, request_interval):
        self.opener = httpx.AsyncClient()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.opener.aclose()
            
    async def insert_purchase(self, purchase):
        try:
            link = purchase['link']
            market_hash = unquote(link.split("/")[-1])
            store = 'steam2buff'
            purchase_price = float(purchase['price'])
            purchase_date = datetime.now()
            float_value = float(purchase['float_value'])
            
            url = f'{self.base_url}/purchase/rr'
                        
            response = await self.opener.post(url, params={
                'market_hash': market_hash,
                'store': store,
                'purchase_price': purchase_price,
                'purchase_date': purchase_date,
                'float_value': float_value
            })
            
            return response.json()
        except Exception as e:
            logger.error(f'Failed to get last entry from PostgreSQL: {e}')
            return None