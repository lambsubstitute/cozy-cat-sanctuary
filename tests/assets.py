"""The page loads Tailwind and two Google fonts from CDNs. Layout tests need them.

route_assets(page) lets those load from the internet as normal and blocks every
other web request (such as the weather service), so runs stay repeatable.

To run offline, set LOCAL_TW_DIR to a folder where you've run
    npm install tailwindcss@3 @fontsource/press-start-2p @fontsource/vt323
and the CSS is built locally from index.html and the fonts served from there.
"""
import base64, json, os, subprocess

_local = None

def _build_local(html):
    global _local
    if _local is not None:
        return _local
    tw = os.environ["LOCAL_TW_DIR"]
    open(f"{tw}/in.css", "w").write("@tailwind base;\n@tailwind components;\n@tailwind utilities;\n")
    subprocess.run(["npx", "tailwindcss", "-i", f"{tw}/in.css", "-o", f"{tw}/out.css", "--content", html],
                   cwd=tw, check=True, capture_output=True)
    css = open(f"{tw}/out.css").read()
    inject = "(()=>{const s=document.createElement('style');s.textContent=" + json.dumps(css) + ";document.head.appendChild(s);})();"
    def font(name):
        path = f"{tw}/node_modules/@fontsource/{name}/files/{name}-latin-400-normal.woff2"
        return base64.b64encode(open(path, "rb").read()).decode()
    fonts = ("@font-face{font-family:'Press Start 2P';src:url(data:font/woff2;base64,%s) format('woff2');}"
             "@font-face{font-family:'VT323';src:url(data:font/woff2;base64,%s) format('woff2');}") % (font("press-start-2p"), font("vt323"))
    _local = (inject, fonts)
    return _local

def route_assets(page, html):
    local = _build_local(html) if os.environ.get("LOCAL_TW_DIR") else None
    def handler(route):
        u = route.request.url
        if "cdn.tailwindcss.com" in u:
            return route.fulfill(status=200, content_type="application/javascript", body=local[0]) if local else route.continue_()
        if "fonts.googleapis.com" in u or "fonts.gstatic.com" in u:
            return route.fulfill(status=200, content_type="text/css", body=local[1]) if local else route.continue_()
        if u.startswith("http"):
            return route.abort()
        return route.continue_()
    page.route("**/*", handler)
