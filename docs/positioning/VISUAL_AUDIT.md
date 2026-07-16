# Visual audit requirements

- Native size: **3840 × 2160 px**.
- GitHub preview: responsive 16:9 scaling from the native asset.
- Use broad bands to avoid false numerical precision.
- Represent every audited work with a numbered marker and short label.
- Distinguish systems/methods, benchmarks/datasets, and end-to-end pipelines.
- Keep labels readable and outside dense category boxes.
- State on the image that it is a conceptual task-design map, not a performance
  ranking.
- Display **Maieusis** and no earlier project name.
- Verify the final PNG visually; do not infer correctness from HTML or SVG
  source text alone.

The reviewed image is `../assets/maieusis-positioning-map.png`; its canonical
HTML source is retained development-side under `docs/release/figures/`.
Regenerate hashes in `../assets/README.md` after any redraw.
