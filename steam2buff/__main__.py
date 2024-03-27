import asyncio
import asyncpg_listen
from steam2buff.provider.steamSelenium import SteamSelenium
from steam2buff.provider.postgres import Postgres
from steam2buff import logger, config
from urllib.parse import unquote
from win11toast import toast
from datetime import datetime

import json

last_entry_checked = None

iconTrue = {
    'src': 'https://i.ibb.co/0sYG97C/checkmark-true.png',
    'placement': 'appLogoOverride'
}

iconFalse = {
    'src': 'https://i.ibb.co/mzWDY0n/checkmark-false.png',
    'placement': 'appLogoOverride'
}

async def notify(title, text, result):
    if result:
        asyncio.create_task(toast_async(title, text, icon=iconTrue, app_id='Microsoft.WindowsTerminal_8wekyb3d8bbwe!App'))
    else:
        asyncio.create_task(toast_async(title, text, icon=iconFalse, app_id='Microsoft.WindowsTerminal_8wekyb3d8bbwe!App'))

async def toast_async(title, text, icon, app_id):
    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(None, lambda: toast(title, text, icon=icon, app_id=app_id))
    await future

async def handle_notifications(notification: asyncpg_listen.NotificationOrTimeout, steamSelenium: SteamSelenium, postgres: Postgres) -> None:
    global last_entry_checked

    # check if the notification has a payload
    if not hasattr(notification, 'payload'):
        return
    
    notification_payload = notification.payload
    notification_json = json.loads(notification_payload)
    notification_data = notification_json.get('data')

    url = notification_data['link']
    listing_id = notification_data['id']
    updated_at = notification_data['updatedat']
    
    logger.info(f"Received notification for url: {url} and listing_id: {listing_id} at {updated_at}")
    

    if notification_data['currency'] == 'SOLD' or listing_id == last_entry_checked:
        logger.info(f"SOLD or already checked")
        return
    
    bought = await steamSelenium.open_url(url, listing_id)
            
    if bought:
        await notify('Steam2Buff', 'Item Bought!', True)
        await postgres.insert_purchase(notification_data)
    else:   
        await notify('Steam2Buff', 'Item Not Bought!', False)
        
    last_entry_checked = listing_id

async def listen_for_changes(steamSelenium: SteamSelenium, postgres: Postgres):
    listener = asyncpg_listen.NotificationListener(
        asyncpg_listen.connect_func(
            user='postgres',
            password='benfica10',
            database='Buff_Steam',
            host='192.168.3.29'
        )
    )
    listener_task = asyncio.create_task(
        listener.run(
            {"steam2buff_table_changes": lambda notification: handle_notifications(notification, steamSelenium, postgres)},
            policy=asyncpg_listen.ListenPolicy.LAST,
            notification_timeout=30
        )
    )
    try:
        await listener_task
    finally:
        await listener.close()

async def main():
    try:
        async with SteamSelenium(
            sessionid=config['steam']['sessionid'],
            steamLoginSecure=config['steam']['steamLoginSecure'],
        ) as steamSelenium, Postgres(
            request_interval=10
        ) as postgres:
            await listen_for_changes(steamSelenium, postgres)
            
    except KeyboardInterrupt:
        exit('Bye~')


if __name__ == '__main__':
    asyncio.run(main())
