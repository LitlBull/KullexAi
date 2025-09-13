import sys, hashlib

_GRAY = "\x1b[90m"
_RESET = "\x1b[0m"

def is_tty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False

def divider(title: str) -> str:
    if is_tty():
        return f"\n\n{_GRAY}──────────────────── {title} ────────────────────{_RESET}\n"
    return f"\n\n{title}\n" + ("-" * len(title)) + "\n"

def tail_window(limit: int) -> bytes:
    window = bytearray()
    read1 = getattr(sys.stdin.buffer, "read1", sys.stdin.buffer.read)
    while True:
        chunk = read1(8192)
        if not chunk:
            break
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()
        window += chunk
        if len(window) > limit:
            window = window[-limit:]
    return bytes(window)

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def iter_sse_lines(resp):  # requests.Response(stream=True)
    buf = []
    for raw in resp.iter_lines(decode_unicode=True):
        if raw is None:
            continue
        if raw == "":
            if not buf:
                continue
            event = {"event": None, "data": "", "id": None}
            for line in buf:
                if line.startswith("data:"):
                    event["data"] += line[5:].lstrip() + "\n"
                elif line.startswith("event:"):
                    event["event"] = line[6:].lstrip()
                elif line.startswith("id:"):
                    event["id"] = line[3:].lstrip()
            event["data"] = event["data"].rstrip("\n")
            yield event
            buf = []
        else:
            buf.append(raw)
    if buf:
        event = {"event": None, "data": "", "id": None}
        for line in buf:
            if line.startswith("data:"):
                event["data"] += line[5:].lstrip() + "\n"
            elif line.startswith("event:"):
                event["event"] = line[6:].lstrip()
            elif line.startswith("id:"):
                event["id"] = line[3:].lstrip()
        event["data"] = event["data"].rstrip("\n")
        yield event