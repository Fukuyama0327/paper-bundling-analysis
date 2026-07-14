# Introduction — 下書き（日本語）

> **方針メモ**
> - 国際誌向け。流れ：バンドリング → 分散管理の障壁 → 広域連携・地域分割 → ギャップ → 貢献
> - サブセクション見出しは付けない。見出しなしの1本の文章として構成する（2026-07-11 決定）。
> - リサーチギャップは宣言のみ（根拠は既往研究章で展開）。
> - 新規性・貢献は末尾に明示。
> - フランスの話は入れない。
> - 「群マネの理念に沿って」は使わない。

---

複数の橋梁補修案件を単一契約にまとめる契約バンドリング（contract bundling）は，個別に発注される複数の案件を一つの契約単位に集約する手法である．米国連邦道路局（Federal Highway Administration: FHWA）は，類似案件のバンドリングが，規模の経済によるコスト削減や調達手続の効率化に寄与するとしている（FHWA, 2020）．本研究では，これらの効果のうち，補修需要をより少ない契約単位に集約できる可能性に着目する．

バンドリングの機会は，契約対象とし得る範囲内で，同じ期間に補修を必要とする橋梁がどの程度発生するかに依存する．橋梁が複数の管理主体に分散している場合，地理的に近接する補修需要であっても，既存の行政界が契約対象の組合せを制約し得る．

日本では，市区町村がそれぞれの管理する橋梁について補修工事を発注している．管理主体ごとに発注する場合，同一契約に含め得る橋梁の範囲は，原則として各主体の管理区域に限定される．このため，管理橋梁数が少ない主体ほど，同一期間に発生する補修需要を一つの契約に集約する機会が限られる．また，共同発注等を行わない限り，地理的に近接する橋梁であっても，管理主体が異なれば別々の契約として扱われる．

この問題への対応として，複数の管理主体が行政界を越えて連携し，橋梁群を一体的に管理・発注することが考えられる．米国Nebraska州では，個々の郡では橋梁バンドリングの便益を十分に得られない場合があることから，複数郡が行政界を越えて橋梁を一つの事業に集約する取組が実施されている（FHWA, 2019）．

日本では，国土交通省が「地域インフラ群再生戦略マネジメント（群マネ）」を推進し，自治体の枠を越えた広域連携をその一類型として示している（国土交通省, 2025）．

しかし，複数自治体の橋梁を一体的に管理・発注する場合に，どのように管理エリアを設計すれば契約バンドリングによる契約集約効果を最大化できるかは，明らかになっていない．

地域分割（districting）研究は，地理的な基本単位を複数の地区へ編成するための一般的な方法を提供してきたが，その主な評価基準は地区の連続性，コンパクト性，負荷均衡などであり，確率的に発生する橋梁補修需要の契約集約効果を扱っていない（Kalcsics and Rios-Mercado, 2019）．一方，契約バンドリング研究は，あらかじめ与えられた事業群から契約ロットを構成する問題を扱っており，劣化過程から補修需要の発生を内生化するとともに，管理エリア自体を設計する枠組みには至っていない（Qiao et al., 2026）．

本研究は，確率的劣化に伴う補修需要と契約バンドリングルールを統合した地域分割最適化モデルを構築し，広域連携による契約集約効果を定量的に評価することを目的とする．本研究の貢献は3点ある．第一に，管理エリアの空間設計と契約ロットの集約を同一の数理的枠組みで定式化する．第二に，マルコフ劣化モデルから導かれる補修需要確率を地域分割問題に組み込み，将来の補修需要を内生化する．第三に，地域内橋梁数 $N$ と一契約当たりの同時発注上限 $L$ を引数とする期待契約件数の閉形式 $f(N,L)$ を導出し，バンドリング効果を解析的に評価可能にする．宮城県内の実橋梁データを用いた数値実験により，地域数および地域内の距離制約が期待契約件数に与える影響を明らかにする．

---

> **残課題・確認事項**
> - 「プロジェクトリストを所与とする既存研究」という指摘は、既往研究章でQiaoらの限界として詳述する。Introductionでは代表文献1件によるギャップ宣言にとどめる。
> - 貢献③の「シミュレーションによらず」という主張：従来の期待契約件数がシミュレーション推定だったことの説明は、モデル章で行う。
> - FHWA (2020) が直接支持するのは、規模の経済、調達時間短縮、設計・施工の効率化、材料単価低減。受注者の「安定的な事業量確保」は同資料から確認できないため削除した。
> - FDOTのDistrict別橋梁数から「バンドリング条件を自然に満たす」とする推論、日本の自治体平均橋梁数、「一補修サイクル1〜2橋」、および「世界各地で共通」とする一般化は、確認した出典が直接支持しないため削除した。国外との共通性は、FHWAのNebraska複数郡バンドリング事例が直接支える範囲に限定して記述した。
> - 四国地方整備局（2019）が直接示すのは、遠距離多数橋の一括発注に関する留意事項と「最も離れた橋梁間の最大距離を50 km程度まで」とする実務目安であり、「一補修サイクル1〜2橋」の根拠ではない。
> - サブセクション見出しは付けず、見出しなしの1本の文章に統合済み。

---

## References in this section

本文中の引用と LaTeX `\bibitem` キーの対応表。

