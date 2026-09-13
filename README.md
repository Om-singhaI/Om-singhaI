<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/hero/hero-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/hero/hero-light.svg">
    <img src="assets/hero/hero-light.svg" width="100%" alt="Om Singhal. Spatial computing, graphics, and the open source tooling underneath. PRs merged at Microsoft, Meta, Apple, and more. Combined B.S./M.S. in Computer Science at Purdue University. Open to software engineering roles.">
  </picture>
</p>

### I fix the bugs hiding in tools other engineers build on.

I'm in a combined B.S./M.S. program in Computer Science at Purdue University, and I'm looking for a software engineering role. My fixes have landed in ONNX export, Core ML conversion, the Lexical editor, Kiota's code generator, and Wrangler. You can reach me at [wengsinghal@gmail.com](mailto:wengsinghal@gmail.com).

## Open source

Merged pull requests at Microsoft, Meta, Apple, Cloudflare, and AWS, since my first merge on August 24, 2026. The skyline below redraws itself every day as new ones land.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/skyline/oss-skyline-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/skyline/oss-skyline-light.svg">
    <img src="assets/skyline/oss-skyline-light.svg" width="100%" alt="Isometric skyline of my merged pull requests: one building per repository, one floor per merged PR, grouped into company districts. It redraws itself every day.">
  </picture>
</p>

### Six worth a look

