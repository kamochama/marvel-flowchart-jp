# Marvel Library v5 全作品接続監査・最終報告（2026-09-03）

## 結論

131作品・361作品ペア・569理由を、canonical facts、evidence/review provenance、SQLite/CSV/JSON parity、Chrome/CDPの実操作まで独立に監査した。構造的な欠落・孤児・逆向き・不正なtransition fan-outは0件だった。したがって、今回の範囲で「導出器の修正が必要な線不足」は確認されていない。

ただし、根拠の完全性は別問題である。source-verifiedで保持できる理由は15、legacy_seed由来で根拠待ちの理由は554、意図的に未materializeとしたものは12である。線を消さず、根拠レベルと表示意味を分離した。

## 実施済み

- `scripts/library_v5/connectivity_audit.py` を追加。R/A/E/C/Pの独立監査、131作品在庫、361ペア在庫、provenance、cycle、reason orphan、transition境界を検査。
- `tests/library_v5/test_connectivity_audit.py` と `test_connectivity_projection_contract.py` を追加。RED（監査器未実装）から開始し、GREENを確認。
- 全ライブラリテスト: **434 passed / 4 skipped**。
- bundled Python build: **成功**（audit issue 0、content-audit issue 0、FK 0、SQLite integrity `ok`）。
- 正本CSV・persistent review ledgerは変更なし。

## 残課題

- 154件のlegacy explicit relationと400件のlegacy shared appearanceは、個別公式ソースを揃えるまでsemantic predecessorとして確定しない。
- Logan/WolverineとLokiのvariant fan-outは個体根拠が必要。現段階で推測分割しない。
- degree 0の8作品は、タイトル類似や同一フランチャイズだけで線を足さず、追加ソースが得られた場合に別バッチで扱う。

## 統合状態

本監査ブランチには、現行公開`main`（`30ffbbf9de9624b644f8c267d1543347a273948c`）を取り込み済み。今回の成果は監査器・テスト・レビュー文書のみで、canonical graphや公開HTMLの意味を変更していない。公開反映は、次の意味修正バッチを別計画で実施し、再監査を通過してから行う。
