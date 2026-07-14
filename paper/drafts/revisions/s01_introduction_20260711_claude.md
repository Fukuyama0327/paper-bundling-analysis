# Introduction — 下書き（日本語）

> **退避情報**
> - 2026-07-11にClaude Coworkから引き継いだ旧稿。
> - GPTによる全面改稿直前の内容を会話記録から復元して保存。
> - 現在の作業版は `paper/drafts/s01_introduction.md`。

> **方針メモ**
> - 国際誌向け。流れ：バンドリング → 分散管理の障壁 → 広域連携・地域分割 → ギャップ → 貢献
> - サブセクション見出しは付けない。見出しなしの1本の文章として構成する（2026-07-11 決定）。
> - リサーチギャップは宣言のみ（根拠は既往研究章で展開）。
> - 新規性・貢献は末尾に明示。
> - フランスの話は入れない。
> - 「群マネの理念に沿って」は使わない。

---

橋梁補修工事の発注において，公告・積算・入札・監督・検査といった契約事務は，契約1件ごとに繰り返し発生する固定的なコストを伴う．受注者側においても，見積・入札・現場動員の固定負担が契約単位ごとに生じる．こうした固定費を削減する手段として，複数の補修案件を単一契約に集約して発注する「契約バンドリング（contract bundling）」が有効とされており，規模の経済による単価削減や受注者の安定的な事業量確保といった効果が報告されている（FHWA, 2020; Qiao, 2019）．

バンドリングの効果が発現するには，一定期間内に複数の補修需要が同時に，かつ同一の管理エリア内で発生することが前提となる．米国では各州の道路局（State DOT）が内部を地区（District）に分割して橋梁を管理しており，一Districtあたり数百から千橋以上を管轄することで，こうした条件を自然に満たしている（FDOT, 2021）．

一方，日本の市区町村のような小規模な地方行政主体が個別に橋梁管理を行う場合，一自治体の管理橋梁数は平均50〜150橋程度にとどまる（国土交通省, 2025）．この規模では，一補修サイクルで対象となる橋梁が1〜2本にとどまることが多く，同一契約に束ねる余地が生まれにくい（四国地方整備局, 2019）．さらに，地理的に近接した橋梁であっても行政界が異なれば別々の契約として発注されるため，近接需要の集約によるバンドリング効果が活かされない．こうした小規模主体における管理スケールの制約は，日本に限らず，米国の農村部郡（County）や欧州の基礎自治体など，世界各地で共通して確認されている課題である（FHWA, 2020）．

この問題への対応として，複数の小規模主体が行政界を越えて連携し，橋梁群を広域的に一括管理する体制が各国で検討されている．日本では国土交通省が「地域インフラ群再生戦略マネジメント（群マネ）」を推進し，市区町村の枠を超えた広域連携体制の構築を政策目標として掲げている（国土交通省, 2025）．

広域連携によって複数自治体の橋梁を一括管理する場合，どのように管理エリアを設計すれば契約バンドリングによる発注効率が最大化されるかは，未解決の問いである．

地域分割（districting）に関する既往研究（Webster, 2013; Kalcsics and Rios-Mercado, 2019）は，選挙区割りや物流配送を対象としており，橋梁補修の契約集約効果を目的関数に組み込む枠組みを提供していない．一方，契約バンドリングの研究（Qiao et al., 2026; Assaf and Assaad, 2023）は，補修プロジェクトが既知として与えられる状況を前提としており，確率的劣化によって補修需要が将来にわたって不確実に発生する過程を扱っていない．また，管理エリアの設計自体を意思決定の対象としていない．

本研究は，確率的劣化に伴う補修需要の発生と契約バンドリングルールを統合した地域分割最適化モデルを構築し，広域連携による発注効率改善効果を定量的に評価することを目的とする．

本研究の主な貢献は以下の3点である．

**貢献①**: 地域分割問題と契約バンドリング最適化の統合的定式化．管理エリアの空間設計と発注集約の両方を同一の数理的枠組みで扱う．

**貢献②**: マルコフ劣化モデルに基づく補修需要の確率的内生化．プロジェクトリストを所与とする既存研究と異なり，補修需要の発生確率をマルコフ推移確率から導出してモデルに組み込む．

