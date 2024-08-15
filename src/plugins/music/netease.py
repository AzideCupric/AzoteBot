"""网易云音乐

https://github.com/Binaryify/NeteaseCloudMusicApi
"""

import httpx
from nonebot.adapters.onebot.v11 import MessageSegment


async def call_netease_api(keywords: str) -> MessageSegment | None:
    """网易云搜索 API"""
    if not keywords:
        return None

    # 构造请求数据
    url = f"http://netease:3000/search?keywords={keywords}"

    try:
        # 使用 httpx 库发送最终的请求
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            rjson = r.json()

            if rjson["code"] != 200:
                # 如果 code 不是 200，说明出错
                return None

            # 获取音乐 ID，并返回对应的 CQ 码
            music_id = rjson["result"]["songs"][0]["id"]

            return MessageSegment.music("163", music_id)

    except (httpx.HTTPError, KeyError):
        # 抛出上面任何异常，说明调用失败
        return None
