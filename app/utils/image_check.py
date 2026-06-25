"""
Checagem de imagens remotas em Markdown antes de gerar o PDF + guard de SSRF.

- check_and_placeholder_images(): URL de imagem http(s) quebrada/insegura vira
  placeholder no PDF e é devolvida pra avisar o usuário (ex.: via SSE). Não bloqueia.
- safe_url_fetcher(): fetcher pro WeasyPrint que aplica o mesmo guard ao baixar a
  imagem de verdade no render (o sink real de SSRF).

Guard de SSRF: exige esquema http/https, resolve o host e rejeita IPs internos
(loopback/privado/link-local/reservado/multicast). Não segue redirect automático;
revalida cada hop manualmente. Sem dependência nova — só stdlib.
"""

import html
import ipaddress
import logging
import re
import socket
import urllib.parse
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# ![alt](url "titulo opcional") — captura alt e url
_IMG_RE = re.compile(r'!\[(?P<alt>[^\]]*)\]\((?P<url>[^)\s]+)(?:\s+"[^"]*")?\)')

_TIMEOUT = 3                       # segundos por hop
_MAX_REDIRECTS = 5
_MAX_BODY = 25 * 1024 * 1024       # 25 MB por imagem
_UA = 'Mozilla/5.0 (compatible; md-converter/1.0)'
_REDIRECT_CODES = (301, 302, 303, 307, 308)


class UnsafeURL(Exception):
    """URL aponta (ou redireciona) pra alvo não-público / esquema proibido."""


class TooManyRedirects(Exception):
    pass


def _ip_is_blocked(ip_str):
    ip = ipaddress.ip_address(ip_str)
    return (ip.is_private or ip.is_loopback or ip.is_link_local or
            ip.is_reserved or ip.is_multicast or ip.is_unspecified)


def is_safe_url(url, _resolver=None):
    """True se for http/https e TODOS os IPs resolvidos forem públicos.

    _resolver: callable(host)->[ip_str] injetável pra teste. Default = getaddrinfo.
    """
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.hostname:
        return False
    try:
        if _resolver is not None:
            ips = _resolver(parts.hostname)
        else:
            ips = [info[4][0] for info in socket.getaddrinfo(parts.hostname, None)]
    except (socket.gaierror, ValueError):
        return False
    if not ips:
        return False
    for ip_str in ips:
        try:
            if _ip_is_blocked(ip_str):
                return False
        except ValueError:
            return False
    return True


# Opener que NÃO segue redirect automaticamente (revalidamos cada hop à mão).
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def _safe_open(url, method, range_probe=False):
    """Abre `url` validando SSRF a cada hop, sem auto-redirect. Devolve a resposta
    aberta (caller fecha). Levanta UnsafeURL / TooManyRedirects / erros de rede.

    ponytail: TOCTOU/DNS-rebinding residual entre resolver e conectar — alvo
    aceitável pra ferramenta interna; endurecer (pin de IP + Host header) se virar exposta.
    """
    current = url
    for _ in range(_MAX_REDIRECTS + 1):
        if not is_safe_url(current):
            raise UnsafeURL(current)
        headers = {'User-Agent': _UA}
        if range_probe:
            headers['Range'] = 'bytes=0-0'
        req = urllib.request.Request(current, method=method, headers=headers)
        loc = None
        try:
            resp = _opener.open(req, timeout=_TIMEOUT)
        except urllib.error.HTTPError as e:
            if e.code in _REDIRECT_CODES and e.headers.get('Location'):
                loc = e.headers.get('Location')
            else:
                raise
        else:
            if resp.status in _REDIRECT_CODES and resp.headers.get('Location'):
                loc = resp.headers.get('Location')
                resp.close()
            else:
                return resp
        current = urllib.parse.urljoin(current, loc)
    raise TooManyRedirects(url)


def _http_broken(url):
    """True se a URL não responder com sucesso OU for insegura (SSRF guard)."""
    try:
        try:
            resp = _safe_open(url, 'HEAD')
        except urllib.error.HTTPError as e:
            if e.code in (403, 405):  # host não gosta de HEAD — confirma com GET
                resp = _safe_open(url, 'GET', range_probe=True)
            else:
                raise
        status = resp.status
        resp.close()
        return status >= 400
    except (UnsafeURL, TooManyRedirects) as e:
        logger.warning(f"Imagem bloqueada (SSRF guard): {e}")
        return True
    except Exception as e:
        logger.info(f"Imagem inacessível ({url}): {e}")
        return True


