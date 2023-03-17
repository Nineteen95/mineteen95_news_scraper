import asyncio
from datetime import datetime, timedelta
from typing import List

from proxy import Proxy


async def refresh_proxy(find_proxies_func, proxies: List[Proxy], refresh_interval: int):
    """
    Асинхронная функция, которая обновляет список прокси-серверов каждые refresh_interval секунд
    :param find_proxies_func: функция для поиска новых прокси
    :param proxies: список текущих прокси
    :param refresh_interval: интервал обновления списка прокси в секундах
    """
    while True:
        try:
            new_proxies = await find_proxies_func()
            for p in new_proxies:
                if p not in proxies:
                    proxies.append(p)
            await asyncio.sleep(refresh_interval)
        except Exception as e:
            print(f"Error refreshing proxies: {e}")
