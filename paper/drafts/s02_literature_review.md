# Literature Review — 下書き（日本語）

> **方針メモ（2026-07-12 更新）**
> - サブセクション見出しは付けない。main.tex・s01と同じく見出しなしの連続する文章として書く（6章立てだった前バージョンから変更）。
> - 契約バンドリング→地域分割→確率的維持管理→統合ギャップの順に論じる。バンドリング・地域分割の2本柱を主軸として厚く書き、確率的維持管理（自分たちの先行研究）は3番目の1段落・数文程度の軽い言及に留める。
> - 分量はmain.tex他セクションとの比のなかで考える。既往研究がモデル構築・数値計算より長くなるのは不自然（2026-07-12にmain.texの既往研究を4,570字→3,258字へ圧縮した経緯を踏まえる）。この草稿もその水準（3,000〜3,500字程度）を上限の目安とする。
> - 引用は1本につき1〜2文まで。研究群ごとに「代表文献を2〜3本＋その限界」に絞り、関連文献を網羅的に並べない（Qiao 2018/2021・Miralinaghi・Bozkaya・Sandoval・Camacho-Collados・Assisは検討はしたが、既存の代表文献で論旨が成立するため本文には入れない。残課題に候補として残す）。
> - Type C（各国制度紹介の段落）・4類型表（Type A/B/C/D）は既往研究のボリュームを不必要に増やすため不採用（main.texからも削除済み）。
> - 「ネットワーク」という語は使わない。本研究・関連研究とも橋梁間の相互作用（交通の迂回、荷重の再配分等）はモデル化しておらず、複数施設を独立に扱う設定であるため、「複数施設を対象とした」等に言い換える。
> - 群マネ・広域連携の政策的背景はs01（はじめに）で既に述べているため、ここでは繰り返さない。既往研究は学術文献のギャップ提示に集中する。

---

橋梁や道路を対象とした契約バンドリングに関する研究では，複数事業を一つの契約に集約することの効果と，事業を束ねる際の判断基準が検討されてきた．Qiao（2019）は，インディアナ州の道路・橋梁プロジェクトを対象に，バンドルが単価，工期，入札者数などに与える影響を統計的に分析した．Assaf and Assaad（2023）およびAssaf et al.（2024）は，実際のインフラ事業の分析を通じて，地理的近接性，工種や規模の類似性，事業時期の整合性など，バンドリング戦略に影響する意思決定要因を抽出・体系化した．これらの研究はバンドリングの効果や判断要因を明らかにしているが，将来発生する補修需要をどのような管理範囲の下で集約するかという問題は扱っていない．

契約ロットの構成を明示的な意思決定問題として扱う研究も行われている．Qiao et al.（2026）は，道路工事プロジェクト群を組合せ最適化問題として定式化し，貪欲ヒューリスティックによってバンドリング戦略を導出した．しかし，同研究では候補となるプロジェクトリストがあらかじめ与えられており，補修需要の確率的な発生過程と管理エリアの設計は意思決定の対象に含まれない．また，空間的なグループ化の効果に着目したGooijer（2024）は，オランダの橋梁約85,000橋を対象に複数のクラスタリング戦略をシミュレーションで比較したが，分析対象はあらかじめ定義されたクラスタ戦略であり，契約集約効果を評価しながらクラスタ自体を形成する最適化ではない．このように，既存のバンドリング研究は，所与の事業群から契約ロットを構成する問題や，所与のクラスタ戦略の効果を主な対象としている．

これに対して，管理エリア自体の設計に関係する研究領域として，地域分割（districting）問題がある．地域分割問題では，地理的な基本単位を複数の地区へ編成する方法が，行政計画，選挙区割り，物流配送などの分野で研究されてきた．Kalcsics and Rios-Mercado（2019）は，均衡性，接続性，コンパクト性などの代表的な地区設計基準と，それらを考慮した数理的手法を体系的に整理している．Webster（2013）は政治区割りを対象に，人口均等性，コンパクト性，連続性，利害共同体の維持といった評価基準を検討した．また，Novaes et al.（2010）は物流配送を対象とする連続的な地域分割モデルを構築し，Power Voronoi図を用いて地理的障害を考慮した分割を示した．これらの研究は，地理的条件や地区間の均衡を考慮して空間的な地区を設計する方法を提供するが，地区内で確率的に発生する橋梁補修需要や，その需要を契約として集約した場合の期待契約件数を評価基準としていない．

また，本研究では，将来の補修需要を確率的に扱う必要がある．確率的な劣化・故障過程をインフラ維持管理上の意思決定に組み込む研究として，Nakazato et al.（2023）は，ライフサイクルコストと年度間費用の変動を考慮した補修方針の最適化を扱っている．Mizutani et al.（2025）は，道路施設の故障過程を考慮した補給部品配置を，連続近似を用いて最適化している．これらの研究は，不確実な劣化・故障過程を意思決定モデルに組み込んでいるが，補修需要の契約集約効果や管理エリアの設計は対象としていない．

以上の研究群は，それぞれ契約ロットの構成，管理エリアの空間設計，補修需要の不確実性を扱ってきた．しかし，これらを結び付け，確率的に発生する橋梁補修需要と契約バンドリングルールから期待契約件数を導出し，管理エリアの設計問題に組み込む枠組みは，確認した範囲では示されていない．本研究は，確率的な補修需要を契約集約効果の評価指標へ変換し，地理的制約の下で期待契約件数を最小化する管理エリアの空間構成を求める点に新規性がある．

