async def start_proxy_finder():
    while True:
        await find_proxies()
        time.sleep(60)  # ждать 60 секунд перед следующей итерацией

if __name__ == "__main__":
    asyncio.run(start_proxy_finder())

import threading
from proxy import find_proxies

def start_proxy_finder():
    t = threading.Thread(target=find_proxies, args=())
    t.daemon = True
    t.start()