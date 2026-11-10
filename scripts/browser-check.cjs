/* Offline file:// verification. Install Playwright separately, including its Chromium browser. */
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const root = path.resolve(__dirname, "..");
async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ offline: true, viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const errors = [];
  const network = [];
  page.on("pageerror", e => errors.push(e.message));
  page.on("console", m => { if (["error", "warning"].includes(m.type())) errors.push(m.text()); });
  page.on("request", r => { if (/^https?:/.test(r.url())) network.push(r.url()); });
  const url = file => pathToFileURL(path.join(root, "portal", file)).href;
  const checks = [];
  try {
    await page.goto(url("index.html"));
    checks.push({ check: "desktop-file-offline", passed: (await page.locator("h1").innerText()).includes("개발자 가이드") });
    fs.mkdirSync(path.join(root, "verification"), { recursive: true });
    await page.screenshot({ path: path.join(root, "verification/portal-desktop.png") });
    await page.locator("#search").fill("Credential Broker");
    checks.push({ check: "local-search", passed: await page.locator("#results a").count() > 0 });
    await page.locator("#search").fill("no-such-word-xyz");
    checks.push({ check: "empty-search", passed: (await page.locator("#results").innerText()).includes("검색 결과가 없습니다") });
    await page.goto(url("diagrams.html"));
    checks.push({ check: "all-nine-local-svg", passed: await page.locator("img").evaluateAll(xs => xs.length === 9 && xs.every(x => x.complete && x.naturalWidth > 0)) });
    await page.goto(url("docs--requirements--baseline-v0.1.html"));
    checks.push({ check: "baseline-table", passed: await page.locator("tbody tr").count() === 37 });
    await page.goto(url("docs--onboarding--03-one-request.html"));
    checks.push({ check: "term-help", passed: await page.locator(".gloss").count() > 0 && await page.locator(".gloss-open").count() === 1 });
    await page.locator(".ix-bar .primary").first().click();
    checks.push({ check: "step-player", passed: await page.locator(".ix-flow li.on").count() === 1 });
    await page.locator('.ix-sim input[name="noToken"]').check();
    await page.locator(".ix-sim .ix-actions .primary").first().click();
    await page.waitForFunction(() => document.querySelector(".ix-sim .ix-result.bad"), null, { timeout: 5000 });
    checks.push({ check: "request-simulator", passed: (await page.locator(".ix-sim .ix-result b").first().innerText()).includes("401") });
    await page.goto(url("docs--identity-and-credentials.html"));
    checks.push({ check: "broker-module", passed: (await page.locator("main").innerText()).includes("RFC8693") });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(url("index.html"));
    await page.locator("#menu").click();
    checks.push({ check: "mobile-menu", passed: await page.locator("#menu").getAttribute("aria-expanded") === "true" });
    await page.locator("#menu").click();
    checks.push({ check: "mobile-no-page-overflow", passed: await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth) });
    await page.screenshot({ path: path.join(root, "verification/portal-mobile.png") });
    checks.push({ check: "console-clean", passed: errors.length === 0, errors });
    checks.push({ check: "zero-network-dependency", passed: network.length === 0, network });
    const report = { status: checks.every(c => c.passed) ? "passed" : "failed", browser: await browser.version(), mode: "file:// + offline:true", checks };
    fs.writeFileSync(path.join(root, "verification/browser-results.json"), JSON.stringify(report, null, 2) + "\n");
    console.log(JSON.stringify(report, null, 2));
    if (report.status !== "passed") process.exitCode = 1;
  } finally { await browser.close(); }
}
main().catch(e => { console.error(e); process.exitCode = 1; });

