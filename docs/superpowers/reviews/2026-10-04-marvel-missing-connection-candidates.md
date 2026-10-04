# Missing connection candidates — not final whole-work audit

Baseline: `5e44ae2402816c9101034f3198d4d1571a64f7c3`, 131 works / 355 directed edges / 562 reasons. Independent research is incomplete; present graph membership is not an oracle of correctness.

## Main-agent checked candidate: Trevor's path into Wonder Man

Primary source: https://www.disneyplus.com/en-sg/explore/articles/marvels-wonder-man (6 February 2026), section **Sir Ben Kingsley as Trevor Slattery**, with MCU-series confirmation in its separate MCU section. The article explicitly follows Trevor's terrorist role in Iron Man 3, imprisonment in All Hail the King and Ta Lo adventure in Shang-Chi into his return to Hollywood in Wonder Man. The comics-only sections are excluded.

At the research baseline, main-agent exact-target checks with Import-Csv returned no `work_relations.csv` or `work_edges_all.csv` rows targeting `wonder-man-s1-2026`. Existing appearances/portrayals also did not register this continuation. On 5 October 2026 the separate `codex/wonder-man-predecessor` branch implements only the narrowed Shang-Chi candidate; it is not yet production-integrated. The other two pairs remain held.

| Source work | Target work | Proposed scope | Current pair |
| --- | --- | --- | --- |
| `all-hail-the-king-2014` | `wonder-man-s1-2026` | Trevor's explicitly recalled imprisonment history into Hollywood return | absent |
| `iron-man-3-2013` | `wonder-man-s1-2026` | Trevor's explicitly recalled former role into Hollywood return | absent |
| `shang-chi-and-the-legend-of-the-ten-rings-2021` | `wonder-man-s1-2026` | Trevor's explicitly recalled Ta Lo adventure into Hollywood return | absent |

The independent reviewer initially identified the first pair. Main-agent primary reading identifies the other two as separate candidates in the same exact passage. Review the appropriate relation kind, direction, full note and UI/export effect in a separate new-fact correction plan with RED/GREEN tests. Do not invent character appearance, identity, chronology, membership or event rows to achieve these connections. The article's Agent Cleary return statement is a separate candidate requiring its own interpretation; it is not included automatically.

## Ordinary ChatGPT review and narrowed correction

2026-10-04: Ordinary ChatGPT independently read the article and recommended adding only `shang-chi-and-the-legend-of-the-ten-rings-2021 -> wonder-man-s1-2026`: story_link/story/indirect/same_or_intended/probable, with one exact primary evidence and created_verified review. Main agent accepts this narrower correction: the text describes a continuous history, not three independent direct predecessor assertions. The existing Iron Man 3 -> All Hail the King -> Shang-Chi path should remain the upstream chain; the All Hail -> Shang-Chi seed needs its own exact full-note source audit. The other two long-range candidate pairs are held, not implemented or treated as confirmed omissions. This interpretation preserves the user's request for predecessor flow through intermediate works rather than manufacturing shortcuts.

Expected topology impact is one new pair/reason, subject to measurement; no count guard is weakened in advance. Exact new-fact RED/GREEN, complete export comparison, independent/ChatGPT implementation review and all-work real-Chrome selection parity are required before integration. This design is part of the approved missing-line correction scope, not a new UI mode.

## Research limitations

The middle partition (ASCII work IDs 44–87) subsequently covered all 44 IDs but fully read primary context for only 13, partially read three, and left 28 without new primary reading. Its final report correctly kept every work `research_open`. It also suggested Vol.2 → Vol.3 from Disney's trilogy language; this is an unadopted candidate pending main-agent primary reread and analysis of the existing Vol.2 → Holiday Special → Vol.3 path, not an automatically confirmed missing edge. Its Wonder Man directness suggestion is not adopted: the narrowed plan retains `indirect` and avoids claiming a direct sequel.

Main-agent follow-up primary reading: D23's `https://d23.com/exploring-shang-chis-ties-to-the-larger-mcu/` and Disney News's `https://news.disney.com/marvel-studios-shang-chi-and-the-legend-of-the-ten-rings-cast-crew-interview` identify Trevor's return and the Ten Rings context but do not explicitly name the All Hail the King predecessor in their inspected text. They are not sufficient alone to close the existing All Hail → Shang-Chi full-note audit. D23's description of who hired the fake Mandarin also requires cross-checking; do not propagate that incidental claim into canonical facts merely because the host is official. That source investigation remains open.

The first independent missing-line partition compared 44 work IDs but many rows use existing relations or incomplete source rereads. Those rows remain research_open, not source-backed no-gap conclusions. Its statement that current edges were treated as correct was contrary to the instruction and was explicitly rejected. Further work-specific independent primary research is required across all 131 works. Dark Phoenix -> Deadpool & Wolverine remains unconfirmed; the inspected generic synopsis does not establish that exact endpoint.
