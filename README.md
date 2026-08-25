# Spatial Computing, Graphics Tooling, and Open Source

![](https://github.com/Om-singhaI/Om-singhaI/blob/main/icons/header.png?raw=true)

I build **spatial computing systems** and contribute to the **graphics and machine learning libraries** underneath them. I design and 3D print my own VR headsets, and I work on the rendering, reconstruction and model export tooling that decides what actually reaches the display.

* 🥽   I design and print my own **VR headsets**, from lens housings and head straps through to the display driver side and the endless tuning of interpupillary distance nobody warns you about.
* 🫀   I built **SonoXR**, which reconstructs a beating heart from an ordinary 2D ultrasound sweep and renders it in mixed reality on a Quest 3, calibrated to show what it *cannot* see rather than quietly inventing tissue.
* 🔧   I contribute to production libraries at **Microsoft, Google, AWS, Meta, Cloudflare, Vercel, Firebase and Hugging Face**, mostly in the graphics, model export and developer tooling layers.
* 🧮   I work on **applied machine learning** where the constraint is interesting: constrained ranking with the Hungarian algorithm, agentic pipelines, ONNX model export and precision correctness.
* 🧪   Every fix I send ships with a regression test that **provably fails without the change**, because a test that passes either way proves nothing.
* 🎯   I care about the boring half of engineering: reproductions, root causes, and being the person a maintainer does not have to double check.

<details>
  <summary>Some things I have shipped~d~d</summary>
  <br>

* 🥇   **[microsoft/onnxscript#3009](https://github.com/microsoft/onnxscript/pull/3009)** — `aten::mean` silently ignored its `dtype` argument when called without `dim`, so a model asking for float64 got float32 back and lost precision on large sums. Merged by the PyTorch ONNX exporter lead.
* 🥇   **[cloudflare/workers-sdk#15320](https://github.com/cloudflare/workers-sdk/pull/15320)** — Wrangler detected `secret-tool` by exit status, but that binary exits nonzero on `--version`, so Linux users who had it installed were told it was missing.
* 🫀   **[SonoXR](https://github.com/Om-singhaI/sonoxr-hackathon)** — 2D ultrasound to a holographic cardiac volume you can walk around and slice with your hands. Python reconstruction pipeline, WebXR client with a browser fallback. **[Live](https://sonoxr-frontend.vercel.app)**
* 🏀   **[NCAA seed prediction](https://github.com/Om-singhaI/NCAA)** — predicting the Selection Committee's exact 1 through 68 seeding. Converts 68 point predictions into ~4,500 pairwise comparisons, blends Logistic Regression and XGBoost, then applies the **Hungarian algorithm** so one team per seed is satisfied by globally optimal assignment. **91.2% exact match**, RMSE 0.392.
* ✦   **[Epiphany](https://github.com/Om-singhaI/Epiphany)** — an autonomous data scientist. Drop in a dataset, it explores, forms hypotheses, validates them with real statistics, trains a model and deploys it. Gemini 2.5 and the Google Agent Development Kit.
* 🎮   **[PLAYER 1001](https://github.com/Om-singhaI/player-1001)** — live crowd play inside a video premiere. One HTML file, one stylesheet, one script, **zero dependencies and zero external requests**, with reduced motion, keyboard and screen reader paths throughout. **[Play it](https://om-singhai.github.io/player-1001/)**

<br>

* 🔎   **How I find work worth doing:**

<br>

Labels like `good first issue` on famous repositories are mostly farmed. What works better is recently created, zero comment, unassigned issues carrying a real reproduction. Then, before writing any code: is it still broken on `main`, has someone already opened a competing PR, and did a maintainer call it intended behaviour? Roughly a third of candidates die at that step, which is a third of the time saved.

The rest is unglamorous. Find the root cause rather than the symptom, since the visible failure is usually a layer or two above the actual defect. Write the test first and watch it fail. Then revert only the source change and watch it fail again. That last step has caught fixes of mine that passed their own test while not actually fixing the reported bug.

</details>

<hr>
<p align="center">
  <i>Open to software engineering roles. Happy to talk about spatial computing, model export, or anything that renders.</i>
</p>

<p align="center">
<a href="mailto:wengsinghal@gmail.com"><img src="https://img.icons8.com/material-outlined/30/000000/new-post.png"/></a>
<a href="https://github.com/Om-singhaI?tab=repositories"><img src="https://img.icons8.com/material-outlined/27/000000/code-file.png"/></a>
<a href="https://sonoxr-frontend.vercel.app"><img src="https://img.icons8.com/material-outlined/30/000000/virtual-reality.png"/></a>
<a href="https://om-singhai.github.io/player-1001/"><img src="https://img.icons8.com/material-outlined/27/000000/geography.png"/></a>
</p>

<p align="center">
<img src="https://visitor-badge.laobi.icu/badge?page_id=Om-singhaI.Om-singhaI" alt="visitor badge"/>
</p>
