// Run after opening the rendered example with playwright-cli run-code --filename.
// Throws on a regression; assertions exercise behavior, not source-string matches.
async (page) => {
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.reload();
  const check = (ok, label) => { if (!ok) throw new Error(label); };
  await page.setViewportSize({width: 1440, height: 1000});
  check(await page.locator("#step-title").innerText() === "Transient failures should not silently drop work", "initial narrative");
  check(await page.locator("#findings-panel").isHidden(), "review lens begins hidden");
  await page.locator("#next-step").click();
  check((await page.locator("#claim-status").innerText()).toLowerCase() === "demonstrated", "claim status visible");
  check(await page.locator("#code-panel").innerText().then(text => text.includes("schedule_retry")), "selected source visible");
  await page.getByRole("button", {name: "Retry implementation", exact: true}).click();
  check(await page.locator("#code-panel").innerText().then(text => text.includes("schedule_retry")), "source evidence button selects excerpt");
  check(await page.locator("#output-examples").innerText().then(text => text.includes("next_attempt")), "intermediate output follows mechanism");
  await page.keyboard.press("ArrowRight");
  check(await page.locator("#step-title").innerText() === "The exhausted path is observable and tested", "keyboard navigation");
  check(await page.locator("#output-examples").innerText().then(text => text.includes("return value: None")), "final output follows proof");
  await page.locator("#play-story").click();
  check(await page.locator("#play-story").getAttribute("aria-pressed") === "true", "story play");
  await page.locator("#play-story").click();
  check(await page.locator("#play-story").getAttribute("aria-pressed") === "false", "story pause");
  await page.locator("#toggle-findings").click();
  check(await page.locator("#findings-panel").isVisible(), "review lens opens separately");
  check(await page.locator("#finding-list").innerText().then(text => !text.includes("[object Object]")), "typed finding evidence renders meaningfully");
  check((await page.locator("#finding-list .finding-meta").first().innerText()).toLowerCase().includes("demonstrated"), "finding evidence status visible");
  await page.getByRole("button", {name: "Terminal-path test", exact: true}).last().click();
  check(await page.locator("#code-panel").innerText().then(text => text.includes("test_exhausted_job")), "finding evidence navigates to source");
  await page.locator("#next-step").click();
  check(await page.locator("#evidence-gap").innerText().then(text => text.toLowerCase().includes("synthetic renderer example")), "evidence gap stays visible");
  await page.setViewportSize({width: 390, height: 844});
  await page.emulateMedia({reducedMotion: "reduce"});
  await page.reload();
  await page.locator("#next-step").click();
  const canvas = page.locator("#diagram-stage canvas");
  check(await canvas.count() === 1, "3D canvas rendered on mobile");
  await canvas.scrollIntoViewIfNeeded();
  const box = await canvas.boundingBox();
  await page.mouse.move(box.x + 100, box.y + 100);
  await page.mouse.down();
  await page.mouse.move(box.x + 130, box.y + 120);
  await page.mouse.up();
  await page.mouse.wheel(0, 100);
  check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "mobile layout fits viewport");
  check(await page.locator("#code-panel").isVisible(), "mobile source panel visible");
  for (const status of ["inferred", "unknown"]) {
    await page.route("**/index.html", async route => {
      const response = await route.fetch();
      const html = await response.text();
      const body = html.replace(/(<script id="walkthrough-data" type="application\/json">)([\s\S]*?)(<\/script>)/,
        (_, start, encoded, end) => {
          const data = JSON.parse(encoded);
          data.findings[0].claim_status = status;
          return start + JSON.stringify(data).replace(/<\//g, "<\\/") + end;
        });
      await route.fulfill({response, body});
    });
    await page.reload();
    await page.locator("#toggle-findings").click();
    check((await page.locator("#finding-list .finding-meta").first().innerText()).toLowerCase().includes(status), "finding " + status + " label visible");
    await page.unroute("**/index.html");
  }
  check(errors.length === 0, "browser errors: " + errors.join("; "));
  return {status: "passed", checks: ["desktop", "source links", "claim labels", "evidence gaps", "navigation", "play/pause", "review lens", "mobile", "3D interaction", "reduced motion", "finding demonstrated/inferred/unknown labels"], errors};
}