- **[microsoft/onnxscript#3009](https://github.com/microsoft/onnxscript/pull/3009)** Honor the `dtype` argument of `aten::mean` when exporting without `dim`.<br>
  Models that asked for a float64 mean quietly averaged in float32, so the mean of `[1e8, 1, -1e8]` came back as 0 instead of 1/3, with no error to warn anyone. Merged by justinchuby.
- **[facebook/lexical#9108](https://github.com/facebook/lexical/pull/9108)** Skip the sibling walk when no selection point reads the index.<br>
  Pasting a big block walked the whole sibling list on every insert, so paste time grew quadratically. The maintainer then carried the same guard into three more code paths.
- **[microsoft/playwright#42365](https://github.com/microsoft/playwright/pull/42365)** Drop the backend after `browser_close` with a shared browser.<br>
  Calling `browser_close` on a shared browser context left a dead backend cached in the MCP server, so every later tool call from that client failed until a restart.
- **[apple/coremltools#2845](https://github.com/apple/coremltools/pull/2845)** Fix unary `torch.einsum` with an empty output subscript.<br>
  Any single input einsum that reduced to a scalar, a matrix trace included, couldn't convert to Core ML at all.
- **[cloudflare/workers-sdk#15320](https://github.com/cloudflare/workers-sdk/pull/15320)** Detect an installed secret tool on Linux regardless of its exit status.<br>
  That tool exits nonzero even on a plain version check, so Wrangler told Linux users who had it installed that it was missing.
- **[microsoft/kiota#8185](https://github.com/microsoft/kiota/pull/8185)** Read collections in the factory for a collection of a primitive union.<br>
  The generated TypeScript factory promised an array but read a single value, so the client generated from GitHub's own REST description didn't compile.

<details>
<summary><b>Merged PRs, by repo</b></summary>
<br>

**Microsoft (14)**
- microsoft/onnxscript · [#3009](https://github.com/microsoft/onnxscript/pull/3009) · [#3013](https://github.com/microsoft/onnxscript/pull/3013) · [#3024](https://github.com/microsoft/onnxscript/pull/3024) · [#3026](https://github.com/microsoft/onnxscript/pull/3026) · [#3035](https://github.com/microsoft/onnxscript/pull/3035) · [#3036](https://github.com/microsoft/onnxscript/pull/3036)
- microsoft/kiota · [#8101](https://github.com/microsoft/kiota/pull/8101) · [#8162](https://github.com/microsoft/kiota/pull/8162) · [#8164](https://github.com/microsoft/kiota/pull/8164) · [#8185](https://github.com/microsoft/kiota/pull/8185)
- microsoft/playwright · [#42365](https://github.com/microsoft/playwright/pull/42365)
- microsoft/typespec · [#11744](https://github.com/microsoft/typespec/pull/11744)
- microsoft/mssql-python · [#727](https://github.com/microsoft/mssql-python/pull/727)
- microsoft/vscode-cmake-tools · [#5047](https://github.com/microsoft/vscode-cmake-tools/pull/5047)

**Meta (12)**
- facebook/lexical · [#9091](https://github.com/facebook/lexical/pull/9091) · [#9097](https://github.com/facebook/lexical/pull/9097) · [#9099](https://github.com/facebook/lexical/pull/9099) · [#9104](https://github.com/facebook/lexical/pull/9104) · [#9108](https://github.com/facebook/lexical/pull/9108) · [#9116](https://github.com/facebook/lexical/pull/9116) · [#9118](https://github.com/facebook/lexical/pull/9118) · [#9122](https://github.com/facebook/lexical/pull/9122) · [#9130](https://github.com/facebook/lexical/pull/9130) · [#9131](https://github.com/facebook/lexical/pull/9131)
- facebook/stylex · [#1817](https://github.com/facebook/stylex/pull/1817) · [#1828](https://github.com/facebook/stylex/pull/1828)

**Cloudflare (2)**
- cloudflare/workers-sdk · [#15320](https://github.com/cloudflare/workers-sdk/pull/15320) · [#15382](https://github.com/cloudflare/workers-sdk/pull/15382)

**Apple, Azure, and AWS (1 each)**
- apple/coremltools · [#2845](https://github.com/apple/coremltools/pull/2845)
- Azure/azure-sdk-for-js · [#39704](https://github.com/Azure/azure-sdk-for-js/pull/39704)
- awslabs/mcp · [#4523](https://github.com/awslabs/mcp/pull/4523)

</details>

## Projects

**[SonoXR](https://github.com/Om-singhaI/sonoxr-hackathon)** · [live demo](https://sonoxr-frontend.vercel.app)<br>
Reconstructs a beating heart from an ordinary 2D ultrasound sweep and renders it in mixed reality on a Quest 3. It's calibrated to show what it can't see instead of inventing tissue. Python reconstruction pipeline, WebXR client with a browser fallback.

**[NCAA seed prediction](https://github.com/Om-singhaI/NCAA)**<br>
Predicts the Selection Committee's exact 1 to 68 seeding. Pairwise comparisons feed a Logistic Regression and XGBoost blend, then the Hungarian algorithm finds the globally optimal one team per seed assignment. **78.0% exact seed match.** A paper on it is under review.

**[Epiphany](https://github.com/Om-singhaI/Epiphany)**<br>
An autonomous data scientist. Drop in a dataset and it explores, forms hypotheses, checks them with real statistics, then trains and deploys a model. Built with Gemini 2.5 and Google ADK.

**[PLAYER 1001](https://github.com/Om-singhaI/player-1001)** · [play it](https://om-singhai.github.io/player-1001/)<br>
Live crowd play inside a video premiere. One HTML file, one stylesheet, one script. Zero dependencies, zero external requests, with reduced motion, keyboard, and screen reader paths.

## How I work

I reproduce the bug on `main` before I touch any code, and I chase the root cause, since the visible failure usually sits a layer or two above the real defect. Then I write the test and watch it fail. Once the fix is in, I revert only the source change and watch the test fail again, because a test that passes either way proves nothing.

<details>
<summary><b>How I pick what to work on</b></summary>
<br>

I skip `good first issue` on famous repos. Those get picked clean fast. I look for fresh, unassigned issues that come with a real reproduction. Before I write any code I check whether it's still broken on `main`, whether someone already has a PR open, and whether a maintainer called it intended behavior. Plenty of candidates die right there, and that's time saved. When the tracker runs dry, I read the source and probe for bugs nobody's reported yet. Some of my Lexical fixes started that way.

</details>

## What I'm building now

- **Soft wrap for Lexical code blocks**, with line numbers that follow each logical line. I've proposed it on [facebook/lexical#8459](https://github.com/facebook/lexical/issues/8459), and it's in progress.
- **An optional `RetryPolicy` for Microsoft's [mssql-python](https://github.com/microsoft/mssql-python) driver**, the feature I was assigned on [issue #682](https://github.com/microsoft/mssql-python/issues/682). It'll let apps retry transient connection failures without writing their own loop. [PR #751](https://github.com/microsoft/mssql-python/pull/751) is in progress.

## Say hi

I'm always happy to talk spatial computing, model export, or anything that renders, and if you're hiring for a software engineering role, I'd love to hear from you.

📫 [wengsinghal@gmail.com](mailto:wengsinghal@gmail.com) · GitHub [@Om-singhaI](https://github.com/Om-singhaI)
