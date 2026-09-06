# Third-Party Notices

This project incorporates workflow concepts and may incorporate adapted implementation material from the following MIT-licensed projects.

## codex-ppt-skill

- Project: `ningzimu/codex-ppt-skill`
- URL: https://github.com/ningzimu/codex-ppt-skill
- Upstream commit reviewed: `f2ed80372f65bb05fe62dd07979b239a17ac065d`
- Commit retrieval date: 2026-08-24
- License: MIT
- Copyright: Copyright (c) 2026 ningzimu
- Local license copy: `LICENSES/codex-ppt-MIT.txt`

Concepts referenced or adapted include outline-first deck planning, per-slide design jobs, full-slide image generation, worker dispatch, run-state recording, visual review, and deck assembly discipline.

## image-to-editable-ppt-skill

- Project: `ningzimu/image-to-editable-ppt-skill`
- URL: https://github.com/ningzimu/image-to-editable-ppt-skill
- Upstream commit reviewed: `fb869763127fd31ba7288d905671ffc4ea542f60`
- Commit retrieval date: 2026-08-24
- License: MIT
- Copyright: Copyright (c) 2026 ningzimu
- Local license copy: `LICENSES/image-to-editable-ppt-MIT.txt`

Concepts referenced or adapted include page-level reconstruction, editable object decisions, page manifests, worker isolation, deterministic record/finalize states, and final structural validation.

## Modifications

The combined workflow changes the upstream purposes and sequencing:

- Huawei internal-report writing and visual rules are authoritative.
- Every slide is first mapped to a page in the user-provided Huawei template library.
- Image2 creates a full-slide design blueprint rather than the final image-only deck.
- Accepted designs are reconstructed as editable PowerPoint objects.
- Only the complete outline is a default user approval gate; downstream work continues automatically unless checkpoints are requested.
- The legacy editable-title/static-middle-image/editable-conclusion workflow is not used.

The upstream projects do not endorse this derivative workflow. Their MIT licenses are reproduced in `LICENSES/`.

## Huawei Template Asset

`assets/huawei-template/PPT模板.pptx` is a user-provided internal template asset. It is not covered by either upstream MIT license. See `assets/huawei-template/NOTICE.md`.

## User-provided insight report examples

`assets/insight-reference/` contains 24 raster page excerpts from four user-provided MWC / Google IO PDF reports, plus a reference PPTX and a provenance catalog. These materials are for the user's internal reference and do not inherit this repository's code licenses. Source filenames, physical page numbers and SHA-256 hashes are recorded in the catalog. Do not publish or redistribute the reference assets automatically.
