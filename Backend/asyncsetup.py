from aiohttp import web
import asyncio
import app

async def store_url_and_process_algorithm():
    return ""
    
app = web.Application()
app.add_routes([
    web.post('/check_url', store_url_and_process_algorithm)
])

if __name__ == '__main__':  
    web.run_app(app)