#!/usr/bin/env python3
"""A seeded random click-through of a prototype page. Python 3, no dependencies, headless Chrome.

  python3 stress.py <page.html> [--seeds 1-24] [--steps 200] [--device phone|laptop|both]
                    [--mode plain|framed|hosted|all] [--timing burst|settled|both] [--out <dir>]
  python3 stress.py <page.html> --seed 17 --steps 200 --device phone --mode framed --timing settled

One line per run, a JSON file per run, the replay command on every failure, exit 1 on any failure.
reference/stress.md says what each failure means. Nothing is written outside the out folder.
"""
from __future__ import annotations

import argparse, base64, hashlib, json, os, queue, random, re, shutil, socket, struct, subprocess, sys, tempfile, threading, time, urllib.request

CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
PHONE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
SIZES = {"laptop": (1400, 950), "phone": (390, 844)}
MAX_FAILURES = 8

# ---------------------------------------------------------------------------------------------
# What runs inside the page. Installed before the page's own scripts, in every frame.
# ---------------------------------------------------------------------------------------------
PAGE_LIB = r'''
(() => {
  const C = __CFG__;
  if (C.mode === "framed" && window.top === window) return;
  const rig = () => { try { return JSON.parse(window.name || "{}"); } catch (e) { return {}; } };
  if (rig().run !== C.run) { try { localStorage.clear(); } catch (e) {} window.name = JSON.stringify({ run: C.run }); }

  const $ = (q, r = document) => r.querySelector(q), $$ = (q, r = document) => Array.from(r.querySelectorAll(q));
  const CTRL = "[data-to],[data-back],[data-close],[data-tab],[data-toggle],[data-root],[data-toast]";
  const seen = (el) => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== "hidden";
  const screens = () => $$("#pt-canvas .screen.is-on:not(.pt-before)");
  const overlays = () => $$("#pt-canvas .overlay.is-on");
  const beforeNode = () => $("#pt-canvas .screen.pt-before.is-on");
  const scroller = (s) => (s && s.querySelector("[data-scroll]")) || s;
  const layer = () => overlays()[0] || beforeNode() || screens()[0] || null;
  const dev = () => { const d = $("#pt-device"); return d ? d.dataset.dev : null; };

  function hash(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(36); }
  // What the person can read on a layer, with pins left out so notes never count as a content change.
  function readable(el) {
    if (!el) return "";
    const pins = $$(".pt-pin", el); pins.forEach((p) => { p.style.display = "none"; });
    const t = (el.innerText || "").replace(/\s+/g, " ").trim();
    pins.forEach((p) => { p.style.display = ""; });
    return t;
  }

  // An independent model of where a stack of ids should land, read from the DOM's own attributes.
  const nodes = () => $$("#pt-canvas .screen:not(.pt-before), #pt-canvas .overlay");
  const find = (id, d) => nodes().find((n) => n.dataset.id === id && n.dataset.device === d);
  const other = (d) => (d === "phone" ? "laptop" : "phone");
  const roleNow = () => { const s = $('#pt-role'); return s ? s.value : null; };
  const allowed = (el) => !el.dataset.roles || el.dataset.roles.split("|").includes(roleNow());
  function place(id, d, n = 0) {
    const el = find(id, d);
    if (el && allowed(el)) return el.classList.contains("overlay") ? { overlay: el, over: el.dataset.over || null } : { screen: el };
    const twin = el || find(id, other(d));
    return twin && twin.dataset.alt && n < 4 ? place(twin.dataset.alt, d, n + 1) : null;
  }
  const firstId = () => { const all = nodes(); return (all.find((n) => "start" in n.dataset) || all[0]).dataset.id; };
  function roleStart() {
    const r = $(`#roles [data-role="${roleNow()}"]`);
    return (r && r.dataset.start) || firstId();
  }

  const S = window.__S = {
    t: null, ctrls: [],
    ready() { return !!$("#pt-canvas .screen.is-on") && !!$("#pt-proto"); },
    styled() { const el = $("#pt-canvas .screen.is-on [class*=flex]") || $("#pt-canvas .screen.is-on"); return !!el && document.readyState === "complete"; },
    page() { const b = $('.pt-top [data-page][aria-pressed="true"]'); return b ? b.dataset.page : null; },
    state() {
      const sc = screens(), ov = overlays(), top = ov[0] || sc[0], b = beforeNode();
      const box = (n) => { if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; };
      const text = readable(top);
      const opts = {}; $$(".pt-dcard[data-group]").forEach((c) => { const w = $$(".pt-dopt", c).find((x) => { const a = $(".pt-dshowing", x); return a && !a.hidden; }); if (w) opts[c.dataset.group] = w.dataset.choice; });
      return {
        screen: sc[0] ? sc[0].dataset.id : null, screens: sc.length, overlay: ov[0] ? ov[0].dataset.id : null, overlays: ov.length,
        dev: dev(), scroll: sc[0] ? Math.round(scroller(sc[0]).scrollTop) : 0, maxScroll: sc[0] ? Math.round(scroller(sc[0]).scrollHeight - scroller(sc[0]).clientHeight) : 0,
        fp: hash(text), textLen: text.length, screenBox: box(sc[0]), overlayBox: box(ov[0]), fills: !sc[0] || (sc[0].offsetWidth === $("#pt-canvas").clientWidth && sc[0].offsetHeight === $("#pt-canvas").clientHeight), before: !!b, page: S.page(), role: roleNow(), opts,
        side: !!$("#pt-side") && !$("#pt-side").hidden, active: (document.activeElement && document.activeElement.tagName) || "",
      };
    },
    controls() {
      const L = layer(); S.ctrls = L ? $$(CTRL, L).filter(seen) : [];
      return S.ctrls.map((el, i) => { const d = el.dataset; return { i, to: d.to || null, back: "back" in d, close: "close" in d, tab: d.tab || null, toggle: d.toggle || null, root: d.root || null, toast: d.toast || null, replace: "replace" in d, label: (el.textContent || "").trim().slice(0, 30) }; });
    },
    useCtrl(i) { S.t = S.ctrls[i]; return !!S.t; },
    use(sel, n = 0) { const list = $$(sel).filter(seen); S.t = list[n] || null; return { found: !!S.t, count: list.length }; },
    count(sel) { return $$(sel).filter(seen).length; },
    // Where a real finger or mouse would land, and whether the target is really what's on top there.
    aim() {
      const el = S.t; if (!el) return null;
      const look = () => {
        const r = el.getClientRects()[0]; if (!r) return null;
        const x = r.left + r.width / 2, y = r.top + r.height / 2;
        const inView = x >= 0 && y >= 0 && x < innerWidth && y < innerHeight;
        const hit = inView ? document.elementFromPoint(x, y) : null;
        const near = navigator.maxTouchPoints > 0 && !el.closest(".pt-pin") && $$(".pt-pin").some((p) => { const q = p.getBoundingClientRect(); return q.width && x > q.left - 12 && x < q.right + 12 && y > q.top - 12 && y < q.bottom + 12; });
        if (near) return { x, y, ok: false, by: ".pt-pin (touch moves the tap onto it)" };
        const ok = !!hit && (hit === el || el.contains(hit) || el.closest("label") === hit);
        return { x, y, ok, by: ok || !hit ? null : (hit.id ? "#" + hit.id : hit.className ? "." + String(hit.className).split(/\s+/)[0] : hit.tagName) };
      };
      el.scrollIntoView({ block: "nearest", inline: "nearest" });
      let a = look();
      if (a && !a.ok) { el.scrollIntoView({ block: "center", inline: "nearest" }); a = look(); } // a sticky bar can sit over the nearest spot
      return a;
    },
    click() { if (S.t) S.t.click(); },
    spot(rx, ry) {
      const L = layer(); if (!L) return null;
      const r = L.getBoundingClientRect();
      return { x: Math.min(innerWidth - 2, Math.max(2, r.left + r.width * rx)), y: Math.min(innerHeight - 2, Math.max(2, r.top + r.height * ry)) };
    },
    clickAt(x, y) { const el = document.elementFromPoint(x, y); if (el) el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, clientX: x, clientY: y, view: window })); return !!el; },
    contextAt(x, y) { const el = document.elementFromPoint(x, y); if (el) el.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: x, clientY: y, view: window })); return !!el; },
    // Press-and-hold and drag with a finger, as pointer events. Chrome's own long-press has no menu to open when headless and stalls.
    async pointer(x, y, dx, dy, hold) {
      const el = document.elementFromPoint(x, y); if (!el) return false;
      const ev = (t, cx, cy, on) => on.dispatchEvent(new PointerEvent(t, { bubbles: true, cancelable: true, clientX: cx, clientY: cy, pointerId: 7, pointerType: "touch", isPrimary: true, button: t === "pointermove" ? -1 : 0, buttons: t === "pointerup" ? 0 : 1, view: window }));
      ev("pointerdown", x, y, el);
      if (hold) await new Promise((r) => setTimeout(r, hold));
      if (dx || dy) { ev("pointermove", x + dx / 2, y + dy / 2, el); ev("pointermove", x + dx, y + dy, el); }
      ev("pointerup", x + dx, y + dy, el);
      return true;
    },
    key(k) { (document.activeElement || document.body).dispatchEvent(new KeyboardEvent("keydown", { key: k, bubbles: true })); },
    type(text) { const t = $("#pt-note-text"); if (!t) return false; t.value = text; t.dispatchEvent(new Event("input", { bubbles: true })); return true; },
    selects() { return $$("#pt-role").filter((s) => s.tagName === "SELECT").map((s) => ({ group: s.dataset.group, value: s.value, options: Array.from(s.options).map((o) => o.value) })); },
    setSelect(group, value) { const s = $(`select[data-group="${group}"]`); if (!s) return false; s.value = value; s.dispatchEvent(new Event("change", { bubbles: true })); return true; },
    decisionDevice(key) { const d = $(`.decision[data-key="${key}"]`); return d ? d.dataset.device || null : null; },
    devices() { const b = $$("#pt-devs [data-dev]"); return $("#pt-devs") && !$("#pt-devs").hidden ? b.map((x) => x.dataset.dev) : []; },
    roleStart, roleNow, exists: (id) => nodes().some((n) => n.dataset.id === id),
    resolves: (id) => !!place(id, dev()),
    isOverlay: (id) => { const p = place(id, dev()); return !!(p && p.overlay); },
    // The stack after the page drops what this view lacks, and where it should land. Mirrors what a person should see.
    expect(ids) {
      const d = dev(), st = ids.slice();
      while (st.length > 1 && !place(st[st.length - 1], d)) st.pop();
      let screen = null, overlay = null;
      for (let i = st.length - 1; i >= 0 && !screen; i--) {
        const p = place(st[i], d);
        if (!p) continue;
        if (p.overlay) {
          if (!overlay && i === st.length - 1) overlay = p.overlay;
          if (p.over) { const q = place(p.over, d); if (q && q.screen) screen = q.screen; }
        } else screen = p.screen;
      }
      screen = screen || find(roleStart(), d) || find(firstId(), d);
      return { ids: st, screen: screen ? screen.dataset.id : null, overlay: overlay ? overlay.dataset.id : null };
    },
    scrollTo(frac) { const s = scroller(screens()[0]); if (!s) return 0; s.scrollTop = Math.floor((s.scrollHeight - s.clientHeight) * frac); return Math.round(s.scrollTop); },
    links(where) {
      const root = where === "info" ? $("#pt-info") : $("#pt-reqs");
      S.linkEls = root ? $$("[data-open], .pt-try", root).filter(seen) : [];
      return S.linkEls.map((el, i) => {
        const dec = el.closest(".decision"), isTry = el.classList.contains("pt-try") && !el.dataset.open;
        const path = (isTry ? (dec.dataset.path || roleStart()) : el.dataset.open).split(/\s+/).filter(Boolean);
        return { i, path, device: (isTry ? dec.dataset.device : el.dataset.device) || null, option: isTry };
      });
    },
    useLink(i) { S.t = S.linkEls[i] || null; return !!S.t; },
    news() {
      const pop = $("#pt-new-pop"); const ch = JSON.parse(($("#pt-changes") || {}).textContent || "{}");
      const items = (ch.history || []).flatMap((r) => [...(r.added || []), ...(r.changed || [])]);
      S.newsEls = pop ? $$("button", pop).filter(seen) : [];
      return S.newsEls.map((b, i) => { const small = $("small", b), name = b.firstChild ? b.firstChild.textContent : ""; const words = small ? small.textContent : ""; const d = words.startsWith("Laptop") ? "laptop" : "phone"; const x = items.find((y) => y.name === name && y.device === d); return { i, path: x ? (x.path || [x.id]) : null, device: d }; });
    },
    useNews(i) { S.t = S.newsEls[i] || null; return !!S.t; },
    pins() {
      const L = overlays()[0] || screens()[0];
      return $$(".pt-pin:not(.pending)", document).map((p) => {
        const owner = L && L.contains(p), host = p.parentElement, r = p.getBoundingClientRect();
        const left = parseFloat(p.style.left) || 0, top = parseFloat(p.style.top) || 0;
        return { key: p.dataset.pinkey || null, owner, inside: !!host && left >= 0 && top >= 0 && left <= host.scrollWidth + 1 && top <= host.scrollHeight + 1, left, top, shown: r.width > 0 };
      });
    },
    pending() { return !!$(".pt-pin.pending"); },
    noteTexts() { return $$("#pt-list .pt-card p").map((p) => p.textContent); },
    // Status must never be colour alone: anything showing a state also needs words, a labelled icon or a title.
    colourOnly() {
      const bad = [];
      const q = "[aria-pressed], .is-on, .pending, .hot, [data-state]";
      $$(q).filter((el) => !el.closest("#pt-src") && !el.closest(".screen, .overlay")).forEach((el) => {
        const named = (el.textContent || "").trim() || el.getAttribute("title") || el.getAttribute("aria-label") || $("[aria-label]", el) || $("[title]", el);
        if (!named) bad.push(el.id ? "#" + el.id : el.tagName.toLowerCase() + "." + String(el.className).split(/\s+/)[0]);
      });
      return bad.slice(0, 10);
    },
    // A page wider than the phone makes a real phone zoom the whole thing out to fit.
    tooWide() {
      if (document.documentElement.scrollWidth <= innerWidth + 1) return null;
      const out = $$("body *").filter((e) => e.getClientRects().length && !e.closest("#pt-canvas") && !e.closest("#pt-src") && e.getBoundingClientRect().right > innerWidth + 1)
        .map((e) => (e.id ? "#" + e.id : e.tagName.toLowerCase() + "." + String(e.className).split(/\s+/)[0]) + " to " + Math.round(e.getBoundingClientRect().right) + "px");
      return { width: document.documentElement.scrollWidth, phone: innerWidth, by: out.slice(0, 6) };
    },
    deadLinks() {
      const bad = new Set();
      const check = (id) => { if (id && !S.exists(id)) bad.add(id); };
      $$("[data-to]").forEach((el) => { if (!el.closest(".pt-before")) check(el.dataset.to); });
      $$("[data-root]").forEach((el) => { if (!el.closest(".pt-before")) check(el.dataset.root); });
      $$("[data-open]").forEach((el) => el.dataset.open.split(/\s+/).filter(Boolean).forEach(check));
      return Array.from(bad).slice(0, 10);
    },
    async settle() {
      const raf = () => new Promise((r) => { requestAnimationFrame(r); setTimeout(r, 100); }), t0 = performance.now();
      while (performance.now() - t0 < 250) {
        const running = document.getAnimations().filter((a) => a.playState === "running");
        if (!running.length) break;
        await raf();
      }
      await raf(); await raf();
      return true;
    },
    // Answers that were held back: the database stub replies when told to, so a seed always replays the same.
    held: [],
    flush() { const n = S.held.length; S.held.splice(0).forEach((f) => f()); return n; },
    seeded: false,
  };

  if (!C.hosted) return;

  // A stand-in for the artifact runtime: database answers arrive late, with notes and choices already there.
  const firstDoc = () => { const n = nodes()[0] || {}; return n.dataset || {}; };
  const stored = () => rig().data || null;
  const data = stored() || { feedback: {}, notes: {}, n: 0, seeded: false };
  const save = () => { window.name = JSON.stringify({ run: C.run, data }); };
  const listeners = [];
  function seedOnce() {
    if (data.seeded) return;
    data.seeded = true; S.seeded = true;
    const f = firstDoc(), id = firstId(), key = ($(".decision[data-key]") || { dataset: {} }).dataset.key, choice = ($(".decision[data-key] .opt") || { dataset: {} }).dataset.choice;
    const base = { screen: id, name: f.name || id, device: f.device, path: [id], role: null, options: {}, rev: 1, at: "2026-01-01T09:00:00.000Z" };
    data.feedback.seed1 = { ...base, kind: "change", text: "Seeded pinned note", pin: { s: 0, x: 40, y: 60, label: "seeded" }, author: "u1" };
    data.feedback.seed2 = { ...base, kind: "question", text: "Seeded note from someone else", pin: null, author: "u2", at: "2026-01-01T09:01:00.000Z" };
    if (key) data.notes[key] = { section: key, choice: choice || "" };
    save();
  }
  const snap = (c) => ({ docs: Object.entries(data[c] || {}).map(([id, d]) => ({ id, data: () => d })) });
  const later = (fn) => new Promise((res, rej) => S.held.push(() => { try { res(fn()); } catch (e) { rej(e); } }));
  const tell = () => listeners.forEach((l) => S.held.push(() => l.cb(snap(l.c))));
  const docAt = (c, id) => ({
    get: () => later(() => ({ id, exists: !!(data[c] || {})[id], data: () => data[c][id] })),
    set: (d) => later(() => { data[c] = data[c] || {}; data[c][id] = d; save(); tell(); }),
    update: (d) => later(() => { data[c][id] = { ...(data[c][id] || {}), ...d }; save(); tell(); }),
    delete: () => later(() => { delete data[c][id]; save(); tell(); }),
  });
  const db = {
    collection: (c) => ({
      get: () => later(() => { seedOnce(); return snap(c); }),
      add: (d) => later(() => { const id = "d" + (++data.n); data[c][id] = d; save(); tell(); return { id }; }),
      doc: (id) => docAt(c, id),
      onSnapshot: (cb) => { const l = { c, cb }; listeners.push(l); S.held.push(() => { seedOnce(); cb(snap(c)); }); return () => listeners.splice(listeners.indexOf(l), 1); },
    }),
    doc: (path) => { const [c, id] = path.split("/"); return docAt(c, id); },
  };
  const user = { id: async () => "u1", profiles: async (ids) => Object.fromEntries(ids.map((i) => [i, { name: "Sam Rivera" }])) };
  window.claude = { use: (n) => later(() => (n === "db" ? db : n === "user" ? user : null)) };
})();
'''