def safe_url_fetcher(url):
    """url_fetcher pro WeasyPrint: imagens http(s) passam pelo guard de SSRF e têm
    o corpo limitado; data:/file:/etc. caem no fetcher padrão (fonts, logo, capa,
    SVG do Mermaid em data-URI)."""
    scheme = urllib.parse.urlsplit(url).scheme.lower()
    if scheme in ('http', 'https'):
        resp = _safe_open(url, 'GET')
        try:
            data = resp.read(_MAX_BODY + 1)
            ctype = resp.headers.get('Content-Type', '').split(';')[0].strip() or None
            final = resp.geturl()
        finally:
            resp.close()
        if len(data) > _MAX_BODY:
            raise UnsafeURL(f"imagem remota excede {_MAX_BODY} bytes: {url}")
        return {'string': data, 'mime_type': ctype, 'redirected_url': final}
    from weasyprint import default_url_fetcher
    return default_url_fetcher(url)


def _placeholder(url):
    safe = html.escape(url)
    return (
        '<div style="border:1px solid #ccc;background:#f7f7f7;border-radius:8px;'
        'padding:16px;color:#808080;font-size:9pt;text-align:center;margin:16px auto;">'
        '⚠ imagem indisponível<br>'
        f'<span style="font-size:8pt;word-break:break-all;">{safe}</span></div>'
    )


def check_and_placeholder_images(md_text, is_broken=None):
    """Substitui imagens remotas quebradas/inseguras por placeholder.

    Args:
        md_text: conteúdo markdown.
        is_broken: callable(url)->bool. Default = checagem HTTP real (com SSRF guard).

    Returns:
        (novo_texto, [urls_quebradas])
    """
    if is_broken is None:
        is_broken = _http_broken

    broken = []
    cache = {}  # ponytail: dedup por URL; sequencial. Paralelizar se doc tiver muitas imagens.

    def _sub(m):
        url = m.group('url')
        if not url.lower().startswith(('http://', 'https://')):
            return m.group(0)  # imagem local/data-uri: não checa
        if url not in cache:
            cache[url] = is_broken(url)
        if cache[url]:
            if url not in broken:
                broken.append(url)
            return _placeholder(url)
        return m.group(0)

    return _IMG_RE.sub(_sub, md_text), broken


if __name__ == '__main__':
    # SSRF guard (IPs literais não precisam de rede):
    assert is_safe_url('http://127.0.0.1/x') is False          # loopback
    assert is_safe_url('http://10.1.2.3/x') is False           # privado
    assert is_safe_url('http://192.168.0.1/x') is False        # privado
    assert is_safe_url('http://169.254.169.254/latest') is False  # link-local (metadata)
    assert is_safe_url('http://[::1]/x') is False              # loopback v6
    assert is_safe_url('http://0.0.0.0/x') is False            # unspecified
    assert is_safe_url('ftp://8.8.8.8/x') is False             # esquema proibido
    assert is_safe_url('http://8.8.8.8/x') is True             # público
    # host só com IPs internos é bloqueado mesmo via resolver injetado:
    assert is_safe_url('http://evil.example/x', _resolver=lambda h: ['127.0.0.1']) is False
    assert is_safe_url('http://cdn.example/x', _resolver=lambda h: ['93.184.216.34']) is True

    # Substituição com is_broken injetado (sem rede):
    src = (
        "# Doc\n\n"
        "![ok](https://example.com/a.png)\n\n"
        "![ruim](https://example.com/missing.png)\n\n"
        "![local](imgs/foto.png)\n\n"
        "![data](data:image/png;base64,AAAA)\n"
    )
    broken_set = {"https://example.com/missing.png"}
    out, broken = check_and_placeholder_images(src, is_broken=lambda u: u in broken_set)
    assert broken == ["https://example.com/missing.png"], broken
    assert "imagem indisponível" in out
    assert "https://example.com/missing.png" in out
    assert "![ok](https://example.com/a.png)" in out
    assert "![local](imgs/foto.png)" in out
    assert "![data](data:image/png;base64,AAAA)" in out
    assert "![ruim]" not in out
    print("OK — image_check self-check (incl. SSRF guard) passou")
