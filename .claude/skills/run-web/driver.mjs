// REPL driver for Closet Muse frontend. Drives headless Chromium via Playwright.
// Designed for agents: wrap in tmux, send-keys commands, capture-pane output.
import { chromium } from 'playwright';
import * as readline from 'node:readline';
import * as fs from 'node:fs';
import * as path from 'node:path';

const SHOT_DIR = process.env.SCREENSHOT_DIR || '/tmp/shots';
fs.mkdirSync(SHOT_DIR, { recursive: true });

let browser = null;
let context = null;
let page = null;
const consoleErrors = [];

const COMMANDS = {
  async launch() {
    if (browser) return console.log('already launched');
    browser = await chromium.launch({ args: ['--no-sandbox'] });
    context = await browser.newContext();
    page = await context.newPage();
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => consoleErrors.push(String(err)));
    console.log('launched.');
  },

  async nav(url) {
    if (!page) return console.log('ERROR: launch first');
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    console.log('navigated:', url);
  },

  async reload() {
    if (!page) return console.log('ERROR: launch first');
    await page.reload({ waitUntil: 'domcontentloaded' });
    console.log('reloaded');
  },

  async ss(name) {
    if (!page) return console.log('ERROR: launch first');
    const f = path.join(SHOT_DIR, (name || `ss-${Date.now()}`) + '.png');
    await page.screenshot({ path: f });
    console.log('screenshot:', f);
  },

  async 'click-text'(text) {
    if (!page) return console.log('ERROR: launch first');
    const r = await page.evaluate((t) => {
      const els = [...document.querySelectorAll('button, a, [role="button"]')];
      const el = els.find((e) => e.textContent?.trim() === t) ?? els.find((e) => e.textContent?.includes(t));
      if (!el) return 'NOT_FOUND';
      el.click();
      return 'OK: ' + el.tagName;
    }, text);
    console.log('click-text', JSON.stringify(text), '→', r);
  },

  async fill(args) {
    if (!page) return console.log('ERROR: launch first');
    const [sel, ...rest] = args.split(' ');
    const value = rest.join(' ');
    await page.fill(sel, value);
    console.log('filled', sel, '=', value);
  },

  async click(sel) {
    if (!page) return console.log('ERROR: launch first');
    await page.click(sel);
    console.log('clicked', sel);
  },

  async 'set-file'(args) {
    if (!page) return console.log('ERROR: launch first');
    const [sel, ...rest] = args.split(' ');
    const filePath = rest.join(' ');
    await page.locator(sel).setInputFiles(filePath);
    console.log('set-file', sel, '=', filePath);
  },

  async wait(sel) {
    if (!page) return console.log('ERROR: launch first');
    try {
      await page.waitForSelector(sel, { timeout: 10_000 });
      console.log('found:', sel);
    } catch {
      console.log('TIMEOUT:', sel);
    }
  },

  async 'wait-text'(text) {
    if (!page) return console.log('ERROR: launch first');
    try {
      await page.waitForFunction((t) => document.body.innerText.includes(t), text, { timeout: 10_000 });
      console.log('found text:', text);
    } catch {
      console.log('TIMEOUT waiting for text:', text);
    }
  },

  async url() {
    if (!page) return console.log('ERROR: launch first');
    console.log(page.url());
  },

  async text(sel) {
    if (!page) return console.log('ERROR: launch first');
    console.log(await page.evaluate((s) => (s ? document.querySelector(s) : document.body)?.innerText ?? '(null)', sel || null));
  },

  async eval(expr) {
    if (!page) return console.log('ERROR: launch first');
    try {
      console.log(JSON.stringify(await page.evaluate(expr)));
    } catch (e) {
      console.log('ERROR:', e.message);
    }
  },

  async cookies() {
    if (!context) return console.log('ERROR: launch first');
    const cookies = await context.cookies();
    console.log(JSON.stringify(cookies, null, 2));
  },

  async 'console-errors'() {
    console.log(consoleErrors.length === 0 ? 'no console errors' : JSON.stringify(consoleErrors, null, 2));
  },

  async quit() {
    if (browser) await browser.close().catch(() => {});
    browser = null;
    context = null;
    page = null;
  },
  help() {
    console.log('commands:', Object.keys(COMMANDS).join(', '));
  },
};

const stdin = fs.createReadStream(null, { fd: fs.openSync('/dev/stdin', 'r') });
const rl = readline.createInterface({ input: stdin, output: process.stdout, prompt: 'driver> ' });

// Piped/heredoc input delivers every line synchronously, but command handlers are
// async (browser actions) — without serializing, later lines (nav/click/...) would
// race ahead of an in-flight `launch` and fail with "launch first". Queue each line
// behind the previous one's completion instead of relying on the emitter to wait.
let queue = Promise.resolve();
// Piped/heredoc stdin drains (and fires 'close') long before the queued async
// commands finish running — guard rl.prompt() so it doesn't touch an interface
// that has already closed (throws ERR_USE_AFTER_CLOSE otherwise).
let closing = false;

rl.on('line', (line) => {
  queue = queue.then(async () => {
    const [cmd, ...rest] = line.trim().split(/\s+/);
    if (!cmd) return;
    const fn = COMMANDS[cmd];
    if (!fn) {
      console.log('unknown:', cmd, '— try: help');
      return;
    }
    try {
      await fn(rest.join(' '));
    } catch (e) {
      console.log('ERROR:', e.message);
    }
    if (cmd === 'quit') {
      closing = true;
      rl.close();
      process.exit(0);
    }
    if (!closing) rl.prompt();
  });
});
rl.on('close', async () => {
  closing = true;
  // With piped/heredoc input, 'close' fires as soon as stdin drains — which can be
  // before the queued async commands above have actually run. Wait for the queue to
  // finish before tearing down, or a fast pipe exits before `launch` ever completes.
  await queue;
  await COMMANDS.quit();
  process.exit(0);
});

console.log('closet-muse web driver — "help" for commands, "launch" to start');
rl.prompt();