| 番号 | 本文中の表記 | `\bibitem` キー | 書誌情報 |
|---|---|---|---|
| [1] | FHWA, 2020 | `fhwafactsheet` | FHWA: Project Bundling Fact Sheet (EDC-5), Federal Highway Administration, U.S. Department of Transportation, 2020. |
| [2] | FHWA, 2019 | `fhwa2019` | FHWA: Bridge Bundling Guidebook: An Efficient and Effective Method for Maintaining and Improving Bridge Assets, Federal Highway Administration, U.S. Department of Transportation, 2019. |
| [3] | 国土交通省, 2025 | `mlit2025gunmane` | 国土交通省：地域インフラ群再生戦略マネジメント手引き Ver.1，2025年10月. |
| [4] | Kalcsics and Rios-Mercado, 2019 | `kalcsics2019` | Kalcsics, J. and Rios-Mercado, R. Z.: Districting Problems, Location Science, Springer International Publishing, pp.705--743, 2019. |
| [5] | Qiao et al., 2026 | `qiao2026` | Qiao, J. Y., Guo, Y., Seilabi, S., Fricker, J. D. and Labi, S.: A proposed algorithm for identifying heuristic-optimal bundling strategies, Computer-Aided Civil and Infrastructure Engineering, Vol.49, 100100, 2026. |

---

## Source evidence

本文中の各引用がどの主張を支えるかを監査するための記録。原文は必要最小限のみ転記し、ページ番号と判断を併記する。原典本文を未確認の文献については、レビュー資料の要約を原文として扱わず、確認状況を明示する。

### [1] FHWA (2020) — Project Bundling Fact Sheet

- **本文で支える主張**: バンドリングによる調達時間の短縮、設計・施工の効率化、規模の経済、材料単価の低減。
- **原文（p.1）**:

> “Economies of scale to increase efficiency.”

> “Bundling design and construction contracts saves procurement time.”

> “Bundling multiple projects can lower the unit cost for materials.”

- **判断**: 現在の本文を直接支持する。
- **原典**: `references/pdf/FHWA_Project_Bundling_Factsheet.pdf`

### [2] FHWA (2019) — Bridge Bundling Guidebook

- **本文で支える主張**: 米国でも地方公共機関が管理する橋梁が存在し，個々の郡ではバンドリングの便益を得にくい場合に，複数郡が行政界を越えて橋梁を束ねる取組が行われていること。
- **原文（Appendix C, p.179）**:

> “Although each county alone may not have the means to reap the benefits of a bridge bundle, by working collaboratively, counties have that ability.”

- **判断**: Nebraska DOTのCounty Bridge Match Programについて，個々の郡だけではバンドリングの便益を得にくい場合と，郡同士の連携によってその制約を補えることを直接支持する。同頁は，別々の郡にある橋梁を一事業に束ねることを制度として認め，奨励していることも明記している。
- **原典**: https://www.fhwa.dot.gov/ipd/pdfs/alternative_project_delivery/bridge_bundling_guidebook_070219.pdf
- **補助確認**: https://www.fhwa.dot.gov/ipd/alternative_project_delivery/defined/bundled_facilities/case_study_ndot_county_bridge_match.aspx

### [3] 国土交通省 (2025) — 群マネの手引き Ver.1

- **本文で支える主張**: 群マネの定義、自治体の枠を越えた広域連携、共同発注・契約一本化という連携形態。
- **原文（p.7）**:

> 「複数自治体のインフラや複数分野のインフラを『群』として捉えることで、効率的・効果的にマネジメントしていく取組」

- **原文（p.9–10）**:

> 「自治体の枠を越えてマネジメントする『広域連携の群マネ』」

> 「代行パターン（他自治体分も含めて、契約は一本化）」／「共同発注パターン」

- **判断**: 現在の本文を直接支持する。「政策目標として掲げる」よりも、資料自身の定義に沿って「推進している」「連携形態が示されている」と書く方が正確。
- **原典**: `references/pdf/国交省_地域インフラ群再生戦略マネジメント手引き_本編.pdf`

### [4] Kalcsics and Rios-Mercado (2019) — Districting Problems

- **本文で支える主張**: districtingの一般的枠組みと、連続性・コンパクト性・負荷均衡等の代表的評価基準。
- **原文**: **原典本文未確認**。現在リポジトリにあるのは調査メモのみで、原著の引用可能な原文とページ番号は未収録。
- **暫定的な確認元**: `references/pdf/調達バンドリング_勉強/District Optimization (Districting Problem) の理論的位置付けと橋梁補修契約バンドリング研究への接続可能性.md`
- **要対応**: main.texへ反映する前に原著を確認し、定義または代表的評価基準を示す原文とページ番号を記録する。

### [5] Qiao et al. (2026) — A proposed algorithm for identifying heuristic-optimal bundling strategies

- **本文で支える主張**: 与えられた道路事業群を組み合わせてbundleを構成する問題であり、確率的劣化による需要発生と管理エリア設計を同時には扱わないこと。
- **原文**: **原典本文未確認**。現在リポジトリにあるのは論文レビューであり、原著の引用可能な原文とページ番号は未収録。
- **暫定的な確認元**: `references/qiao2026_review.md`
- **要対応**: main.texへ反映する前に、入力となるproject set、意思決定変数、問題設定を示す原文を確認する。論文に明記されない「扱っていない事項」は、方法・定式化全体を確認した上で著者側の比較判断として記述する。
