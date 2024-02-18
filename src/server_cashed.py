import uvicorn
import asyncio
import aiohttp
import aioredis

from uuid import uuid4
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class UrlInfo(BaseModel):
    id: str
    status: str
    result: dict = []


class UrlsList(BaseModel):
    urls: list


urls_info = {}
app = FastAPI()
redis = None


# redis functions
async def get_redis():
    global redis
    if redis is None:
        redis = await aioredis.from_url("redis://localhost")


async def close_redis():
    if redis:
        await redis.close()


@app.on_event("startup")
async def startup_event():
    await get_redis()


@app.on_event("shutdown")
async def shutdown_event():
    await close_redis()


async def clear_cache_after_timeout(url, timeout):
    await asyncio.sleep(timeout)
    await redis.delete(url)


# server functions
@app.post("/api/v1/tasks/", status_code=201)
async def check_urls(urls_list: UrlsList):
    id = str(uuid4())
    urls_info[id] = UrlInfo(
                                id=id,
                                status="in progress",
                                result={},
                                )
    asyncio.create_task(address_verication(urls_list, id))
    return urls_info[id]


async def get_status(session, results, url, redis):
    cached_result = await redis.get(url)
    if cached_result:
        results[url] = cached_result.decode()
    else:
        async with session.get(url) as response:
            status_code = response.status
            results[str(url)] = str(status_code)
            await redis.set(url, str(status_code))


async def address_verication(urls_list, id):
    results = {}
    async with aiohttp.ClientSession() as session:
        for url in urls_list.urls:
            try:
                await get_status(session, results, url, redis)
            except aiohttp.ClientError as e:
                results[str(url)] = str(e)
                await redis.set(url, results[str(url)])
            asyncio.create_task(clear_cache_after_timeout(url, 100))
    urls_info[id].result = results
    urls_info[id].status = "done"


@app.get("/api/v1/tasks/{urls_id}")
async def get_url(urls_id: str):
    if urls_id not in urls_info:
        raise HTTPException(status_code=404, detail="Task not found")
    return urls_info[urls_id]


# for redis server
# nc localhost 6379
# GET domain
# QUIT
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8888)
