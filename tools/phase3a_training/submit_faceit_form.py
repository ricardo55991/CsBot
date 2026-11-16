"""Preenche e envia o formulario FACEIT Downloads API via Chrome DevTools Protocol.

Uso:
    python tools/phase3a_training/submit_faceit_form.py inspect
    python tools/phase3a_training/submit_faceit_form.py fill

Requer um Chrome ja lancado com:
    chrome.exe --remote-debugging-port=9222 \
        --user-data-dir="%LOCALAPPDATA%\\Google\\Chrome\\User Data" \
        --profile-directory="Default"

O perfil carrega a sessao Google do operador humano; o script nao le,
descriptografa nem persiste cookie algum.
"""

import asyncio
import json
import sys
import urllib.request

import websockets

FORM_URL = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSd-BQTLw_jpm18gChVssYSKsKzwWKxhgzeHRH4THMrl_ZCrdA/viewform"
)
CDP = "http://127.0.0.1:9222"

ANSWERS = {
    "full_name": "Ricardo Alexandre",
    "email": "ricardo.barros.jr@gmail.com",
    "faceit_nickname": "ShuutUp",
}


def http_json(path):
    with urllib.request.urlopen(CDP + path, timeout=10) as r:
        return json.loads(r.read().decode())


def pick_page_target():
    targets = http_json("/json/list")
    pages = [t for t in targets if t.get("type") == "page"]
    if not pages:
        raise RuntimeError("nenhuma aba de pagina encontrada no Chrome")
    return pages[0]


class Session:
    def __init__(self, ws):
        self.ws = ws
        self._id = 0

    async def call(self, method, params=None):
        self._id += 1
        mid = self._id
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    async def js(self, expression, await_promise=False):
        res = await self.call("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": await_promise,
        })
        return res.get("result", {}).get("value")


INSPECT_JS = r"""
(() => {
  const out = { url: location.href, title: document.title, fields: [] };
  const nodes = document.querySelectorAll('input, textarea, [role="radio"], [role="checkbox"]');
  nodes.forEach((n, i) => {
    let label = n.getAttribute('aria-label') || '';
    if (!label) {
      const l = n.closest('[data-item-id]');
      if (l) {
        const h = l.querySelector('[role="heading"], .M7eMe, .HoXoMd');
        if (h) label = h.innerText.trim().slice(0, 160);
      }
    }
    out.fields.push({
      i,
      tag: n.tagName,
      type: n.type || n.getAttribute('role') || '',
      aria: (n.getAttribute('aria-label') || '').slice(0, 120),
      label: label.replace(/\s+/g, ' ').slice(0, 160),
      name: n.name || '',
      value: (n.value || '').slice(0, 60),
    });
  });
  out.loginGate = /accounts\.google\.com|ServiceLogin/.test(location.href);
  out.bodyHead = document.body.innerText.slice(0, 400).replace(/\s+/g, ' ');
  return out;
})()
"""

FILL_JS_TEMPLATE = r"""
(() => {
  const A = __ANSWERS__;
  const log = [];

  function setNative(el, value) {
    const proto = el.tagName === 'TEXTAREA'
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    setter.call(el, value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('blur', { bubbles: true }));
  }

  function questionText(el) {
    const item = el.closest('[data-item-id]');
    if (!item) return '';
    const h = item.querySelector('[role="heading"], .M7eMe, .HoXoMd');
    return h ? h.innerText.trim() : '';
  }

  const textInputs = [...document.querySelectorAll('input[type="text"], input[type="email"], input:not([type]), textarea')]
      .filter(e => e.offsetParent !== null);

  const rules = [
    { key: 'email',  match: /e-?mail/i },
    { key: 'full_name', match: /full\s*name|nome/i },
    { key: 'faceit_nickname', match: /faceit.*(nick|account|id|name)|nickname/i },
  ];

  for (const el of textInputs) {
    const q = questionText(el) || el.getAttribute('aria-label') || '';
    for (const r of rules) {
      if (r.match.test(q) && !el.dataset.autofilled) {
        setNative(el, A[r.key]);
        el.dataset.autofilled = '1';
        log.push({ filled: r.key, into: q.slice(0, 90) });
        break;
      }
    }
  }

  return { log, remaining: textInputs.filter(e => !e.dataset.autofilled).map(e => ({
      q: (questionText(e) || e.getAttribute('aria-label') || '').slice(0, 120),
      type: e.type || '' })) };
})()
"""

SUBMIT_JS = r"""
(() => {
  const btns = [...document.querySelectorAll('[role="button"], button')];
  const submit = btns.find(b => /^submit$/i.test((b.innerText || '').trim()))
              || btns.find(b => /submit|enviar/i.test((b.getAttribute('aria-label') || '')));
  if (!submit) return { clicked: false, buttons: btns.map(b => (b.innerText || '').trim()).filter(Boolean).slice(0, 15) };
  submit.click();
  return { clicked: true, label: (submit.innerText || submit.getAttribute('aria-label') || '').trim() };
})()
"""


async def run(mode: str):
    target = pick_page_target()
    print(f"[cdp] alvo: {target['title'][:80]}")
    async with websockets.connect(target["webSocketDebuggerUrl"], max_size=8 * 1024 * 1024) as ws:
        s = Session(ws)
        await s.call("Page.enable")
        await s.call("Runtime.enable")

        if mode == "inspect":
            await s.call("Page.navigate", {"url": FORM_URL})
            await asyncio.sleep(6)
            info = await s.js(INSPECT_JS)
            print(json.dumps(info, indent=2, ensure_ascii=False)[:6000])
            return

        info = await s.js(INSPECT_JS)
        if info.get("loginGate"):
            print("[bloqueio] a pagina esta no login do Google; sessao ausente.")
            print(json.dumps(info, indent=2, ensure_ascii=False)[:1500])
            return

        js = FILL_JS_TEMPLATE.replace("__ANSWERS__", json.dumps(ANSWERS))
        res = await s.js(js)
        print("[preenchimento]", json.dumps(res, indent=2, ensure_ascii=False)[:4000])

        if mode == "fill":
            return

        if res["remaining"]:
            print("\n[atencao] campos nao preenchidos automaticamente:")
            for r in res["remaining"]:
                print("   -", r)
            print("\nNada foi enviado. Ajuste as regras de mapeamento antes de submeter.")
            return

        sub = await s.js(SUBMIT_JS)
        print("[submit]", json.dumps(sub, ensure_ascii=False))
        await asyncio.sleep(5)
        after = await s.js("({url: location.href, text: document.body.innerText.slice(0,500)})")
        print("[apos submit]", json.dumps(after, ensure_ascii=False)[:1200])


if __name__ == "__main__":
    asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else "inspect"))