# The wrapper that plays the site's side of the bridge, with the sandbox the site will use (D16).
FRAME_HTML = r'''<!doctype html><html><head><meta charset="utf-8"><title>stress frame</title>
<style>html,body{margin:0;height:100%}iframe{border:0;width:100%;height:100%;display:block}</style></head><body>
<iframe id="f" sandbox="allow-scripts" src="__SRC__"></iframe>
<script>
(() => {
  const f = document.getElementById("f"), list = [], choices = {};
  const F = window.__frame = { messages: 0, last: null, feedback: null, notes: list, choices,
    send(m) { f.contentWindow.postMessage(m, "*"); },
    goto(key) { F.send({ type: "wireframes-goto", key }); },
    askFeedback() { F.feedback = null; F.send({ type: "wireframes-feedback" }); },
  };
  const state = () => F.send({ type: "wireframes-state", me: { id: "u1", name: "Sam Rivera" }, notes: list.slice(), choices: { ...choices }, pdf: null });
  f.addEventListener("load", state);
  addEventListener("message", (e) => {
    if (e.source !== f.contentWindow) return;
    const m = e.data || {}; F.messages++;
    if (m.type === "wireframes") F.last = m;
    if (m.type === "wireframes-feedback") F.feedback = m;
    if (m.type === "wireframes-note") { list.push(m.note || m); state(); }
    if (m.type === "wireframes-choice") { choices[m.key] = m.choice; state(); }
  });
})();
</script></body></html>
'''


