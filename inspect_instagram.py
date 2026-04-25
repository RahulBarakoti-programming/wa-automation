"""
Instagram Click Inspector
=========================
Injects a JavaScript listener into Instagram. Every element you click
prints its full selector details to the terminal AND appends them to
instagram_selectors.txt — ready to copy into automation code.

Usage:
    python inspect_instagram.py

Controls (in terminal):
    Enter     → re-inject the JS listener (if Instagram removed it after navigation)
    q + Enter → quit
"""

import os
import re
import time
import json
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_FILE = "instagram_selectors.txt"
USER_DATA_DIR = os.path.abspath("./User_Data/Instagram")

# ── Chrome version detection (reused from core.py) ───────────────────────────
def _detect_chrome_version():
    try:
        for cmd in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]:
            try:
                out = subprocess.check_output([cmd, "--version"], stderr=subprocess.DEVNULL).decode()
                match = re.search(r"(\d+)\.\d+\.\d+\.\d+", out)
                if match:
                    return int(match.group(1))
            except Exception:
                continue
    except Exception:
        pass
    return None

# ── JS injected into the page ─────────────────────────────────────────────────
# Builds a rich CSS selector for any clicked element and posts it to a
# hidden div that Python polls every 500 ms.
INJECT_JS = """
(function() {
    // Avoid double-injection
    if (document.getElementById('__ig_inspector_badge')) return 'already_active';

    // --- Helper: generate a robust CSS selector for an element ---
    function buildSelector(el) {
        var parts = [];
        var cur = el;
        for (var i = 0; i < 6 && cur && cur !== document.body; i++) {
            var seg = cur.tagName.toLowerCase();
            if (cur.id) {
                try { seg += '#' + CSS.escape(cur.id); } catch(e) { seg += '#' + cur.id; }
                parts.unshift(seg);
                break;
            }
            var attrList = [
                ['name','name'], ['aria-label','aria-label'],
                ['data-testid','data-testid'], ['role','role'],
                ['placeholder','placeholder'], ['type','type']
            ];
            var matched = false;
            for (var ai = 0; ai < attrList.length; ai++) {
                var attr = attrList[ai][0];
                var v = cur.getAttribute(attr);
                if (v) {
                    seg += '[' + attr + '="' + v.replace(/"/g, '\\\\"') + '"]';
                    matched = true;
                    break;
                }
            }
            if (!matched) {
                var href = cur.getAttribute('href');
                if (href) {
                    seg += '[href="' + href.replace(/"/g, '\\\\"') + '"]';
                } else if (cur.parentNode) {
                    var idx = Array.prototype.indexOf.call(cur.parentNode.children, cur) + 1;
                    if (idx > 0) seg += ':nth-child(' + idx + ')';
                }
            }
            parts.unshift(seg);
            cur = cur.parentElement;
        }
        return parts.join(' > ');
    }

    // --- Helper: collect all meaningful attributes ---
    function getAttrs(el) {
        var keep = [
            'id','name','type','role','aria-label','aria-placeholder',
            'data-testid','data-tab','data-icon','placeholder',
            'contenteditable','accept','href','title'
        ];
        var out = {};
        for (var ki = 0; ki < keep.length; ki++) {
            try {
                var val = el.getAttribute(keep[ki]);
                if (val !== null && val !== '') out[keep[ki]] = val;
            } catch(e) {}
        }
        out.tag = el.tagName.toLowerCase();
        try {
            var cls = (el.className || '').toString().trim();
            if (cls) out.classes = cls.slice(0, 120);
        } catch(e) {}
        try {
            var txt = (el.innerText || '').trim().slice(0, 80);
            if (txt) out.text = txt;
        } catch(e) {}
        return out;
    }

    // --- XPath builder (iterative - no recursion to avoid stack overflow) ---
    function getXPath(el) {
        var parts = [];
        var cur = el;
        for (var i = 0; i < 12 && cur && cur !== document.documentElement; i++) {
            if (cur.id) {
                parts.unshift('//*[@id="' + cur.id + '"]');
                return parts.join('/');
            }
            try {
                var siblings = [];
                var childNodes = cur.parentNode ? cur.parentNode.childNodes : [];
                for (var si = 0; si < childNodes.length; si++) {
                    if (childNodes[si].nodeName === cur.nodeName) siblings.push(childNodes[si]);
                }
                var idx2 = siblings.indexOf(cur) + 1;
                parts.unshift(cur.nodeName.toLowerCase() + '[' + idx2 + ']');
            } catch(e) {
                parts.unshift(cur.nodeName.toLowerCase());
            }
            cur = cur.parentElement;
        }
        return '//' + parts.join('/');
    }

    // --- Overlay badge ---
    var badge = document.createElement('div');
    badge.id = '__ig_inspector_badge';
    badge.style.cssText = [
        'position:fixed','bottom:16px','right:16px','z-index:2147483647',
        'background:rgba(15,15,25,0.95)','color:#00ff99','font-family:monospace',
        'font-size:11px','padding:12px 14px','border-radius:10px',
        'max-width:460px','word-break:break-all','pointer-events:none',
        'border:1px solid #00ff9944','box-shadow:0 4px 24px rgba(0,0,0,0.5)',
        'white-space:pre-wrap','line-height:1.5'
    ].join(';');
    badge.textContent = '[IG Inspector] Active -- click any element';
    document.body.appendChild(badge);

    // --- Click listener (wrapped in try-catch so errors never swallow events) ---
    document.addEventListener('click', function(e) {
        try {
            var el = e.target;
            var selector = buildSelector(el);
            var attrs    = getAttrs(el);
            var xpath    = getXPath(el);

            var entry = {
                ts:  new Date().toISOString(),
                url: window.location.href,
                selector: selector,
                attrs:    attrs,
                xpath:    xpath,
            };

            var itemDiv = document.createElement('div');
            itemDiv.className = '__ig_click_data_item';
            itemDiv.style.display = 'none';
            itemDiv.textContent = JSON.stringify(entry);
            document.body.appendChild(itemDiv);

            var lines = ['[Clicked]', 'CSS: ' + selector, 'Tag: ' + attrs.tag];
            if (attrs['aria-label'])  lines.push('aria-label: '  + attrs['aria-label']);
            if (attrs['name'])        lines.push('name: '        + attrs['name']);
            if (attrs['role'])        lines.push('role: '        + attrs['role']);
            if (attrs['placeholder']) lines.push('placeholder: ' + attrs['placeholder']);
            if (attrs['text'])        lines.push('text: '        + attrs['text']);
            badge.textContent = lines.join('\\n');

        } catch(err) {
            // Never let errors suppress event capture
            try {
                var errEntry = { error: String(err), url: window.location.href, ts: new Date().toISOString() };
                var errDiv = document.createElement('div');
                errDiv.className = '__ig_click_data_item';
                errDiv.style.display = 'none';
                errDiv.textContent = JSON.stringify(errEntry);
                document.body.appendChild(errDiv);
            } catch(e2) {}
        }
    }, true);  // capture phase

    return 'injected';
})();
"""