---

> **残課題・確認事項**
> - 引用は著者・年のみの仮置き。s01と同水準の原文照合（ページ番号・原文引用）は未実施。
> - Nakazato et al. (2023)・Mizutani et al. (2025) は出版社ページのAbstract等で本文記述に対応する問題設定を確認済み。モデルの対象外事項を含む詳細な比較は、著者保有原稿でも確認する。
> - main.texの`\bibitem`に未登録：なし（本文で使う文献はすべて既存の`\bibitem`でカバーされている：`nakazato2023`, `mizutani2025`, `webster2013`, `kalcsics2019`, `novaes2010`, `qiao2019`, `qiao2026`, `gooijer2024`, `assaf2023`, `assaf2024`）。
> - 検討したが不採用にした文献（分量抑制のため）：Hadjidemetriou (2020), Frangopol and Liu (2007), Orcesi and Cremona (2010), Wu et al. (2017)（確率的維持管理系の国際文献）／Qiao (2018), Qiao (2021), Miralinaghi et al. (2022)（契約バンドリング系）／Bozkaya et al. (2003), Sandoval et al. (2020), Camacho-Collados et al. (2015), Assis et al. (2014)（District Optimization系）。将来的に査読者から「レビューが手薄」と指摘された場合の増補候補として保持。
> - 群マネ・広域連携の制度的背景はs01（はじめに）で既出のため本節では割愛した。既存main.texの既往研究冒頭（管理エリアの普遍性・米国State DOT・日本の小規模自治体問題）とs01の記述に重複がないか、統合時に要確認。
> - 本文は「契約バンドリング→地域分割→確率的維持管理→統合ギャップ」の順に再構成済み。main.texへ統合する際は、現行の既往研究本文を部分修正するのではなく、本草稿の構成に沿って節全体を置き換える。

---

## References in this section

本文中の引用とLaTeX `\bibitem`キーの対応表。書誌情報はmain.texの現行`\bibitem`からそのまま転記（新規追加なし）。

| 番号 | 本文中の表記 | `\bibitem`キー | 書誌情報 |
|---|---|---|---|
| [1] | Qiao, 2019 | `qiao2019` | Qiao, Y.: Bundling effects on contract performance of highway projects: quantitative analysis and optimization framework, Ph.D. Dissertation, Purdue University, 2019. |
| [2] | Assaf and Assaad, 2023 | `assaf2023` | Assaf, G. and Assaad, R. H.: Key decision-making factors influencing bundling strategies: analysis of bundled infrastructure projects, Journal of Infrastructure Systems, Vol.29, No.2, 2023. |
| [3] | Assaf et al., 2024 | `assaf2024` | Assaf, G., Assaad, R. H. and Karaa, F.: Identifying the opportunities and challenges of project bundling: modeling and discovering key patterns using unsupervised machine learning, Journal of Infrastructure Systems, Vol.30, No.1, 2024. |
| [4] | Qiao et al., 2026 | `qiao2026` | Qiao, J. Y., Guo, Y., Seilabi, S., Fricker, J. D. and Labi, S.: A proposed algorithm for identifying heuristic-optimal bundling strategies, Computer-Aided Civil and Infrastructure Engineering, Vol.49, 100100, 2026. |
| [5] | Gooijer, 2024 | `gooijer2024` | Gooijer, N. J. C.: Entity-based System Dynamics for Bridge Asset Management: Exploring the Effects of Spatial Maintenance Cluster Strategies on Infrastructure System Performance, MSc Thesis, Delft University of Technology, 2024. |
| [6] | Kalcsics and Rios-Mercado, 2019 | `kalcsics2019` | Kalcsics, J. and Rios-Mercado, R. Z.: Districting Problems, Location Science, Springer International Publishing, pp.705--743, 2019. |
| [7] | Webster, 2013 | `webster2013` | Webster, G. R.: Reflections on current criteria to evaluate redistricting plans, Political Geography, Vol.32, No.1, pp.3--14, 2013. |
| [8] | Novaes et al., 2010 | `novaes2010` | Novaes, A. G. N., Frazzon, E. M., Scholz-Reiter, B. and Lima Jr., O. F.: A continuous districting model applied to logistics distribution problems, Proceedings of the XVI International Conference on Industrial Engineering and Operations Management, Sao Carlos, Brazil, 2010. |
| [9] | Nakazato et al., 2023 | `nakazato2023` | Nakazato, Y., Mizutani, D. and Fukuyama, S.: Optimal Repair Policies for Infrastructure Systems with Life Cycle Cost Minimization and Annual Cost Leveling, Journal of Infrastructure Systems, Vol.29, No.3, 04023021, 2023. |
| [10] | Mizutani et al., 2025 | `mizutani2025` | Mizutani, D., Fukuyama, S. and Satsukawa, K.: Optimal road facility spare parts location with continuum approximation, Transportation Research Part C: Emerging Technologies, Vol.174, 105109, 2025. |

**解決済み**: [8] Novaes et al. (2010) は原論文（Proceedings of the XVI ICIEOM, São Carlos, Brazil, 2010）をダウンロード・確認し、共著者フルネーム（Antônio Galvão Naclério Novaes, Enzo Morosini Frazzon, Bernd Scholz-Reiter, Orlando Fontes Lima Jr.）を特定した。main.texの`\bibitem{novaes2010}`および本表を修正済み。全10件の文献がフルネームで整理されている。