# ---------------------------------------------------------------------------------------------
# Chrome, over its debugging port. A small WebSocket client keeps this free of dependencies.
# ---------------------------------------------------------------------------------------------
class HarnessError(Exception):
    """The test rig failed, not the page."""


class Socket:
    def __init__(self, url: str):
        m = re.match(r"ws://([^:/]+):(\d+)(/.*)", url)
        self.s = socket.create_connection((m.group(1), int(m.group(2))), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET {m.group(3)} HTTP/1.1\r\nHost: {m.group(1)}:{m.group(2)}\r\nUpgrade: websocket\r\n"
                        f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.s.recv(4096)
            if not chunk:
                raise HarnessError("Chrome closed the connection during the handshake")
            head += chunk
        self.buf = head.split(b"\r\n\r\n", 1)[1]

    def _read(self, n: int) -> bytes:
        while len(self.buf) < n:
            chunk = self.s.recv(1 << 16)
            if not chunk:
                raise HarnessError("Chrome closed the connection")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def send(self, text: str):
        data = text.encode()
        head = bytearray([0x81])
        if len(data) < 126:
            head.append(0x80 | len(data))
        elif len(data) < 65536:
            head.append(0x80 | 126); head += struct.pack(">H", len(data))
        else:
            head.append(0x80 | 127); head += struct.pack(">Q", len(data))
        mask = os.urandom(4)
        head += mask
        n = len(data)
        pad = (mask * (n // 4 + 1))[:n]
        self.s.sendall(bytes(head) + (int.from_bytes(data, "big") ^ int.from_bytes(pad, "big")).to_bytes(n, "big"))

    def recv(self) -> str:
        parts = b""
        while True:
            b0, b1 = self._read(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            payload = self._read(n)
            op = b0 & 0x0F
            if op == 8:
                raise HarnessError("Chrome closed the connection")
            if op == 9:
                continue
            parts += payload
            if b0 & 0x80:
                return parts.decode("utf-8", "replace")

    def close(self):
        try:
            self.s.close()
        except OSError:
            pass


class Chrome:
    """One headless Chrome with one tab. Each worker has its own, so file:// storage never mixes."""

    def __init__(self, binary: str):
        self.dir = tempfile.mkdtemp(prefix="stress-chrome-")
        self.proc = subprocess.Popen(
            [binary, "--headless=new", "--disable-gpu", "--remote-debugging-port=0", f"--user-data-dir={self.dir}",
             "--no-first-run", "--no-default-browser-check", "--disable-background-timer-throttling",
             "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows",
             "--disable-features=Translate,BackForwardCache,IsolateSandboxedIframes", "--disable-site-isolation-trials",
             "--window-size=1400,950", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        port_file = os.path.join(self.dir, "DevToolsActivePort")
        for _ in range(300):
            if os.path.exists(port_file) and os.path.getsize(port_file):
                break
            time.sleep(0.05)
        else:
            self.close()
            raise HarnessError("Chrome did not start")
        port = open(port_file).read().split()[0]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        tabs = json.load(opener.open(f"http://127.0.0.1:{port}/json", timeout=20))
        page = next(t for t in tabs if t["type"] == "page")
        self.ws = Socket(page["webSocketDebuggerUrl"])
        self.id = 0
        self.contexts: dict[int, dict] = {}
        self.errors: list[str] = []
        self.loaded = 0
        self.crashed = False
        self.dialogs: list[str] = []
        self.pending_dialog = False
        for m in ("Page.enable", "Runtime.enable"):
            self.call(m)

    def _event(self, msg: dict):
        m, p = msg.get("method"), msg.get("params", {})
        if m == "Runtime.executionContextCreated":
            c = p["context"]; self.contexts[c["id"]] = c
        elif m == "Runtime.executionContextDestroyed":
            self.contexts.pop(p.get("executionContextId"), None)
        elif m == "Runtime.executionContextsCleared":
            self.contexts.clear()
        elif m == "Runtime.exceptionThrown":
            d = p["exceptionDetails"]
            text = (d.get("exception") or {}).get("description") or d.get("text") or "error"
            self.errors.append(str(text).split("\n")[0][:200])
        elif m == "Page.loadEventFired":
            self.loaded += 1
        elif m == "Inspector.targetCrashed":
            self.crashed = True
        elif m == "Page.javascriptDialogOpening":
            self.dialogs.append(f"{p.get('type')}: {p.get('message', '')[:80]}")
            self.pending_dialog = True

    def call(self, method: str, params: dict | None = None, timeout: float = 30):
        self.id += 1
        me = self.id
        self.ws.s.settimeout(timeout)
        self.ws.send(json.dumps({"id": me, "method": method, "params": params or {}}))
        while True:
            try:
                msg = json.loads(self.ws.recv())
            except socket.timeout:
                raise HarnessError(f"Chrome did not answer {method}")
            if msg.get("id") == me:
                if "error" in msg:
                    raise HarnessError(f"{method}: {msg['error'].get('message')}")
                return msg.get("result", {})
            if "method" in msg:
                self._event(msg)
                if self.pending_dialog:
                    self.pending_dialog = False
                    self.id += 1
                    self.ws.send(json.dumps({"id": self.id, "method": "Page.handleJavaScriptDialog", "params": {"accept": True}}))

    def pump(self):
        """Take in any events waiting, without blocking for long."""
        self.call("Runtime.evaluate", {"expression": "0"})

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=5)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        shutil.rmtree(self.dir, ignore_errors=True)


def find_chrome(given: str | None) -> str:
    for c in ([given] if given else []) + CHROME_PATHS + [shutil.which("google-chrome") or "", shutil.which("chromium") or ""]:
        if c and os.path.exists(c):
            return c
    sys.exit("Chrome wasn't found. Pass --chrome <path>.")


# ---------------------------------------------------------------------------------------------
# One run: a seed, a mode, a window size, a timing.
# ---------------------------------------------------------------------------------------------
class Run:
    def __init__(self, chrome: Chrome, url: str, seed: int, steps: int, mode: str, device: str, timing: str, expect_restore: bool):
        self.c, self.url, self.seed, self.steps, self.mode, self.device, self.timing = chrome, url, seed, steps, mode, device, timing
        self.expect_restore = expect_restore
        self.rng = random.Random(f"{seed}/{mode}/{device}/{timing}")
        self.settled = timing == "settled"
        self.touch = device == "phone"
        self.log: list[str] = []
        self.fails: list[dict] = []
        self.seen_fails: set[tuple] = set()
        self.counts: dict[str, int] = {}
        self.skips: dict[str, int] = {}
        self.stack: list[dict] | None = None   # None: this walk took a path the model can't follow; it picks up at the next root
        self.notes: list[dict] = []
        self.note_n = 0
        self.hot = 0
        self.dirty = False                     # a tab or toggle has changed since the page opened
        self.baseline: dict[tuple, str] = {}
        self.step_no = 0
        self.doing = ""
        self.scripts: list[str] = []
        self.ctx = None

    # -- talking to the page
    def ev(self, expr: str, wait: bool = False):
        params = {"expression": expr, "returnByValue": True, "awaitPromise": wait}
        if self.mode == "framed":
            params["contextId"] = self.frame_context()
        r = self.c.call("Runtime.evaluate", params)
        if "exceptionDetails" in r:
            d = r["exceptionDetails"]
            raise HarnessError(f"page script: {(d.get('exception') or {}).get('description') or d.get('text')}")
        return r.get("result", {}).get("value")

    def top(self, expr: str):
        r = self.c.call("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        return r.get("result", {}).get("value")

    def frame_context(self) -> int:
        if self.ctx in self.c.contexts:
            return self.ctx
        tree = self.c.call("Page.getFrameTree")["frameTree"]
        kids = tree.get("childFrames") or []
        if not kids:
            raise HarnessError("the frame hasn't loaded")
        fid = kids[0]["frame"]["id"]
        for cid, ctx in sorted(self.c.contexts.items(), reverse=True):
            aux = ctx.get("auxData", {})
            if aux.get("frameId") == fid and aux.get("isDefault"):
                self.ctx = cid
                return cid
        raise HarnessError("the frame has no script context yet")

    def S(self, call: str, wait: bool = False):
        return self.ev("__S." + call, wait)

    def settle(self):
        if self.settled:
            self.S("settle()", wait=True)

    # -- opening the page
    def open(self):
        w, h = SIZES[self.device]
        if self.device == "phone":
            # mobile: False keeps the layout at a true 390 with real touch. With True, a page wider than the phone gets
            # zoomed out by Chrome and input stops lining up; that case is its own failure (page-wider-than-phone).
            self.c.call("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 2, "mobile": False})
            self.c.call("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 1})
            self.c.call("Emulation.setUserAgentOverride", {"userAgent": PHONE_UA})
        else:
            self.c.call("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False})
            self.c.call("Emulation.setTouchEmulationEnabled", {"enabled": False})
        cfg = {"mode": self.mode, "hosted": self.mode == "hosted", "run": f"{self.seed}-{time.time()}"}
        src = PAGE_LIB.replace("__CFG__", json.dumps(cfg))
        self.scripts.append(self.c.call("Page.addScriptToEvaluateOnNewDocument", {"source": src})["identifier"])
        self.c.call("Page.navigate", {"url": self.url})
        self.wait_ready()

    def wait_ready(self):
        self.ctx = None
        for _ in range(400):
            try:
                if self.ev("!!(window.__S && __S.ready() && __S.styled())"):
                    break
            except HarnessError:
                pass
            time.sleep(0.05)
        else:
            raise HarnessError("the page never finished opening")
        time.sleep(0.25)  # the in-page Tailwind compiler runs after load
        self.c.pump()

    def close(self):
        for s in self.scripts:
            try:
                self.c.call("Page.removeScriptToEvaluateOnNewDocument", {"identifier": s})
            except HarnessError:
                pass
        self.scripts = []
        self.c.call("Page.navigate", {"url": "about:blank"})

    # -- input. Burst dispatches at once; settled uses real mouse and touch, so what's on top decides.
    def press(self, x: float, y: float, hold: float = 0, button: str = "left"):
        if self.touch and button == "left":
            pt = [{"x": x, "y": y}]
            self.c.call("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": pt})
            if hold:
                time.sleep(hold)
            self.c.call("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        else:
            base = {"x": x, "y": y, "button": button, "clickCount": 1}
            self.c.call("Input.dispatchMouseEvent", {"type": "mousePressed", **base})  # no mouseMoved: Chrome holds it 5s for a frame an idle page never draws
            if hold:
                time.sleep(hold)
            self.c.call("Input.dispatchMouseEvent", {"type": "mouseReleased", **base})

    def tap_target(self, name: str) -> bool:
        """Click whatever __S.t points at. False when a person couldn't have reached it."""
        if not self.settled:
            self.S("click()")
            return True
        a = self.S("aim()")
        if not a:
            self.skip(f"{name}: not on screen")
            return False
        if not a["ok"]:
            self.skip(f"{name}: covered by {a['by'] or 'nothing in view'}")
            return False
        self.press(a["x"], a["y"])
        return True

    def tap(self, sel: str, name: str, n: int = 0) -> bool:
        if not self.S(f"use({json.dumps(sel)},{n})")["found"]:
            return False
        return self.tap_target(name)

    def key(self, k: str):
        if self.settled and not self.touch:  # a phone has no such key, and a real key press stalls touch input afterwards
            code = {"Escape": 27}.get(k, 0)
            base = {"key": k, "code": k, "windowsVirtualKeyCode": code, "nativeVirtualKeyCode": code}
            self.c.call("Input.dispatchKeyEvent", {"type": "rawKeyDown", **base})
            self.c.call("Input.dispatchKeyEvent", {"type": "keyUp", **base})
        else:
            self.S(f"key({json.dumps(k)})")

    # -- bookkeeping
    def skip(self, why: str):
        self.skips[why] = self.skips.get(why, 0) + 1

    def fail(self, kind: str, what: str = "", **extra):
        where = extra.get("where") or (self.last_state or {}).get("screen")
        key = (kind, where)
        if key in self.seen_fails:
            return
        self.seen_fails.add(key)
        self.fails.append({"step": self.step_no, "kind": kind, "action": what, "where": where, **extra})

    last_state: dict | None = None

    def state(self) -> dict:
        self.last_state = self.S("state()")
        return self.last_state

    def entry(self, id_: str) -> dict:
        return {"id": id_, "scroll": 0, "fp": None}

    def here(self, st: dict) -> str:
        return st["overlay"] or st["screen"]

    def land(self, what: str, kind: str):
        """Compare where the page is with where the model says it should be."""
        if self.stack is None:
            return self.state()
        e = self.S(f"expect({json.dumps([x['id'] for x in self.stack])})")
        self.stack = self.stack[: len(e["ids"])]
        st = self.state()
        if st["screen"] != e["screen"] or st["overlay"] != e["overlay"]:
            self.fail(kind, what, want=[e["screen"], e["overlay"]], got=[st["screen"], st["overlay"]], stack=e["ids"])
            self.stack = None
        return st

    def invalidate(self, scroll: bool = False):
        for x in self.stack or []:
            x["fp"] = None
            if scroll:
                x["scroll"] = 0

    def restored(self, what: str, st: dict, entry: dict, kind: str):
        """After Back or a close: the same words and the same scroll as when the person left."""
        if entry.get("fp") is None:
            return
        if st["fp"] != entry["fp"]:
            self.fail("content-changed-after-" + kind, what, where=self.here(st))
        elif not st["overlay"] and abs(st["scroll"] - min(entry["scroll"], max(st["maxScroll"], 0))) > 2:
            self.fail("scroll-not-restored", what, want=entry["scroll"], got=st["scroll"], where=self.here(st))

    def check(self, what: str):
        st = self.state()
        self.c.pump()
        if self.c.crashed:
            raise HarnessError("the page crashed")
        if self.c.errors:
            for e in self.c.errors:
                self.fail("page-error", what, error=e, where=e)
            self.c.errors.clear()
        if st["screens"] == 0:
            self.fail("blank-canvas", what)
        elif st["screens"] > 1:
            self.fail("two-screens-on", what, n=st["screens"])
        elif not st["screenBox"] or min(st["screenBox"]) <= 0:
            self.fail("screen-has-no-size", what, box=st["screenBox"])
        elif not st["fills"]:
            self.fail("screen-does-not-fill-canvas", what, box=st["screenBox"])
        elif st["textLen"] == 0 and not st["overlay"]:
            self.fail("screen-is-empty", what)
        if st["overlays"] > 1:
            self.fail("two-overlays-on", what, n=st["overlays"])
        if st["overlay"] and (not st["overlayBox"] or min(st["overlayBox"]) <= 0):
            self.fail("overlay-has-no-size", what, box=st["overlayBox"])
        if st["page"] != "proto":
            self.fail("left-the-prototype", what, page=st["page"])
            self.S('use(".pt-top [data-page=proto]")')
            self.S("click()")
        key = (st["screen"], st["overlay"], st["dev"], st["role"], json.dumps(st["opts"], sort_keys=True))
        if not self.dirty and not st["before"]:
            self.baseline.setdefault(key, st["fp"])
        if self.settled:
            self.check_pins(what, st)
            if self.mode == "framed":
                self.check_bridge(what, st)

    def check_pins(self, what: str, st: dict):
        pins = self.S("pins()")
        here = self.here(st)
        want = [n for n in self.notes if n.get("pin") and n["screen"] == here and n["dev"] == st["dev"]]
        waiting = self.mode == "hosted" and self.ev("__S.held ? __S.held.length : (window.__stub && __stub.held.length) || 0")
        if len(pins) != len(want) and not waiting:
            self.fail("pin-count", what, want=len(want), got=len(pins), where=here)
        for p in pins:
            if not p["owner"]:
                self.fail("pin-on-wrong-layer", what, where=here)
            elif not p["inside"]:
                self.fail("pin-outside-screen", what, where=here, at=[p["left"], p["top"]])

    def check_bridge(self, what: str, st: dict):
        last = self.top("window.__frame && __frame.last && __frame.last.current")
        if last and last != "overview" and last != "s-" + self.here(st) and not st["before"]:
            self.fail("bridge-reports-wrong-screen", what, want="s-" + self.here(st), got=last)

    # -- actions
    def act_nav(self):
        ctrls = self.S("controls()")
        if not ctrls:
            return self.act_restart()
        pool = ctrls
        if self.hot > 0 and self.rng.random() < 0.55:
            near = [c for c in ctrls if c["back"] or c["close"]]
            if near:
                pool = near
            elif self.rng.random() < 0.5:
                return self.act_restart()
        c = self.rng.choice(pool)
        self.S(f"useCtrl({c['i']})")
        names = [k for k in ("to", "back", "close", "tab", "toggle", "root", "toast", "replace") if c.get(k)]
        what = " ".join(f"{k}={c[k]}" if c[k] is not True else k for k in names)
        if self.settled:
            if not self.S("aim()"):
                self.skip("control: not on screen")
                return "skip " + what
        before = self.state()
        if not self.tap_target("control"):
            return "skip " + what
        self.settle()
        if c["tab"] or c["toggle"]:
            self.dirty = True
            self.invalidate()
        closed = backed = False
        popped = None
        if self.stack is not None:
            if c["close"] and len(self.stack) > 1 and self.S(f"isOverlay({json.dumps(self.stack[-1]['id'])})"):
                self.stack.pop(); closed = True; popped = self.stack[-1]
            if c["back"]:
                if len(self.stack) > 1:
                    self.stack.pop(); backed = True
                    while len(self.stack) > 1:
                        e = self.S("expect(" + json.dumps([x["id"] for x in self.stack]) + ")")
                        if (e["screen"], e["overlay"]) != (before["screen"], before["overlay"]):
                            break
                        self.stack.pop()
                    popped = self.stack[-1]
                else:
                    self.fail("back-did-nothing", what, why="nothing to go back to", where=self.here(before))
            if c["to"]:
                self.follow(c["to"], c["replace"], before, closed or backed, what)
            if c["root"]:
                self.follow_root(c["root"], what)
        st = self.land(what, "overlay-stuck" if closed else "back-landed-elsewhere" if backed else "landed-elsewhere")
        if backed and self.stack is not None and (st["screen"], st["overlay"], st["fp"]) == (before["screen"], before["overlay"], before["fp"]):
            self.fail("back-did-nothing", what, why="the screen didn't change", where=self.here(before))
        if popped is not None and not c["to"] and not c["root"] and self.stack is not None and self.stack[-1] is popped:
            self.restored(what, st, popped, "back" if backed else "close")
        if c["to"] and st["overlay"] and not before["overlay"] and st["screen"] == before["screen"] and abs(st["scroll"] - before["scroll"]) > 2:
            self.fail("scroll-jump-under-overlay", what, want=before["scroll"], got=st["scroll"], where=before["screen"])
        if st["overlay"] and not before["overlay"]:
            self.hot = 3
        return what

    def follow(self, to: str, replace: bool, before: dict, moved: bool, what: str):
        if not self.S(f"exists({json.dumps(to)})"):
            self.fail("to-target-missing", what, target=to)
            return
        if not self.S(f"resolves({json.dumps(to)})"):
            self.fail("to-did-nothing", what, target=to, why="no such place on this device or for this role")
            return
        if not moved:
            self.stack[-1]["scroll"] = before["scroll"]
            self.stack[-1]["fp"] = before["fp"]
        if replace:
            self.stack.pop()
        self.stack.append(self.entry(to))

    def follow_root(self, root: str, what: str):
        if not self.S(f"exists({json.dumps(root)})"):
            self.fail("to-target-missing", what, target=root)
        self.stack = [self.entry(root)]

    def act_restart(self):
        if not self.tap("#pt-restart", "start over"):
            return "skip start over"
        self.settle()
        self.stack = [self.entry(self.S("roleStart()"))]
        st = self.land("start over", "landed-elsewhere")
        key = (st["screen"], st["overlay"], st["dev"], st["role"], json.dumps(st["opts"], sort_keys=True))
        if key in self.baseline and self.baseline[key] != st["fp"]:
            self.fail("start-over-kept-old-state", "start over", where=st["screen"])
        return "start over"

    def act_device(self):
        devs = self.S("devices()")
        st = self.state()
        others = [d for d in devs if d != st["dev"]]
        if not others:
            return self.act_nav()
        d = self.rng.choice(others)
        if not self.tap(f'#pt-devs [data-dev="{d}"]', "device"):
            return "skip device"
        self.settle()
        self.invalidate(scroll=True)
        self.land("device " + d, "device-landed-elsewhere")
        self.hot = 3
        return "device " + d

    def act_select(self):
        sels = [s for s in self.S("selects()") if len(s["options"]) > 1]
        if not sels:
            return self.act_nav()
        s = self.rng.choice(sels)
        value = self.rng.choice([o for o in s["options"] if o != s["value"]])
        dev_before = self.state()["dev"]
        self.S(f"setSelect({json.dumps(s['group'])},{json.dumps(value)})")
        self.settle()
        what = f"select {s['group']}={value}"
        if s["group"] == "role":
            self.stack = [self.entry(self.S("roleStart()"))]
            self.hot = 3
        else:
            self.invalidate(scroll=self.state()["dev"] != dev_before)
        self.land(what, "landed-elsewhere")
        return what

    def act_compare(self):
        n = self.S('count("#pt-compare [data-cmp]")')
        if not n:
            return self.act_nav()
        i = self.rng.randrange(n)
        if not self.tap("#pt-compare [data-cmp]", "compare", i):
            return "skip compare"
        self.settle()
        self.hot = 3
        return f"compare {i}"

    def act_escape(self):
        before = self.state()
        self.key("Escape")
        self.settle()
        typing = before["active"] in ("TEXTAREA", "SELECT")
        if self.stack is not None and not typing and len(self.stack) > 1 and self.S(f"isOverlay({json.dumps(self.stack[-1]['id'])})"):
            self.stack.pop()
            st = self.land("escape", "overlay-stuck")
            if self.stack is not None:
                self.restored("escape", st, self.stack[-1], "close")
        return "escape"

    def act_scroll(self):
        return f"scroll to {self.S('scrollTo(%f)' % self.rng.random())}"

    def open_path(self, path: list, device: str | None, what: str, option: bool):
        """The page's own jump: Info links, Requirements, What's new. The stack becomes the path."""
        self.settle()
        if self.S("page()") != "proto":
            self.S('use(".pt-top [data-page=proto]")')
            self.S("click()")
            self.settle()
        if option:
            self.dirty = True
        start = self.S("roleStart()")
        full = [start, path[0]] if len(path) == 1 and path[0] != start else path
        self.stack = [self.entry(i) for i in full]
        self.land(what, "landed-elsewhere")
        return what

    def act_links(self, where: str):
        if not self.tap(f".pt-top [data-page={where}]", where + " tab"):
            return "skip " + where
        self.settle()
        links = self.S(f"links({json.dumps(where)})")
        if not links:
            self.tap(".pt-top [data-page=proto]", "prototype tab")
            self.settle()
            return where + " (nothing to open)"
        link = self.rng.choice(links)
        self.S(f"useLink({link['i']})")
        if not self.tap_target(where + " link"):
            self.tap(".pt-top [data-page=proto]", "prototype tab")
            self.settle()
            return "skip " + where + " link"
        return self.open_path(link["path"], link["device"], f"{where} link {' '.join(link['path'])}", link["option"])

    def act_news(self):
        if not self.S('count("#pt-new")'):
            return self.act_nav()
        if not self.tap("#pt-new", "what's new"):
            return "skip what's new"
        self.settle()
        news = self.S("news()")
        if not news:
            if self.S('count("#pt-new-pop")'):
                self.tap("#pt-new", "what's new")
            return "what's new (nothing)"
        item = self.rng.choice(news)
        self.S(f"useNews({item['i']})")
        if not self.tap_target("what's new item"):
            self.S('use("#pt-new")'); self.S("click()")
            return "skip what's new item"
        if not item["path"]:
            self.stack = None
            self.settle()
            return "what's new jump (unknown path)"
        return self.open_path(item["path"], item["device"], "what's new " + " ".join(item["path"]), False)

    def act_notes(self):
        if self.rng.random() < 0.5:
            if not self.tap("#pt-note-btn", "notes"):
                return "skip notes"
            self.settle()
            return "notes toggle"
        if self.S('count(".pt-side [data-scope]")'):
            i = self.rng.randrange(2)
            self.tap(".pt-side [data-scope]", "notes scope", i)
            self.settle()
            return f"notes scope {i}"
        return "notes (closed)"

    def side_open(self) -> bool:
        if self.state()["side"]:
            return True
        if not self.tap("#pt-note-btn", "notes"):
            return False
        self.settle()
        return self.state()["side"]

    def finish_note(self, pinned: bool) -> str:
        st = self.state()
        self.note_n += 1
        text = f"stress note {self.seed}-{self.note_n}"
        self.S(f"type({json.dumps(text)})")
        if not self.tap("#pt-add", "add note"):
            self.note_n -= 1
            self.S('type("")')
            return "skip add note"
        self.settle()
        if self.mode == "hosted":
            self.flush()
        self.notes.append({"text": text, "screen": self.here(st), "dev": st["dev"], "pin": pinned})
        return "note added" + (" with pin" if pinned else "")

    def act_pin_button(self):
        if not self.side_open():
            return "skip pin (notes didn't open)"
        if self.S("state().before"):
            return "skip pin (compare on)"
        if not self.tap("#pt-pin-btn", "pin button"):
            return "skip pin button"
        self.settle()
        rx, ry = 0.1 + self.rng.random() * 0.8, 0.1 + self.rng.random() * 0.8
        p = self.S(f"spot({rx},{ry})")
        if self.settled:
            self.press(p["x"], p["y"])
        else:
            self.S(f"clickAt({p['x']},{p['y']})")
        self.settle()
        if not self.S("pending()"):
            self.tap("#pt-pin-btn", "pin button")  # the click went somewhere else: put the button back
            self.settle()
            return "skip pin (no spot taken)"
        return self.finish_note(True)

    def act_pin_press(self):
        """Pin anywhere: right-click on a laptop, press-and-hold on a phone (D28). Counts as skipped until the page has it."""
        rx, ry = 0.1 + self.rng.random() * 0.8, 0.1 + self.rng.random() * 0.8
        p = self.S(f"spot({rx},{ry})")
        if self.settled:
            if self.touch:
                self.S(f"pointer({p['x']},{p['y']},0,0,600)", wait=True)
            else:
                self.press(p["x"], p["y"], button="right")
        else:
            self.S(f"contextAt({p['x']},{p['y']})")
        self.settle()
        if not self.S("pending()"):
            self.skip("pins: the page has no right-click or press-and-hold yet")
            return "skip pin press"
        return self.finish_note(True)

    def act_pin_drag(self):
        if not self.S('use(".pt-pin:not(.pending)")')["found"]:
            return "skip drag (no pin here)"
        a = self.S("aim()")
        if not self.settled or not a or not a["ok"]:
            self.skip("pins: drag needs real input")
            return "skip drag"
        before = self.S("pins()")
        dx, dy = self.rng.randint(-60, 60), self.rng.randint(-60, 60)
        c = self.c
        if self.touch:
            self.S(f"pointer({a['x']},{a['y']},{dx},{dy},0)", wait=True)
        else:
            base = {"button": "left", "clickCount": 1}
            c.call("Input.dispatchMouseEvent", {"type": "mousePressed", "x": a["x"], "y": a["y"], **base})
            c.call("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": a["x"] + dx, "y": a["y"] + dy, "button": "left", "buttons": 1})
            c.call("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": a["x"] + dx, "y": a["y"] + dy, **base})
        self.settle()
        if self.S("pins()") == before:
            self.skip("pins: the page has no drag yet")
            return "skip drag (no support)"
        return "pin dragged"

    def act_pin_edit(self):
        if not self.S('use(".pt-card .pt-edit")')["found"]:
            self.skip("pins: the page has no edit yet")
            return "skip edit"
        if not self.tap_target("edit"):
            return "skip edit"
        self.settle()
        return "note edit opened"

    def act_note_remove(self):
        if not self.S('use("#pt-list .pt-remove")')["found"]:
            return "skip remove (none)"
        texts = self.S("noteTexts()")
        if not self.tap_target("remove"):
            return "skip remove"
        self.settle()
        if self.mode == "hosted":
            self.flush()
        gone = set(texts) - set(self.S("noteTexts()"))
        self.notes = [n for n in self.notes if n["text"] not in gone]
        return "note removed"

    def act_reload(self):
        st = self.state()
        self.c.call("Page.reload", {})
        self.wait_ready()
        if self.mode == "hosted":
            self.flush()
        if self.S("page()") != "proto":
            self.S('use(".pt-top [data-page=proto]")')
            self.S("click()")
        after = self.state()
        self.dirty = False
        self.baseline = {}
        self.c.errors.clear() if not self.c.errors else None
        if self.expect_restore:
            if (after["screen"], after["overlay"], after["dev"]) != (st["screen"], st["overlay"], st["dev"]):
                self.fail("reload-lost-the-place", "reload", want=[st["screen"], st["overlay"], st["dev"]], got=[after["screen"], after["overlay"], after["dev"]])
            self.stack = None
        else:
            self.stack = [self.entry(self.S("roleStart()"))]
            self.land("reload", "reload-landed-elsewhere")
        if self.mode == "framed" and not self.expect_restore:
            self.notes = []  # the sandbox has no storage and the page has no bridge yet, so its notes went with the reload
        return "reload"

    def act_browser_back(self):
        before = self.state()
        self.ev("setTimeout(() => history.back(), 0), 0")
        time.sleep(0.15)
        try:
            self.c.pump()
            alive = self.ev("!!(window.__S && __S.ready())")
        except HarnessError:
            alive = False
        if not alive:
            if self.expect_restore:
                self.fail("browser-back-left-the-page", "browser back", where=self.here(before))
            self.skip("browser Back left the page (no history in the page yet)")
            self.c.call("Page.navigate", {"url": self.url})
            self.wait_ready()
            if self.S("page()") != "proto":
                self.S('use(".pt-top [data-page=proto]")')
                self.S("click()")
            self.dirty = False
            self.baseline = {}
            self.stack = [self.entry(self.S("roleStart()"))]
            self.state()
            if self.mode == "framed":
                self.notes = []
            return "browser back (left the page, reopened)"
        self.settle()
        if self.expect_restore and self.stack is not None and len(self.stack) > 1:
            self.stack.pop()
            st = self.land("browser back", "back-landed-elsewhere")
            if self.stack is not None:
                self.restored("browser back", st, self.stack[-1], "back")
        return "browser back"

    def act_frame_goto(self):
        if self.mode != "framed":
            return self.act_nav()
        last = self.top("window.__frame && __frame.last")
        keys = [s["key"] for s in (last or {}).get("screens", []) if s["key"].startswith("s-")]
        if not keys:
            return "goto (no screens reported)"
        key = self.rng.choice(keys)
        self.top(f"__frame.goto({json.dumps(key)})")
        time.sleep(0.03)
        self.settle()
        return self.open_path([key[2:]], None, "goto " + key, False)

    def act_frame_feedback(self):
        if self.mode != "framed" or not self.settled:
            return self.act_nav()
        self.top("__frame.askFeedback()")
        time.sleep(0.05)
        self.settle()
        got = self.top("__frame.feedback")
        if not got or "text" not in got:
            self.fail("bridge-no-feedback-reply", "feedback")
        return "feedback asked"

    def flush(self):
        if self.mode != "hosted":
            return 0
        n = 0
        for _ in range(8):  # an answer can start the next question
            m = self.S("flush()")
            if self.settled:
                self.S("settle()", wait=True)
            else:
                self.ev("new Promise((r) => setTimeout(r, 0))", wait=True)
            n += m or 0
            if not m:
                break
        if self.S("seeded") and not any(x["text"].startswith("Seeded pinned") for x in self.notes):
            st = self.first_screen
            self.notes.append({"text": "Seeded pinned note", "screen": st[0], "dev": st[1], "pin": True})
            self.notes.append({"text": "Seeded note from someone else", "screen": st[0], "dev": st[1], "pin": False})
            self.ev("__S.seeded = false")
        return n

    first_screen = ("", "")

    def choose(self):
        r = self.rng.random()
        if self.hot > 0:
            self.hot -= 1
        if r < 0.60:
            q = self.rng.random()
            if q < 0.80: return self.act_nav
            if q < 0.86: return self.act_restart
            if q < 0.90: return self.act_escape
            if q < 0.93: return self.act_browser_back
            if q < 0.95: return self.act_reload
            if q < 0.97: return lambda: self.act_links(self.rng.choice(["info", "reqs"]))
            if q < 0.985: return self.act_news
            return self.act_frame_goto
        if r < 0.80:
            q = self.rng.random()
            if q < 0.40: return self.act_device
            if q < 0.80: return self.act_select
            return self.act_compare
        q = self.rng.random()
        if q < 0.25: return self.act_scroll
        if q < 0.45: return self.act_notes
        if q < 0.65: return self.act_pin_button
        if q < 0.75: return self.act_pin_press
        if q < 0.85: return self.act_pin_drag
        if q < 0.90: return self.act_pin_edit
        if q < 0.97: return self.act_note_remove
        return self.act_frame_feedback

    def walk(self):
        self.open()
        if self.S("page()") != "proto":
            self.tap(".pt-top [data-page=proto]", "prototype tab")
            self.settle()
        st = self.state()
        self.first_screen = (self.ev('document.querySelector("#pt-canvas .screen:not(.pt-before), #pt-canvas .overlay").dataset.id'),
                             self.ev('document.querySelector("#pt-canvas .screen:not(.pt-before), #pt-canvas .overlay").dataset.device'))
        self.stack = [self.entry(self.S("roleStart()"))]
        for b in self.S("deadLinks()"):
            self.fail("to-target-missing", "static check", target=b, where=b)
        for b in self.S("colourOnly()"):
            self.fail("status-by-colour-alone", "static check", where=b)
        if self.device == "phone":
            for tab in ("proto", "info"):
                self.S(f'use(".pt-top [data-page={tab}]")'); self.S("click()")
                wide = self.S("tooWide()")
                if wide:
                    self.fail("page-wider-than-phone", "static check", where=tab, **wide)
            self.S('use(".pt-top [data-page=proto]")'); self.S("click()")
            self.settle()
        self.check("open")
        flush_at = self.rng.randint(1, 6)
        for i in range(1, self.steps + 1):
            self.step_no = i
            if i == flush_at:
                n = self.flush()
                if n:
                    self.log.append(f"{i} database answered ({n})")
                flush_at = i + self.rng.randint(4, 20)
            b = self.state()
            if self.device == "phone" and b["side"] and self.rng.random() < 0.6:
                self.tap("#pt-side-close", "close notes")  # at phone width Notes fills the page, so a person closes it to carry on
                self.settle()
                b = self.state()
            act = self.choose()
            self.doing = getattr(act, "__name__", "action")
            what = act()
            a = self.state()
            self.counts[what.split(" ")[0]] = self.counts.get(what.split(" ")[0], 0) + 1
            self.log.append(f"{i} {what} | {b['screen']}/{b['overlay'] or '-'}/{b['dev']} -> {a['screen']}/{a['overlay'] or '-'}/{a['dev']}")
            self.check(what)
            if self.stack is None and not self.rng.randrange(6):
                self.step_no = i
                self.act_restart()  # the model lost the thread after a failure: start clean and keep walking
            if len(self.fails) >= MAX_FAILURES:
                break
        return self.result()

    def result(self):
        digest = hashlib.sha1("\n".join(self.log).encode()).hexdigest()[:10]
        return {"seed": self.seed, "mode": self.mode, "device": self.device, "timing": self.timing, "steps": len([x for x in self.log if " database " not in x]),
                "failures": self.fails, "skips": self.skips, "log_hash": digest, "actions": self.counts, "log": self.log}


# ---------------------------------------------------------------------------------------------
# Running many
# ---------------------------------------------------------------------------------------------
def parse_seeds(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += range(int(a), int(b) + 1)
        else:
            out.append(int(part))
    return out


def replay_cmd(a, page: str, r: dict) -> str:
    extra = " --expect-restore" if a.expect_restore else ""
    return f"python3 stress.py {page} --seed {r['seed']} --steps {a.steps} --mode {r['mode']} --device {r['device']} --timing {r['timing']}{extra}"


def main():
    p = argparse.ArgumentParser(description="A seeded random click-through of a prototype page.")
    p.add_argument("page")
    p.add_argument("--seeds", default="1-24")
    p.add_argument("--seed", type=int, help="replay one seed")
    p.add_argument("--steps", type=int, default=200)
    p.add_argument("--device", choices=["phone", "laptop", "both"], default="both")
    p.add_argument("--mode", choices=["plain", "framed", "hosted", "all"], default="all")
    p.add_argument("--timing", choices=["burst", "settled", "both"], default="both")
    p.add_argument("--expect-restore", action="store_true", help="the page keeps its place on reload and has browser history")
    p.add_argument("--out", help="default: a new folder under the system temp folder")
    p.add_argument("--jobs", type=int, default=max(1, min(6, (os.cpu_count() or 2) - 2)))
    p.add_argument("--chrome")
    a = p.parse_args()

    page = os.path.abspath(os.path.expanduser(a.page))
    if not os.path.exists(page):
        sys.exit(f"No such page: {page}")
    binary = find_chrome(a.chrome)
    out = os.path.abspath(os.path.expanduser(a.out)) if a.out else tempfile.mkdtemp(prefix="stress-")
    os.makedirs(out, exist_ok=True)
    frame = os.path.join(out, "stress-frame.html")
    with open(frame, "w", encoding="utf-8") as f:
        f.write(FRAME_HTML.replace("__SRC__", "file://" + page))

    seeds = [a.seed] if a.seed is not None else parse_seeds(a.seeds)
    modes = ["plain", "framed", "hosted"] if a.mode == "all" else [a.mode]
    devices = ["laptop", "phone"] if a.device == "both" else [a.device]
    timings = ["burst", "settled"] if a.timing == "both" else [a.timing]
    jobs: "queue.Queue[tuple]" = queue.Queue()
    for m in modes:
        for d in devices:
            for t in timings:
                for s in seeds:
                    jobs.put((s, m, d, t))
    total = jobs.qsize()
    results: list[dict] = []
    lock = threading.Lock()

    def report(r: dict):
        with lock:
            results.append(r)
            name = f"seed {r['seed']} {r['mode']} {r['device']} {r['timing']}"
            with open(os.path.join(out, f"{r['mode']}-{r['device']}-{r['timing']}-{r['seed']}.json"), "w") as f:
                json.dump(r, f, indent=1)
            if r.get("harness"):
                print(f"{name}: not finished: {r['harness']}", flush=True)
            elif r["failures"]:
                first = r["failures"][0]
                print(f"{name}: {r['steps']} steps, {len(r['failures'])} failures [{r['log_hash']}], first at step {first['step']}: {first['kind']} ({first.get('where')})", flush=True)
                print("  replay: " + replay_cmd(a, a.page, r), flush=True)
            else:
                print(f"{name}: {r['steps']} steps, ok [{r['log_hash']}]", flush=True)

    retried = set()

    def worker():
        chrome = None
        while True:
            try:
                s, m, d, t = jobs.get_nowait()
            except queue.Empty:
                break
            run = None
            try:
                if chrome is None:
                    chrome = Chrome(binary)
                chrome.errors.clear()
                url = "file://" + (frame if m == "framed" else page)
                run = Run(chrome, url, s, a.steps, m, d, t, a.expect_restore)
                r = run.walk()
                run.close()
                report(r)
            except Exception as e:  # the rig, not the page: say so, and carry on with a new Chrome
                if (s, m, d, t) not in retried:
                    retried.add((s, m, d, t))
                    print(f"seed {s} {m} {d} {t}: the rig failed ({e}), again on a new Chrome", flush=True)
                    jobs.put((s, m, d, t))
                    if chrome:
                        chrome.close()
                    chrome = None
                    continue
                partial = run.result() if run else {"seed": s, "mode": m, "device": d, "timing": t, "steps": 0, "failures": [], "skips": {}, "log_hash": "", "log": []}
                partial["harness"] = f"{type(e).__name__}: {e}" + (f" (during {run.doing}, step {run.step_no})" if run and run.doing else "")
                report(partial)
                if chrome:
                    chrome.close()
                chrome = None
        if chrome:
            chrome.close()

    started = time.time()
    threads = [threading.Thread(target=worker) for _ in range(min(a.jobs, total))]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    failed = [r for r in results if r["failures"]]
    rig = [r for r in results if r.get("harness")]
    kinds: dict[str, list] = {}
    for r in failed:
        for f in r["failures"]:
            kinds.setdefault(f["kind"], []).append((r, f))
    skips: dict[str, int] = {}
    for r in results:
        for k, n in r["skips"].items():
            skips[k] = skips.get(k, 0) + n
    print(f"\n{len(results)} runs of {total} in {int(time.time() - started)}s: {len(results) - len(failed) - len(rig)} ok, {len(failed)} with failures, {len(rig)} not finished.")
    combos = sorted({(r["mode"], r["device"], r["timing"]) for r in results})
    print("Ran: " + ", ".join(" ".join(c) for c in combos))
    for k, items in sorted(kinds.items(), key=lambda x: -len(x[1])):
        r, f = min(items, key=lambda x: x[1]["step"])
        places = sorted({str(x[1].get("where")) for x in items})
        print(f"  {k}: {len(items)} times, at {', '.join(places[:6])}{' …' if len(places) > 6 else ''}")
        print(f"    earliest: step {f['step']}, {f.get('action')}\n    replay: {replay_cmd(a, a.page, r)}")
    if skips:
        print("Skipped actions (not failures):")
        for k, n in sorted(skips.items(), key=lambda x: -x[1]):
            print(f"  {k}: {n}")
    print(f"JSON per run: {out}")
    sys.exit(1 if failed or rig else 0)


if __name__ == "__main__":
    main()
