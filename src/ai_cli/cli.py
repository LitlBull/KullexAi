from __future__ import annotations
import argparse, os, sys, time
from .config import load_config, CONFIG_PATH
from .prompts import build_prompt
from .redact import basic as redact_basic
from .stream import divider, tail_window, sha256_hex
from .providers import PROVIDERS

VERSION = "0.1.0"

def _add_flags(parser: argparse.ArgumentParser, cfg: dict) -> None:
    m = parser.add_mutually_exclusive_group()
    m.add_argument("-sum", "--summary", action="store_true", help="Summarize the input")
    m.add_argument("-sol", "--solutions", action="store_true", help="Suggest fixes and next steps")
    m.add_argument("-ser", "--search", action="store_true", help="Deepsearch: clusters + anomalies")
    m.add_argument("-scan", "--scan", action="store_true", help="Network scan analysis (nmap/masscan)")
    m.add_argument("-exp", "--explain", action="store_true", help="Explain terms in the input")  # Added

    parser.add_argument("-o", "--out", help="Write only the AI section to a file")
    parser.add_argument("-p", "--provider",
                        choices=sorted(PROVIDERS.keys()),
                        default=cfg.get("provider", "openai"))
    parser.add_argument("-m", "--model", default=cfg.get("model", "gpt-4o-mini"))
    parser.add_argument("-e", "--endpoint", default=cfg.get("endpoint", ""),
                        help="Override endpoint (e.g., local vLLM or gateway URL)")
    parser.add_argument("-L", "--limit", type=int, default=int(cfg.get("window_bytes", 128 * 1024)),
                        help="Max input bytes to keep from stdin (tail window)")
    parser.add_argument("-T", "--maxtok", type=int, default=int(cfg.get("max_tokens", 400)),
                        help="Max output tokens from the model")
    parser.add_argument("--stream", action="store_true", help="Stream AI output via SSE")
    parser.add_argument("-t", "--timeout", type=int, default=None, help="HTTP timeout (seconds)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Do not print AI section to stdout")
    parser.add_argument("--version", action="version", version=f"kull {VERSION}")

EXIT_NO_MODE = 1
EXIT_AI_FAIL = 2
EXIT_NO_INPUT = 3

def _pick_mode(args: argparse.Namespace) -> str:
    # If no mode selected:
    if not (args.summary or args.solutions or args.search or args.scan):
        # If interactive (no piped input), show help/exit; else default to summary
        if sys.stdin.isatty():
            return ""  # main() prints help
        args.summary = True
    if args.summary:
        return "sum"
    if args.solutions:
        return "sol"
    if args.search:
        return "ser"
    if args.scan:
        return "scan"
    if args.explain:
        return "exp"
    return "sum"    # Add 'if args.exp: return "exp"' if implementing exp mode. Note exp support requires adding an -exp flag

def main() -> None:
    cfg = load_config()

    ap = argparse.ArgumentParser(
        prog="kull",
        description="KullexAi: AI as a Unix filter (stdin → stdout + AI section). "
                    f"Config: {CONFIG_PATH}"
    )
    sub = ap.add_subparsers(dest="subcmd")

    # init subcommand (delegates to the wizard)
    initp = sub.add_parser("init", help="Interactive setup and config writer")
    _add_flags(ap, cfg)
    args = ap.parse_args()

    if args.subcmd == "init":
        from .kull_init import run_init
        run_init()
        return

    mode = _pick_mode(args)
    if not mode:
        ap.print_help()
        sys.exit(EXIT_NO_MODE)

    window = tail_window(args.limit)
    if not window:
        print("[kull] No input on stdin", file=sys.stderr)
        sys.exit(EXIT_NO_INPUT)

    text = window.decode("utf-8", errors="replace")
    if cfg.get("redact", "basic") == "basic":
        text = redact_basic(text)

    # Build the system prompt (username injection happens inside build_prompt if you added it)
    # If you implemented username handling in prompts: from .user import current_username
    # prompt = build_prompt(mode, current_username())
    prompt = build_prompt(mode, username=os.getlogin() or "user")

    # Visual divider before AI section (unless quiet/file-only)

    title = {"sum": "ai summary", "sol": "ai solutions", "ser": "ai deepsearch", "scan": "ai scan", "exp": "ai explain"}[mode]
    if not args.quiet:
        sys.stdout.write(divider(title))
        sys.stdout.flush()

    # Provider instance (endpoint override is optional)
    ProviderClass = PROVIDERS[args.provider]
    try:
        prov = ProviderClass(base_url=args.endpoint or None)
    except Exception as e:
        if not args.quiet:
            sys.stdout.write(f"AI init failed: {e}\n"); sys.stdout.flush()
        print(f"[kull] provider init failed: {e}", file=sys.stderr)
        sys.exit(EXIT_AI_FAIL)

    # Call AI
    start = time.time()
    ai_text = ""
    try:
        if args.stream:
            parts: list[str] = []
            for delta in prov.stream(prompt, text, args.model, args.maxtok, args.timeout):
                if not args.quiet:
                    sys.stdout.write(delta)
                parts.append(delta)
            ai_text = "".join(parts)
            if not ai_text.strip() and not args.quiet:
                print("AI output truncated or empty", file=sys.stderr)
        else:
            ai_text = prov.complete(prompt, text, args.model, args.maxtok, args.timeout)
            if not ai_text.strip() and not args.quiet:
                print("AI output truncated or empty", file=sys.stderr)
            if not args.quiet:
                sys.stdout.write(ai_text)
                sys.stdout.flush()
    except Exception as e:
        if not args.quiet:
            sys.stdout.write(f"AI failed: {e}\n")
            sys.stdout.flush()
        print(f"[kull] error: {e}", file=sys.stderr)
        sys.exit(EXIT_AI_FAIL)
    finally:
        elapsed = int((time.time() - start) * 1000)
        #print(f"[kull] provider={args.provider} model={args.model} mode={mode} "
        #    f"tokens<={args.maxtok} elapsed_ms={elapsed}", file=sys.stderr)


    # Optional file output

    if args.out:
        header = (f"# ai-section v1\n"
                  f"provider={args.provider} model={args.model} mode={mode} "
                  f"window_bytes={len(window)} sha256={sha256_hex(window)}\n"
                  f"tokens<={args.maxtok} elapsed_ms={elapsed}\n"
                  f"timestamp={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n---\n")
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(header); f.write(ai_text)
                if not ai_text.endswith("\n"):
                    f.write("\n")
        except Exception as e:
            if not args.quiet:
                print(f"[kull] failed to write {args.out}: {e}", file=sys.stderr)
    

if __name__ == "__main__":
    main()
