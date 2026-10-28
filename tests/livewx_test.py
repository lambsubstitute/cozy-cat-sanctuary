import sys, json, base64, io
from PIL import Image
from playwright.sync_api import sync_playwright
html = sys.argv[1]
state = {'code': 61, 'temp': 11.4, 'cloud': 95, 'wind': 22, 'fail': False}
GEO = {"results": [{"id": 1, "name": "Glastonbury", "latitude": 51.1489, "longitude": -2.7142, "country": "United Kingdom", "admin1": "England"},
                   {"id": 2, "name": "Glastonbury", "latitude": 41.7123, "longitude": -72.6082, "country": "United States", "admin1": "Connecticut"}]}
def handler(route):
    u = route.request.url
    if 'geocoding-api.open-meteo.com' in u:
        return route.fulfill(status=200, content_type='application/json', body=json.dumps(GEO), headers={'Access-Control-Allow-Origin': '*'})
    if 'api.open-meteo.com' in u:
        if state['fail']: return route.abort()
        body = {"current": {"time": "2026-10-16T10:45", "temperature_2m": state['temp'], "weather_code": state['code'], "cloud_cover": state['cloud'], "wind_speed_10m": state['wind'], "is_day": 1},
                "daily": {"time": ["2026-10-16"], "sunrise": ["2026-10-16T07:41"], "sunset": ["2026-10-16T18:16"]}}
        return route.fulfill(status=200, content_type='application/json', body=json.dumps(body), headers={'Access-Control-Allow-Origin': '*'})
    if u.startswith('http'): return route.abort()
    return route.continue_()
SNAP = """() => { const c = roomCanvas; const o = document.createElement('canvas'); o.width = 640; o.height = 380;
  const g = o.getContext('2d'); g.imageSmoothingEnabled = false; g.drawImage(c, 0, 0, 640, 380); return o.toDataURL(); }"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1280, 'height': 900})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("**/*", handler)
    pg.add_init_script("window.__skipCreator = true;")
    pg.goto(f"file://{html}"); pg.wait_for_timeout(600)
    pg.click('#btnSettings'); pg.wait_for_timeout(100)
    pg.click('text=The real weather where I live'); pg.wait_for_timeout(100)
    print('need place:', pg.inner_text('#wxSection').split('\n')[-1])
    pg.fill('#wxPlace', 'Glastonbury'); pg.click('text=Find'); pg.wait_for_timeout(400)
    print('results:', pg.evaluate("liveWx.results.map(r => r.label)"))
    pg.click('text=Glastonbury, England, United Kingdom'); pg.wait_for_timeout(800)
    print('status:', pg.evaluate("[liveWx.status, wxSummary()]"))
    print('outside:', pg.evaluate("[outside.precip, outside.light, outside.cloud, outside.temp, outside.phase, document.getElementById('weatherLabel').textContent, document.getElementById('weatherIcon').textContent]"))
    shots = [pg.evaluate(SNAP)]
    for code, cloud, temp in [(45, 100, 6), (3, 100, 9), (0, 5, 14), (73, -1, -2), (95, 100, 18)]:
        state.update(code=code, cloud=cloud if cloud >= 0 else 0, temp=temp)
        pg.evaluate("void 0; liveWx.nextFetch = 0; 0;"); pg.wait_for_timeout(1500)
        print(code, pg.evaluate("[outside.precip, outside.storm, outside.fog, outside.cloud, document.getElementById('weatherLabel').textContent]"))
        shots.append(pg.evaluate(SNAP))
    pg.screenshot(path='wx_settings.png')
    # the service unreachable
    state['fail'] = True
    pg.evaluate("void 0; liveWx.nextFetch = 0; 0;"); pg.wait_for_timeout(1500)
    print('on failure:', pg.evaluate("[liveWx.status, liveWx.msg.slice(0, 60), outside.precip, !!liveWeatherNow()]"))
    print('saved:', pg.evaluate("JSON.parse(localStorage.getItem(WX_KEY)).place.label"))
    pg.reload(); pg.wait_for_timeout(800)
    print('after reload:', pg.evaluate("[liveWx.on, liveWx.place && liveWx.place.name, !!liveWeatherNow(), document.getElementById('weatherLabel').textContent]"))
    ims = [Image.open(io.BytesIO(base64.b64decode(s.split(',')[1]))) for s in shots]
    out = Image.new('RGB', (640 * 2, 380 * 3)); [out.paste(im, ((i % 2) * 640, (i // 2) * 380)) for i, im in enumerate(ims)]; out.save('wx_rooms.png')
    print(errs)
    b.close()