**貢献③**: 閉形式の期待契約件数関数 $f(N, L)$ の導出．地域内橋梁数 $N$ と同時発注上限 $L$ を引数にとる解析的な関数式を理論的に導くことで，シミュレーションによらずバンドリング効果の感度分析が可能となる．

宮城県内の実橋梁データを用いた数値実験を通じて，提案モデルの有効性を検証し，距離制約と地域数の変化が発注効率に与えるトレードオフを定量的に評価する．

---

> **残課題・確認事項**
> - 貢献②の「プロジェクトリストを所与とする既存研究」という指摘は、既往研究章でQiaoらの限界として詳述する。ここでは宣言のみ。
> - 貢献③の「シミュレーションによらず」という主張：従来の期待契約件数がシミュレーション推定だったことの説明は、モデル章で行う。
> - FDOT (2021) は現在 main.tex の参考文献リストに未収録。main.tex統合時に `\bibitem` を追加する必要がある。
> - 要確認：main.tex本文では同じ「State DOT District 800〜1,300橋」の記述に `fhwa2019`（FHWA Bridge Bundling Guidebook, 2019）を出典として使っている。本ドラフトの「一Districtあたり数百〜千橋以上」という記述も、FDOT (2021) ではなく `fhwa2019` に統一すべきか、それとも別々の一次資料として両方残すか、main.tex統合時に要判断。
>
> **解決済み（2026-07-11）**
> - 冒頭の老朽化インフラ文献 → ASCE 2021 Infrastructure Report Card (Bridges) を採用（本文・下記参照表に反映済み）。
> - サブセクション見出しは付けず、見出しなしの1本の文章に統合済み。

---

## References in this section

本文中の引用と LaTeX `\bibitem` キーの対応表。

| 番号 | 本文中の表記 | `\bibitem` キー | 書誌情報 |
|---|---|---|---|
| [1] | ASCE, 2021 | `asce2021bridges` | American Society of Civil Engineers: 2021 Report Card for America's Infrastructure — Bridges, ASCE, Reston, VA, 2021. https://infrastructurereportcard.org/cat-item/bridges-infrastructure/ |
| [2] | FHWA, 2020 | `fhwafactsheet` | FHWA: Project Bundling Fact Sheet (EDC-5), Federal Highway Administration, U.S. Department of Transportation, 2020. |
| [3] | Qiao, 2019 | `qiao2019` | Qiao, Y.: Bundling effects on contract performance of highway projects: quantitative analysis and optimization framework, Ph.D. Dissertation, Purdue University, 2019. |
| [4] | FDOT, 2021 | **未登録**（要追加） | FDOT: Bridge Inventory 2021 Annual Report, Florida Department of Transportation, 2021. https://fdotwww.blob.core.windows.net/sitefinity/docs/default-source/maintenance/str/bi/annual_rpt_21.pdf |
| [5] | 国土交通省, 2025 | `mlit2025gunmane` | 国土交通省：地域インフラ群再生戦略マネジメント手引き Ver.1，2025年10月. |
| [6] | 四国地方整備局, 2019 | `shikoku2019` | 四国地方整備局：橋梁補修工事発注に際しての留意事項（案），2019年8月. |
| [7] | Webster, 2013 | `webster2013` | Webster, G. R.: Reflections on current criteria to evaluate redistricting plans, Political Geography, Vol.32, No.1, pp.3--14, 2013. |
| [8] | Kalcsics and Rios-Mercado, 2019 | `kalcsics2019` | Kalcsics, J. and Rios-Mercado, R. Z.: Districting Problems, Location Science, Springer International Publishing, pp.705--743, 2019. |
| [9] | Qiao et al., 2026 | `qiao2026` | Qiao, J. Y., Guo, Y., Seilabi, S., Fricker, J. D. and Labi, S.: A proposed algorithm for identifying heuristic-optimal bundling strategies, Computer-Aided Civil and Infrastructure Engineering, Vol.49, 100100, 2026. |
| [10] | Assaf and Assaad, 2023 | `assaf2023` | Assaf, G. and Assaad, R. H.: Key decision-making factors influencing bundling strategies: analysis of bundled infrastructure projects, Journal of Infrastructure Systems, Vol.29, No.2, 2023. |
