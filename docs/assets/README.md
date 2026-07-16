# Public image specifications

The public README uses these three human-reviewed figures, in this order:

1. `maieusis-question-development.png` — the end-to-end question-development
   flow and its plan/reject/defer/warning closure;
2. `maieusis-positioning-map.png` — the audited two-axis related-work map;
3. `maieusis-paperbank-pattern-induction.png` — how reviewed paper cases become
   reusable, source-bound question-forming patterns.

All three native PNGs are **3840 × 2160 px**. Their cleaned, canonical HTML
sources remain in the private development truth; the public projection ships
only the PNGs, alt text, captions, and positioning evidence.

| Asset | SHA-256 |
| --- | --- |
| `maieusis-question-development.png` | `9df06c89a7bbbe6c92fdc7b8f7be440cfc75fbd23ef37c8f98371ca4177c39cf` |
| `maieusis-positioning-map.png` | `28bd2f181805eab20cdaf65d965363828b79ccb89b8c31e1f8bd80422bde9e4f` |
| `maieusis-paperbank-pattern-induction.png` | `311a15deffb49748397f89249125786f5787ce77dc1914c81325b1dfdca05990` |

Before release, verify dimensions and hashes, inspect every PNG at full size,
check the README alt text and captions, and confirm that no earlier project
name remains visible or embedded in the canonical source.

Extended attributes are a local intake concern and are not stored by Git. The
release archive gate rejects AppleDouble/download-metadata files and verifies
the byte hashes above; no HTML source or local filesystem metadata is shipped.
