import sqlite3
import random
import asyncio
import aiohttp
import async_timeout



class ProxyDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_table()

    def create_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY,
                ip TEXT,
                port TEXT,
                country TEXT,
                status TEXT,
                last_checked TEXT
            )
        """)
        conn.commit()
        conn.close()

    def insert_proxy(self, ip, port, country, status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO proxies (ip, port, country, status, last_checked)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (ip, port, country, status))
        conn.commit()
        conn.close()

    def update_proxy_status(self, ip, port, status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE proxies
            SET status=?, last_checked=datetime('now')
            WHERE ip=? AND port=?
        """, (status, ip, port))
        conn.commit()
        conn.close()

    def get_working_proxies(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ip, port
            FROM proxies
            WHERE status='working'
        """)
        proxies = cursor.fetchall()
        conn.close()
        return [f"{proxy[0]}:{proxy[1]}" for proxy in proxies]


async def check_proxy(ip, port):
    url = 'https://httpbin.org/get'
    proxy_url = f"http://{ip}:{port}"
    async with aiohttp.ClientSession() as session:
        try:
            with async_timeout.timeout(5):
                async with session.get(url, proxy=proxy_url) as response:
                    return response.status == 200
        except:
            return False


async def test_proxies(proxies):
    working_proxies = []
    async with asyncio.Semaphore(10):
        tasks = []
        for proxy in proxies:
            ip, port = proxy.split(':')
            task = asyncio.ensure_future(check_proxy(ip, port))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        for i, response in enumerate(responses):
            if response:
                ip, port = proxies[i].split(':')
                working_proxies.append((ip, port))
    return working_proxies


async def update_proxy_status(proxy_db):
    proxies = proxy_db.get_working_proxies()
    working_proxies = await test_proxies(proxies)
    conn = sqlite3.connect(proxy_db.db_path)
    cursor = conn.cursor()
    for ip, port in proxies:
        if (ip, port) in working_proxies:
            cursor.execute("""
                UPDATE proxies
                SET status='working', last_checked=datetime('now')
                WHERE ip=? AND port=?
            """, (ip, port))
        else:
            cursor.execute("""
                UPDATE proxies
                SET status='not working', last_checked=datetime('now')
                WHERE ip=? AND port=?
            """, (ip, port))
    conn.commit()
    conn.close()


async def find_proxies(ip_range, port_range, num_workers=10):
    """
    Find working proxies by checking the given range of IP addresses and port numbers asynchronously.

    Args:
        ip_range (list): List of IP address ranges to check.
        port_range (list): List of port ranges to check.
        num_workers (int): Number of worker threads to use for checking proxies. Default is 10.

    Returns:
        List of tuples containing the working proxies in the form (ip, port).
    """
    proxies = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for ip in ip_range:
            for port in port_range:
                task = asyncio.create_task(check_proxy(ip, port, session))
                tasks.append(task)
        working_proxies = await asyncio.gather(*tasks)

    for proxy in working_proxies:
        if proxy is not None:
            proxies.append(proxy)

    return proxies


async def check_proxy(ip, port, session):
    """
    Check if the given proxy is working by attempting to connect to a website.

    Args:
        ip (str): IP address of the proxy.
        port (str): Port number of the proxy.
        session (aiohttp.ClientSession): An aiohttp client session object to use for the connection.

    Returns:
        Tuple of the working proxy in the form (ip, port) or None if the proxy is not working.
    """
    proxy = f"http://{ip}:{port}"
    try:
        async with session.get(TEST_URL, proxy=proxy, timeout=5) as response:
            if response.status == 200:
                # Update proxy status in database
                update_proxy_status(ip, port, True)
                return (ip, port)
    except:
        pass
    # Update proxy status in database
    update_proxy_status(ip, port, False)
    return None



class ProxyManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    def get_proxies(self, country=None):
        if country is None:
            self.cursor.execute('SELECT * FROM proxies')
        else:
            self.cursor.execute('SELECT * FROM proxies WHERE country=?', (country,))
        proxies = self.cursor.fetchall()
        return proxies

    def get_random_proxy(self, country=None):
        proxies = self.get_proxies(country)
        if len(proxies) == 0:
            return None
        else:
            return random.choice(proxies)
