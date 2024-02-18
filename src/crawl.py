import ssl
import json
import asyncio
import aiohttp
import argparse


SERVER_URL = "http://127.0.0.1:8888/api/v1/tasks/"


async def send_urls_to_server(urls):
    async with aiohttp.ClientSession() as session:
        payload = {"urls": urls}
        async with session.post(
                                SERVER_URL,
                                json=payload,
                                ) as response:
            urls_info = await response.json()
            urls_id = urls_info["id"]

        await check_answer(urls_id, session)


async def check_answer(urls_id, session):
    while True:
        async with session.get(
                                f"{SERVER_URL}{urls_id}",
                              ) as response:
            result = await response.json()
            if "status" in result and result["status"] == "done":
                for url, status_code in result["result"].items():
                    print(f" URL: {url}\tStatus: {status_code}")
                break
        await asyncio.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="Перечислите urls")
    parser.add_argument("urls",
                        metavar="URL",
                        type=str,
                        nargs='+',
                        )
    args = parser.parse_args()
    urls = args.urls
    asyncio.run(send_urls_to_server(urls))


if __name__ == "__main__":
    main()
