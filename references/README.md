# References

このディレクトリは、論文執筆で参照する資料の置き場である。

## 運用方針

- PDF本体は `references/pdf/` に置く。
- PDF本体はGit管理しない。ファイルサイズ・著作権・複数PC間同期の都合があるため、`references/pdf/*.pdf` は `.gitignore` の対象にしている。
- PDFから読んだ論点、ページ、本文での使い方は、Git管理されるMarkdownに残す。
- 文献表・引用形式を整える段階で、必要なら `references/metadata/` にCSVまたはBibTeXを作る。

## PDFファイル名

原則として、PDF名は次の形式にする。

```text
発行主体_資料名_年.pdf
```

例:

```text
国交省_インフラメンテナンス包括的民間委託導入の手引き_2023.pdf
四国地方整備局_橋梁補修工事発注留意事項案_2019.pdf
FHWA_Project_Bundling_Factsheet.pdf
```

年が不明な資料、会議資料、タイトルが長すぎる資料は、本文確認時に識別しやすい名前を優先する。

## 主要な整理先

- `notes/procurement_bundling_issues.md`: 契約バンドリング、発注効率化、距離制約、対象範囲の根拠整理。
- `paper/objective_design.md`: 目的関数として何を扱うかの設計判断。
- `paper/methodology.md`: 数理モデル・最適化・シナリオ設定。
