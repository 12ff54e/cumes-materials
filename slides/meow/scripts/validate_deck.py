#!/usr/bin/env python3
"""Preview every slide with Chrome DevTools and export the 16:9 PDF."""

import argparse
import base64
import json
from pathlib import Path
import re
import subprocess
import time

import requests
import websocket
from PIL import Image, ImageDraw

DECK = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrome", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--port", type=int, default=9229)
    parser.add_argument("--deck", type=Path, default=DECK,
                        help="Deck directory; defaults to this meow presentation")
    parser.add_argument("--pdf", type=Path, help="PDF output; defaults to DECK/DECKNAME.pdf")
    parser.add_argument("--report", type=Path, help="JSON report; defaults to DECK/data/validation.json")
    args = parser.parse_args()
    deck = args.deck.resolve()
    pdf_path = args.pdf or deck / f"{deck.name}.pdf"
    report_path = args.report or deck / "data/validation.json"
    scratch = args.scratch.resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    origin = f"http://localhost:{args.port}"
    log = (scratch / "chrome.log").open("w")
    browser = subprocess.Popen([
        str(args.chrome), "--headless", "--disable-gpu", "--no-sandbox", "--disable-extensions",
        f"--remote-debugging-port={args.port}", f"--remote-allow-origins={origin}",
        f"--user-data-dir={scratch / 'chrome-profile'}", "about:blank",
    ], stdout=log, stderr=subprocess.STDOUT)
    ws = None
    try:
        for _ in range(100):
            try:
                pages = [page for page in requests.get(origin + "/json", timeout=1).json()
                         if page.get("type") == "page"]
                if pages:
                    break
            except requests.RequestException:
                pass
            time.sleep(.1)
        else:
            raise RuntimeError("Chrome did not start")
        ws = websocket.create_connection(pages[0]["webSocketDebuggerUrl"], origin=origin, timeout=30)
        sequence, events = 0, []

        def cdp(method, params=None):
            nonlocal sequence
            sequence += 1
            ws.send(json.dumps({"id": sequence, "method": method, "params": params or {}}))
            while True:
                response = json.loads(ws.recv())
                if response.get("id") == sequence:
                    if "error" in response:
                        raise RuntimeError(response["error"])
                    return response.get("result", {})
                events.append(response)

        def js(expression):
            result = cdp("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
            if "exceptionDetails" in result:
                raise RuntimeError(result)
            return result["result"].get("value")

        def key(value, code=None):
            for kind in ("keyDown", "keyUp"):
                cdp("Input.dispatchKeyEvent", {"type": kind, "key": value, "code": code or value})

        cdp("Page.enable")
        cdp("Runtime.enable")
        cdp("Network.enable")
        cdp("Page.navigate", {"url": (deck / "index.html").as_uri()})
        for _ in range(100):
            if js("document.readyState==='complete' && !!document.querySelector('.overview') && document.querySelectorAll('.slide').length>0"):
                break
            time.sleep(.1)
        else:
            raise RuntimeError("Deck did not finish loading: " + str(js("location.href")))
        js("document.fonts.ready.then(()=>true)")
        js("Promise.all([...document.images].map(i=>i.complete?Promise.resolve():new Promise((r,j)=>{i.onload=r;i.onerror=j}))).then(()=>true)")
        js("document.head.insertAdjacentHTML('beforeend','<style>.slide{transition:none!important}</style>')")
        count = js("document.querySelectorAll('.slide').length")
        results = {"slides": count, "layouts": {}, "checks": {}}
        check = """(()=>{const s=document.querySelector('.slide.active'), c=s.querySelector('.content'),
          foot=s.querySelector('footer').getBoundingClientRect();
          const nodes=[...c.querySelectorAll('p,td,th,h3,.equation,.hero-number,.math-inline,img,pre')];
          return {title:s.dataset.title,contentOverflow:c.scrollHeight>c.clientHeight+2,
            overruns:nodes.filter(e=>{let r=e.getBoundingClientRect(),p=e.closest('.panel'),box=p&&p.getBoundingClientRect();return r.bottom>foot.top+2||r.right>innerWidth-10||r.left<0||(box&&(r.bottom>box.bottom+1||r.right>box.right+1))||(e.classList.contains('math-inline')&&e.scrollWidth>e.clientWidth+2)}).map(e=>e.dataset.tex||e.textContent.slice(0,100)||e.getAttribute('src')),
            mathErrors:s.querySelectorAll('.katex-error').length}})()"""
        for width, height in ((1600, 900), (1280, 720)):
            cdp("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})
            rows = []
            for number in range(1, count + 1):
                js(f"location.hash='#/{number}'")
                time.sleep(.035)
                row = js(check)
                row["slide"] = number
                rows.append(row)
                if width == 1600:
                    screenshot = cdp("Page.captureScreenshot", {"format": "png"})["data"]
                    (scratch / f"slide-{number:02d}.png").write_bytes(base64.b64decode(screenshot))
            results["layouts"][f"{width}x{height}"] = rows
        js("location.hash='#/1'")
        time.sleep(.04)
        key("ArrowRight")
        results["checks"]["next"] = js("location.hash==='#/2'")
        key("ArrowLeft")
        results["checks"]["previous"] = js("location.hash==='#/1'")
        key("o", "KeyO")
        results["checks"]["overview"] = js(f"document.querySelector('.overview').classList.contains('open') && document.querySelectorAll('.overview-card').length==={count}")
        key("Escape")
        key("n", "KeyN")
        results["checks"]["notes"] = js("document.querySelector('#notes-overlay').classList.contains('open') && document.querySelector('.notes-copy').textContent.length>20")
        key("Escape")
        note_slide = js("[...document.querySelectorAll('.slide')].findIndex(s=>s.querySelector('.speaker-notes .math-inline'))+1")
        if note_slide:
            js(f"location.hash='#/{note_slide}'")
            time.sleep(.04)
            key("n", "KeyN")
            results["checks"]["notes_math"] = js("document.querySelector('.notes-copy').innerHTML===document.querySelector('.slide.active .speaker-notes').innerHTML && !!document.querySelector('.notes-copy .katex')")
            key("Escape")
        key("?", "Slash")
        results["checks"]["help"] = js("document.querySelector('#help-overlay').classList.contains('open')")
        key("Escape")
        key("End")
        results["checks"]["end"] = js(f"location.hash==='#/{count}'")
        key("Home")
        results["checks"]["home"] = js("location.hash==='#/1'")
        results["checks"]["images_loaded"] = js("[...document.images].every(i=>i.complete && i.naturalWidth>0)")
        results["checks"]["metadata"] = js("[...document.querySelectorAll('.slide')].every(s=>s.dataset.title&&s.dataset.chapter&&s.dataset.summary)")
        results["checks"]["all_math_rendered"] = js("[...document.querySelectorAll('[data-tex]')].every(e=>e.querySelector('.katex')&&!e.querySelector('.katex-error'))")
        results["checks"]["math_case_preserved"] = js("[...document.querySelectorAll('.math-inline')].every(e=>getComputedStyle(e).textTransform==='none')")
        cdp("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True})
        results["checks"]["mobile_scroll"] = js("getComputedStyle(document.querySelector('.slide.active')).overflowY==='auto'")
        js("document.dispatchEvent(new TouchEvent('touchstart',{changedTouches:[new Touch({identifier:1,target:document.body,clientX:300,clientY:300})]})); document.dispatchEvent(new TouchEvent('touchend',{changedTouches:[new Touch({identifier:1,target:document.body,clientX:100,clientY:300})]}))")
        results["checks"]["swipe"] = js("location.hash==='#/2'")
        cdp("Emulation.setDeviceMetricsOverride", {"width": 1280, "height": 720, "deviceScaleFactor": 1, "mobile": False})
        cdp("Emulation.setEmulatedMedia", {"media": "print"})
        results["print"] = js("""[...document.querySelectorAll('.slide')].map((s,i)=>{let r=s.getBoundingClientRect(),f=s.querySelector('footer').getBoundingClientRect();return {slide:i+1,width:r.width,height:r.height,overruns:[...s.querySelectorAll('.content p,.content td,.content th,.content img,.content h3,.content .equation,.content .math-inline,.content pre')].filter(e=>{let b=e.getBoundingClientRect(),p=e.closest('.panel'),box=p&&p.getBoundingClientRect();return b.bottom>f.top+2||b.right>r.right||b.left<r.left||(box&&(b.bottom>box.bottom+1||b.right>box.right+1))||(e.classList.contains('math-inline')&&e.scrollWidth>e.clientWidth+2)}).map(e=>e.dataset.tex||e.textContent.slice(0,80)||e.getAttribute('src'))}})""")
        # Large vector decks can take longer to print. Read a stream instead of
        # making the browser serialize the entire PDF in one WebSocket message.
        ws.settimeout(120)
        stream = cdp("Page.printToPDF", {"printBackground": True, "preferCSSPageSize": True,
                     "transferMode": "ReturnAsStream", "marginTop": 0, "marginBottom": 0,
                     "marginLeft": 0, "marginRight": 0})["stream"]
        ws.settimeout(30)
        chunks = []
        while True:
            chunk = cdp("IO.read", {"handle": stream, "size": 1 << 20})
            chunks.append(base64.b64decode(chunk["data"]) if chunk.get("base64Encoded") else chunk["data"].encode())
            if chunk.get("eof"):
                break
        cdp("IO.close", {"handle": stream})
        pdf = b"".join(chunks)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(pdf)
        results["pdf_pages"] = len(re.findall(rb"/Type /Page\b", pdf))
        results["runtime_errors"] = [event for event in events if event.get("method") == "Runtime.exceptionThrown"]
        results["network_failures"] = [event for event in events if event.get("method") == "Network.loadingFailed"]
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(results, indent=2) + "\n")
        for group in range((count + 11) // 12):
            sheet = Image.new("RGB", (1200, 1000), (2, 10, 17))
            draw = ImageDraw.Draw(sheet)
            for offset in range(12):
                number = group * 12 + offset + 1
                if number > count:
                    break
                picture = Image.open(scratch / f"slide-{number:02d}.png")
                picture.thumbnail((390, 220))
                x, y = (offset % 3) * 400, (offset // 3) * 250
                sheet.paste(picture, (x, y))
                draw.text((x + 8, y + 223), str(number), fill="white")
            sheet.save(scratch / f"contact-{group+1}.png")
        issues = {size: [row for row in rows if row["contentOverflow"] or row["overruns"] or row["mathErrors"]]
                  for size, rows in results["layouts"].items()}
        print(json.dumps({"layout_issues": issues, "print_issues": [row for row in results["print"] if row["overruns"]],
                          "checks": results["checks"], "pdf_pages": results["pdf_pages"],
                          "runtime_errors": results["runtime_errors"], "network_failures": results["network_failures"]}, indent=2))
    finally:
        if ws:
            ws.close()
        browser.terminate()
        browser.wait(timeout=10)
        log.close()


if __name__ == "__main__":
    main()
