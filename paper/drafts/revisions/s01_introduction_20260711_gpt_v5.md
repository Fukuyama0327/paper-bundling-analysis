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

バンドリングの機会は，契約対象とし得る範囲内で，同じ期間に補修を必要とする橋梁がどの程度発生するかに依存する．日本では，市区町村がそれぞれの管理する橋梁について補修工事を発注しているため，同一契約に含め得る橋梁の範囲は，原則として各主体の管理区域に限定される．このため，管理橋梁数が少ない主体ほど，同一期間に発生する補修需要を一つの契約に集約する機会が限られる．また，地理的に近接する橋梁であっても，管理主体が異なれば，通常は同一契約の対象とならない．

この問題への対応として，複数の管理主体が行政界を越えて連携し，橋梁群を一体的に管理・発注することが考えられる．米国Nebraska州では，個々の郡では橋梁バンドリングの便益を十分に得られない場合があることから，複数郡が行政界を越えて橋梁を一つの事業に集約する取組が実施されている（FHWA, 2019）．

日本では，国土交通省が「地域インフラ群再生戦略マネジメント（群マネ）」を推進し，自治体の枠を越えた広域連携をその一類型として示している（国土交通省, 2025）．

しかし，複数自治体の橋梁を一体的に管理・発注する場合に，どのように管理エリアを設計すれば，地理的制約の下で期待契約件数を最小化できるかは，明らかになっていない．

この問いは，橋梁の劣化モデル，地域分割，道路インフラ事業の契約バンドリングという三つの研究領域にまたがる．橋梁の劣化モデル研究では，不確実性を伴う劣化予測に基づく維持管理計画が研究されてきた（Hadjidemetriou et al., 2020）．地域分割研究では，地理的な基本単位を複数の地区へ編成するための方法が体系的に研究されてきた（Kalcsics and Rios-Mercado, 2019）．一方，道路インフラ分野の契約バンドリング研究は，あらかじめ選定された事業群から契約ロットを構成する方法を扱っている（Qiao et al., 2026）．しかし，確率的に発生する橋梁補修需要と契約バンドリングを結び付け，管理エリアの設計問題として扱う枠組みは，確認した範囲では示されていない．

本研究は，確率的劣化に伴う補修需要と契約バンドリングルールを統合した地域分割最適化モデルを構築し，広域連携による契約集約効果を定量的に評価することを目的とする．

本研究の主な貢献は以下の3点である．

**貢献①：確率的補修需要，契約バンドリング，地域分割の統合的定式化．** 劣化モデル研究，契約バンドリング研究，地域分割研究として個別に扱われてきた三つの問題を，橋梁補修の管理エリア設計という一つの最適化問題として統合する．

**貢献②：橋梁劣化データから調達評価への接続．** 点検データからマルコフ推移確率を推定し，補修需要の発生確率を導出するとともに，地域内橋梁数 $N$ と一契約当たりの同時発注上限 $L$ を引数とする期待契約件数の閉形式 $f(N,L)$ を構築する．これにより，確率的な補修需要を契約集約効果の評価指標へ変換し，地域分割最適化の目的関数に組み込む．

**貢献③：実橋梁データに基づく広域連携効果の定量評価．** 宮城県内の橋梁データを用いて，管理橋梁数，同時発注上限，地域数および距離制約が期待契約件数に与える影響を体系的に分析し，現行の管理単位との比較を通じて契約集約効果を示す．

---

> **残課題・確認事項**
> - 「プロジェクトリストを所与とする既存研究」という指摘は、既往研究章でQiaoらの限界として詳述する。Introductionでは代表文献1件によるギャップ宣言にとどめる。
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
| [4] | Hadjidemetriou et al., 2020 | `hadjidemetriou2020`（未登録） | Hadjidemetriou, G. M., Xie, X. and Parlikad, A. K.: Predictive Group Maintenance Model for Networks of Bridges, Transportation Research Record, Vol.2674, No.4, pp.373--383, 2020. https://doi.org/10.1177/0361198120912226 |
| [5] | Kalcsics and Rios-Mercado, 2019 | `kalcsics2019` | Kalcsics, J. and Rios-Mercado, R. Z.: Districting Problems, Location Science, Springer International Publishing, pp.705--743, 2019. https://doi.org/10.1007/978-3-030-32177-2_25 |
| [6] | Qiao et al., 2026 | `qiao2026` | Qiao, J. Y., Guo, Y., Seilabi, S., Fricker, J. D. and Labi, S.: A proposed algorithm for identifying heuristic-optimal bundling strategies, Computer-Aided Civil and Infrastructure Engineering, Vol.49, 100100, 2026. https://doi.org/10.1016/j.cacaie.2026.100100 |

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

### [4] Hadjidemetriou et al. (2020) — Predictive Group Maintenance Model for Networks of Bridges

- **本文で支える主張**: 不確実性を伴う橋梁劣化モデルを用いて，維持管理の優先順位・時期・グループ化を検討する研究領域が存在すること。
- **原文（Abstract）**:

> “The paper presents an approach that prioritizes the maintenance of MSMCN of bridges, using a deterioration model of components with uncertainty.”

- **判断**: 劣化予測と維持管理計画を接続する研究領域の代表例として本文を支持する。同研究のgroup maintenanceはsetup costの共有を扱うが，公共調達上の契約ロット設計を直接扱うものではない。この差異はSection 2で詳述する。
- **原典**: https://doi.org/10.1177/0361198120912226
- **著者公開版**: https://www.repository.cam.ac.uk/items/1227977e-b976-40cb-87e2-4050202a29a3

### [5] Kalcsics and Rios-Mercado (2019) — Districting Problems

- **本文で支える主張**: districtingでは，地理的な基本単位を複数の地区へ編成する問題が体系的に研究されていること。
- **原文（Abstract）**:

> “Districting is the problem of grouping small geographic areas, called basic units, into larger geographic clusters, called districts.”

- **判断**: 地理的な基本単位を複数の地区へ編成するという本文の分野説明を直接支持する。地区の連続性，コンパクト性，負荷均衡等の詳細はSection 2で原著本文に基づいて整理する。
- **原典**: https://doi.org/10.1007/978-3-030-32177-2_25
- **書誌・Abstract確認**: https://ideas.repec.org/h/spr/sprchp/978-3-030-32177-2_25.html

### [6] Qiao et al. (2026) — A proposed algorithm for identifying heuristic-optimal bundling strategies

- **本文で支える主張**: 与えられた道路事業群を組み合わせてbundleを構成する問題であり、確率的劣化による需要発生と管理エリア設計を同時には扱わないこと。
- **原文（Abstract）**:

> “This paper formulates project bundling as a combinatorial optimization problem and solves it using a greedy heuristic algorithm.”

- **判断**: 複数事業からbundleを構成する組合せ最適化問題を扱うことを直接支持する。確率的劣化による需要発生と管理エリア設計を扱わないという点は，原文中の明示的な限界記述ではなく，同論文の問題設定・定式化と本研究を比較した著者側の判断であるため，Section 2でその根拠を詳述する。
- **原典**: https://doi.org/10.1016/j.cacaie.2026.100100
- **出版社ページ**: https://www.sciencedirect.com/science/article/pii/S1093968726030860
- **リポジトリ内レビュー**: `references/qiao2026_review.md`
