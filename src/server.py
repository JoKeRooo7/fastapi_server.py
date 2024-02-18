import asyncio
import aiohttp
import uvicorn

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


async def address_verication(urls_list, id):
    results = {}
    async with aiohttp.ClientSession() as session:
        for url in urls_list.urls:
            try:
                async with session.get(url) as response:
                    status_code = response.status
                    results[str(url)] = str(status_code)
            except aiohttp.ClientError as e:
                results[str(url)] = str(e)
    urls_info[id].result = results
    urls_info[id].status = "done"


@app.get("/api/v1/tasks/{urls_id}")
async def get_url(urls_id: str):
    if urls_id not in urls_info:
        raise HTTPException(status_code=404, detail="Task not found")
    return urls_info[urls_id]


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8888)