# ── Logging ───────────────────────────────────────────────────────────────────
SECTION_COLORS = {
    "url":      "\033[94m",   # blue
    "selector": "\033[92m",   # green
    "attrs":    "\033[93m",   # yellow
    "xpath":    "\033[96m",   # cyan
    "reset":    "\033[0m",
    "bold":     "\033[1m",
    "dim":      "\033[2m",
}
C = SECTION_COLORS

def log_entry(entry):
    # Handle error entries
    if "error" in entry:
        print(f"{C['attrs']}⚠ JS Error: {entry['error']}{C['reset']}")
        return

    ts    = entry.get("ts", "")
    url   = entry.get("url", "")
    sel   = entry.get("selector", "")
    attrs = entry.get("attrs", {})
    xpath = entry.get("xpath", "")

    print(f"\n{'─'*60}")
    print(f"{C['bold']}[{ts}]{C['reset']}")
    print(f"{C['dim']}URL:{C['reset']} {C['url']}{url}{C['reset']}")
    print(f"{C['bold']}CSS Selector:{C['reset']}")
    print(f"  {C['selector']}{sel}{C['reset']}")
    print(f"{C['bold']}XPath:{C['reset']}")
    print(f"  {C['xpath']}{xpath}{C['reset']}")
    print(f"{C['bold']}Attributes:{C['reset']}")
    for k, v in attrs.items():
        print(f"  {C['attrs']}{k}{C['reset']}: {v}")

    # Write to file
    try:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{'─'*60}\n")
            f.write(f"[{ts}] {url}\n")
            f.write(f"CSS:   {sel}\n")
            f.write(f"XPath: {xpath}\n")
            for k, v in attrs.items():
                f.write(f"  {k}: {v}\n")
        print(f"DEBUG: Successfully appended to {OUTPUT_FILE}")
    except Exception as e:
        print(f"DEBUG: Error writing to file: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    import sys
    import select

    # Init output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("Instagram Selector Inspector\n")
        f.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n")

    print("\n" + "="*60)
    print("  Instagram Click Inspector")
    print("="*60)
    print(f"  Results will be saved to: {OUTPUT_FILE}")
    print("  Controls (type in this terminal):")
    print("    Enter   → re-inject JS listener (useful after page navigation)")
    print("    q Enter → quit")
    print("="*60 + "\n")

    # Launch Chrome with persistent Instagram session
    os.makedirs(USER_DATA_DIR, exist_ok=True)

    # Clean up stale Chrome lock files left by previous Ctrl+C kills
    for lock_name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        lock_path = os.path.join(USER_DATA_DIR, lock_name)
        try:
            os.remove(lock_path)
            print(f"  [cleanup] Removed stale {lock_name}")
        except FileNotFoundError:
            pass

    chrome_ver = _detect_chrome_version()
    print(f"Detected Chrome version: {chrome_ver}")

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # NOTE: --disable-gpu removed — it prevents Chrome from creating a visible
    # window on GPU-enabled Linux (e.g. Pop!_OS), causing 'Browser window not found'
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")   # safer than driver.maximize_window()
    options.add_argument("--window-size=1440,900")

    driver = uc.Chrome(
        options=options,
        user_data_dir=USER_DATA_DIR,
        use_subprocess=True,
        version_main=chrome_ver,
    )
    # maximize_window() is redundant with --start-maximized but kept as fallback
    try:
        driver.maximize_window()
    except Exception:
        pass
    driver.get("https://www.instagram.com/accounts/login/")

    print("\n>>> A Chrome window has opened. Log in to Instagram there.")
    print(">>> The click tracker will auto-inject and stay active.")
    print(">>> Press Ctrl+C or type  q + Enter  here to quit.\n")

    # Determine if stdin is an interactive terminal
    stdin_is_tty = sys.stdin.isatty()

    def try_inject(verbose=False):
        """Inject (or re-inject) the JS listener. Returns True on fresh inject."""
        try:
            result = driver.execute_script(INJECT_JS)
            if result == 'already_active':
                if verbose:
                    print("\u2139\ufe0f  Listener already active on this page.")
                return False   # already in, nothing to do
            print("\u2705 Click listener injected \u2014 click elements in the browser.")
            return True
        except Exception as e:
            if verbose:
                print(f"\u26a0\ufe0f  Inject failed: {e}")
            return False

    last_url = ""

    # Wait for page to be interactive before first inject
    print("\u23f3 Waiting for page to load...")
    for attempt in range(8):
        time.sleep(1.5)
        try:
            state = driver.execute_script("return document.readyState")
            if state == "complete":
                break
        except Exception:
            pass

    if not try_inject(verbose=True):
        # Retry once more after a short delay
        time.sleep(2)
        try_inject(verbose=True)

    try:
        while True:
            # ── 1. POLL clicks FIRST (before any sleep/navigation check) ─────
            try:
                items = driver.find_elements(By.CLASS_NAME, "__ig_click_data_item")
                for item in items:
                    raw = item.get_attribute("textContent")
                    if raw:
                        try:
                            entry = json.loads(raw)
                            log_entry(entry)
                        except Exception:
                            pass
                    # Remove the element so it doesn't get read again
                    driver.execute_script("arguments[0].remove();", item)
            except Exception:
                pass  # page mid-navigation or element stale — skip silently

            # ── 2. Check keyboard input (non-blocking) ───────────────────────
            if stdin_is_tty:
                ready, _, _ = select.select([sys.stdin], [], [], 0)
                if ready:
                    line = sys.stdin.readline().strip()
                    if line.lower() == 'q':
                        print("\n👋 Quitting...")
                        break
                    else:
                        try_inject(verbose=True)

            # ── 3. Auto re-inject only on TRUE page navigation ───────────────
            try:
                current_url = driver.current_url
                if current_url != last_url:
                    last_url = current_url
                    # Drain any remaining clicks from old page before sleeping
                    try:
                        raw2 = driver.execute_script(POLL_JS)
                        if raw2:
                            for entry in json.loads(raw2):
                                log_entry(entry)
                    except Exception:
                        pass
                    time.sleep(1.2)   # let new page settle
                    injected = try_inject()
                    if not injected:
                        pass  # already active on this context
            except Exception:
                pass

            time.sleep(0.25)

    except KeyboardInterrupt:
        print("\n👋 Interrupted — quitting.")

    try:
        driver.quit()
    except Exception:
        pass

    print(f"\n✅ Done. All selectors saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
