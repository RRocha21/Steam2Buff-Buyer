import asyncio

from steam2buff import logger

from pyppeteer import launch
from pyppeteer.errors import TimeoutError, NetworkError

class SteamSelenium:

    def __init__(self, sessionid=None, steamLoginSecure=None):
        logger.info('SteamPyppeteer', sessionid, steamLoginSecure)
        self.sessionid = sessionid
        self.steamLoginSecure = steamLoginSecure
        self.browser = None
        self.page = None
        
    async def intercept_request(self, req):
        # Skip images, fonts, and stylesheets
        if req.resourceType in ['image', 'font', 'stylesheet']:
            await req.abort()
        else:
            await req.continue_()

    async def __aenter__(self):
        try:
            self.browser = await launch(
                headless=True,
            )
            self.page = await self.browser.newPage()
            
            await self.page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0")
            
            pages = await self.browser.pages()
            
            await pages[0].close()
            
            # delete previous page 
            
            await self.page.setRequestInterception(True)
            
            self.page.on('request', lambda req: asyncio.ensure_future(self.intercept_request(req)))
            
            await self.page.goto(
                'https://steamcommunity.com/market/listings/730/AWP%20%7C%20Neo-Noir%20%28Field-Tested%29'
            )

            await self.page.setCookie(
                {"name": "sessionid", "value": self.sessionid},
                {"name": "steamLoginSecure", "value": self.steamLoginSecure},
            )

            await self.page.reload()

            return self
        except Exception as e:
            logger.error(f'Failed to open Steam: {e}')
            exit(1)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.browser.close()

    async def open_url(self, url, listing_id):
        logger.info(f'Start Open URL: {url}')
        await self.page.goto(url, {
            'waitUntil': 'domcontentloaded'
        })
        logger.info(f'Opened URL: {url}')
        try:
            try:
                await self.page.waitForSelector(f'#largeiteminfo_item_name', timeout=500)
                    # Selector found, exit the loop
                logger.info(f'Page Loaded')
            except TimeoutError:
                try:
                    await self.page.reload({ 'waitUntil': 'load' })
                    await self.page.waitForSelector(f'#largeiteminfo_item_name', timeout=500)
                    logger.info(f'Page Loaded 2')
                except TimeoutError:
                    try:
                        await self.page.reload({'waitUntil': 'load' })
                        await self.page.waitForSelector(f'#largeiteminfo_item_name', timeout=500)
                        logger.info(f'Page Loaded 3')
                    except TimeoutError:
                        logger.error(f'Failed to locate element within timeout')
                        return False
            
            
            try:
                element = await self.page.waitForSelector(f'#listing_{listing_id}', timeout=2000)
                if not element:
                    logger.error(f'Failed to locate element with id: {listing_id}')
                    return False
                logger.info(f'Listing Found')
            except TimeoutError:
                logger.error(f'Failed to locate listing')
                return False

            try:
                button_to_click = await element.querySelector('div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > a')
                if not button_to_click:
                    logger.error('Button not found')
                    return False
                logger.info(f'Button Found')
            except Exception as e:
                logger.error(f'Error occurred while finding the button: {e}')
                return False

            try:
                await button_to_click.click()
                logger.info('Clicked on the element successfully')
            except Exception as e:
                logger.error(f'Failed to click on element: {e}')
                return False

            try:
                await self.page.waitForSelector('#market_buynow_dialog_accept_ssa_container', timeout=5000)
                await self.page.evaluate('''document.querySelector('#market_buynow_dialog_accept_ssa_container input').click();''')
                logger.info('Clicked on the accept checkbox successfully')
            except Exception as e:
                logger.error(f'Failed to click on the accept checkbox: {e}')
                return False

            # Wait for the payment button to appear
            try:
                await self.page.waitForSelector('#market_buynow_dialog_paymentinfo_bottomactions', timeout=5000)
                await self.page.evaluate('''document.querySelector('#market_buynow_dialog_paymentinfo_bottomactions a').click();''')
                logger.info('Clicked on the payment button successfully')
            except Exception as e:
                logger.error(f'Failed to click on the payment button: {e}')
                return False

            return True
        except Exception as e:
            logger.error(f'Failed to open URL: {e}')
            return False