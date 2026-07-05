
## 要点: 研究接続可能性の核心

- **District Optimization の定義確定**: Kalcsics (Springer, 2019) は Districting Problem を「地理的基本単位(基本ユニット,basic units)を、グループ化によってより大きな地理的クラスタ(district)にまとめていく問題」と定義している。基礎単位を basic units、集約後のクラスタを districts と呼ぶ枠組みが国際的に共有されている [5]。
- **3 つの代表的サブ問題**: 同一問題の派生として、政治区割り(Political Districting)、営業・サービス地区設計(Territory Design)、公共サービス地区割(Service Districting)が並列に発展してきた。橋梁補修バンドリングは、このうち Service/Territory Design 系列に直接接続する [24]。
- **共通制約の核**: contiguity(連続性/連結性), compactness(コンパクト性), balance/workload equality(負荷均衡)の 3 制約がほとんどの既往研究で採用される。橋梁を地理的にバンドリングする本研究は、contiguity を「工事現場の地理的近接性」に、balance を「補修需要量(交通量・劣化度・コスト)の均衡」に、compactness を「運搬・動員効率の再近接性」にそれぞれ読み替えることで定式化可能となる [5], [24]。
- **定式化の階層構造**: 本研究の地域バンドリング問題は、再近接空間でのクラスタリング(Graph Partitioning)というよりも、空間多角形集約問題(Spatial Regionalization)に分類される。ACM SSTD 2025 による総括では、spatial regionalization は contiguity 制約と p-regions / max-p 制約を共通の枠組みとして持つと整理されている [68]。
- **周辺問題との明確な差異**: Cluster は contiguity を強制しない、VRP は既に固定された地域の内部でルートを引く、Facility Location は新規拠点の配置を対象とするのに対し、District Optimization は「既存の地理単位をどう集約するか」に焦点を置く。橋梁補修バンドリングはまさに「既存橋梁オブジェクトの集約」であるため、Cluster でも VRP でもない独自の位置付けとなる [5], [24]。
- **多分野横断的な発展**: この理論は Operations Research (Kalcsics, Bozkaya, Lespay)、GIS (Google Research の road partitioning)、Public Administration (George がニュージーランド選挙区割りに適用、CLEARROADS が雪氷作業地区割りを整理)、Transportation (Ji/Ye/Yang が都市交通ネットワークを Normalized Cut で分割)、Infrastructure Management (FHWA の Bridge Bundling 概念) で個別に発展してきた。橋梁補修研究は OR/Infrastructure の交差点に位置する [67], [39], [60]。
- **インフラ系バンドリングの実務慣行**: FHWA は Bridge Bundling を「予防保全、補修、または架け替えのために、定義された橋梁セットをタイムリーかつ効率的に計画すること」と公式定義し、近接性・地理・道路種別・交通量・作業帯管理を bundle 化の判断軸として挙げている。NYSDOT 実務地区では「ハイウェイ地区単位(statewide district)」が bundle ロットに対応している [33], [30]。
- **研究ギャップ**: 既存文献では電気メータ巡回(Assis 2014)、配送地区設計(Lespay 2022; Sandoval 2020)、警察管区(Camacho-Collados 2015)、選挙区(George 1997; Swamy 2023)、販売テリトリー(Oracle, Xactly)で定式化されているが、**橋梁補修契約ロットを districting の組合せ最適化として明示的に定式化した文献はほぼ存在しない**。既存の橋梁実務バンドリングはヒューリスティック / 行政地区ベースであり、OR 的な厳密解やメタヒューリスティクス最適化を組み込んだ学術研究は探索ギャップとなっている [3], [2], [11]。

## 1. District Optimization の定義と分類体系

District Optimization の中心問題は、Kalcsics が Springer の "Location Science" ハンドブック(2019)でまとめた定義によれば、「地理的基本単位(これを basic units と呼ぶ)を、より大きな地理クラスタ(district)に compact, contiguous, balanced という 3 条件で集約する」ことにある [5]。この定義は Bozkaya らの 2003 年のタブー探索論文でも同様に踏襲されており、応用例の代表として「選挙区(school board, political constituency)」「販売 / 配送地区(sales or delivery regions)」「都市サービス地区」の 3 系統が挙げられている [24]。

研究領域は実務上の目的関数に応じて 4 つのサブ問題に分岐してきた。

|サブ問題|中心目的|代表的応用|主要制約|
|---|---|---|---|
|Political Districting|投票権の平等 / コンパクト性 / ゲリマンダリング防止|選挙区割り、国勢調査地区|人口同準, compactness, contiguity, 既存の郡/市境界尊重|
|Territory Design|配送コスト削減, ドライバーの負荷均衡|飲料配送(Lespay 2022), 営業テリトリー(Oracle)|p-center 最小化, balance, contiguity|
|Service Districting|公共サービス提供の効率化|メータ巡回(Assis 2014), 警察管区(Camacho-Collados 2015), 雪氷作業地区|workload balance, response time, compactness|
|Spatial Regionalization|統計的類似性による地域集約|教育地区境界, 統計区|contiguity, 内部均質性, 母数均衡|

出典: [5], [3], [11], [20], [68].

> **ケーススタディ: ニュージーランド選挙区割りへの大規模ネットワーク最適化 (George et al. 1997)**. George らは 35,000 個の meshblock (基本統計単位) を 95 の Parliamentary District にまとめる問題を、ネットワーク最適化として定式化した。司法/歴史的境界を尊重しつつ、人口同準とコンパクト性を同時に最適化する必要があり、組合せ最適化と GIS の統合事例として位置付けられる [67]。この事例は「既存の基本単位 (市町村、地区、橋梁) を地理的に意味のある地域に集約する」という問題の原型そのものを持っており、橋梁補修バンドリングにも適用できる構造を持つ。

このうち、本研究の橋梁補修バンドリングは **Service Districting の系列**(保守対象への近接性確保、補修需要量(workload)の均衡、契約ロットとしてのコンパクト性)に直接属すると整理できる。

> **観察 -> メカニズム -> 含意 -> 推奨**: District Optimization の 4 系列は実務目的関数で分岐しているが、共通言語 (basic units -> districts) と共通制約 (contiguity / compactness / balance) を共有する。橋梁補修研究ではこれら 3 制約を補修契約ロット定義に読み替えることで、既存系列に接合できる。

## 2. 数学的定式化の枠組みと代表的客観関数

District Optimization の数理的構造は Sandoval らの定式化(Sandoval 2020)および Assis らの定式化(Assis 2014)に代表される。基本形は次の 3 つの骨格で構成される。

- **集合被覆 / 分割制約 (set partitioning / assignment)**: 各 basic unit $i$ はちょうど 1 つの district $k$ に割り当てる (式: $\sum_{k} x_{ik} = 1$ for all $i$)。
- **地域数固定制約 (p-region / max-p)**: ACM SSTD 2025 の総括では、ACM 標準の regionalization 制約として「p-regions (固定数)」と「max-p (上限数のみ)」の 2 形式が整理されており、橋梁補修バンドリングも bundle 数を固定するか上限のみかで定式化が変わる [68]。
- **連続性制約 (contiguity)**: Sandoval 2020 では cut-generation 戦略で連続性を課す。Bozkaya 2003 も contiguity を "illegal move" としてタブー探索に組み込む [2], [24]。

これを踏まえ、既往研究で採用されてきた代表的な目的関数を整理する。

|カテゴリ|目的関数|説明|代表適用|出典|
|---|---|---|---|---|
|Compactness|Moment-of-Inertia (Moment of inertia about centroid)|重心から構成地点までの総距離が小さいほど compact|Political Districting, 配送地区|[6]|
|Compactness|Perimeter / Area ratio|周囲長と面積の比で「歪度」を測る|政治区割り (R package Compactness)|[9]|
|Compactness (alternative)|Convex Hull ratio (Hopkins / Reock)|地域の convex hull と実際の面積比|Political Districting|[10]|
|Workload balance|Capacity violation minimization|各地区の負荷を事前に設定した基準値に揃える|警察管区, メータ巡回|[11], [3]|
|Dispersion|p-center dispersion minimization|地域分散を最小化 (capacitated p-center と同型)|飲料配送 (Sandoval 2020)|[2]|
|Cost / distance|Travel cost minimization|地域内総走行時間/距離を最小化|配送設計 (Lespay 2022)|[20]|
|Multi-objective|Fairness + compactness|政治的公平性 (vote-seat 比、競争性、効率ギャップ) + 非政治的コンパクト性|政治区割り (Swamy 2023)|[1]|
|Network modularity|Modularity / normalized cut|地域内リンク密度が高く、地域間が低いことを最大化|道路ネットワーク分割 (Ma 2023, Ji 2012)|[41], [52]|

> **ケーススタディ: 米国内の選挙区と多目的 districting (Swamy et al. 2023)**. Swamy らは Wisconsin 州の選挙区を多目的に最適化するため、党派性の (a)symmetry, competitiveness, vote-seat 比例性、効率ギャップ(効率性ギャップ)、コンパクト性の複数尺度を組み合わせた多目的 MIP を構築した。レベル別アプローチ(multilevel)により州全体を逐次 refine し、組合せ爆発を回避するスケーラブルな解法を提示している [1]。橋梁補修バンドリングでは、(a) 補修需要の balance、(b) 地理的 compactness、(c) 既存維持管理境界との整合という複数目的を同時に扱う必要があり、Swamy の多目的フレームは参考構造となる。

> **観察 -> メカニズム -> 含意 -> 推奨**: 既往研究の客観関数は大きく「形状 (compactness 系列)」「負荷 (workload 系列)」「分散 (cost / dispersion 系列)」「ネットワーク/モジュラリティ系列」の 4 種類に分類できる。橋梁補修バンドリングでは (a) 動員効率 = p-center 分散 (Sandoval 2020 流)、(b) 補修需要量 balance (Assis 2014 流)、(c) bundle 数 min (制限 infra cost optimization)、(d) 既存道路・行政区境界尊重 (Bozkaya 2003 の「禁忌制約」流) の複合目的関数が理論的に妥当である。

## 3. 周辺問題との位置付け: VRP / Clustering / Facility Location / Regionalization との違い

District Optimization が学術的に確立した問題として認識されるためには、隣接する最適化問題との明確な差異を整理する必要がある。文献を横断して 4 つの隣接問題と本問題を比較すると以下の表に整理できる。

|比較軸|District Optimization|Clustering|Vehicle Routing (VRP)|Facility Location|Spatial Regionalization|
|---|---|---|---|---|---|
|入力|既存の地理単位 (basic units) の集合|任意のデータ点 / ベクトル|拠点と顧客、需要|配置候補拠点 + 需要点|空間多角形 (spatial polygons)|
|出力|地理的に不規則な地域の集合 (districts)|メンバシップの集合 (形状制約なし)|各車両が回る経路 (固定地域内)|拠点を配置し需要を割当|不規則形状の均質地域集合|
|連続性制約|通常必須 (contiguity hard constraint)|任意 (k-means 等では不要)|不要 (個別経路に従う)|不要 (拠点配置のみ)|ほぼ必須 (ACM SSTD 2025)|
|規模|数百 ~ 数万 basic units|数百 ~ 数百万クラスタ|数百 customer 数|数 ~ 数百拠点|数百 ~ 数千ポリゴン|
|主な目的|compactness / balance / cost / 多目的|内部均質性最大化|走行コスト最小化|距離 / 容量コスト最小化|内部均質性 + 境界整合|
|中心定式化|set partitioning + contiguity cut|k-means, hierarchical, spectral|set partitioning + capacity|0-1 MIP + capacity|set partitioning + contiguity|
|代表的応用|政治区割り, 配送地区|マーケティング分析|物流配送, スクールバス|倉庫・工場配置|統計区割り, リスク管理|

出典: [5], [23], [22], [68].

> **ケーススタディ: メータ巡回地区設計 (Assis et al. 2014)**. Assis らはブラジル電力網のメータ読み取り地区再設計を districting 問題として定式化した。彼らは 4 つのメタヒューリスティクス (ILS, VND, GA, SA) を比較し、「contiguity は hard constraint、balance は capacity equality constraint、compactness は secondary objective」という典型的な DP の階層構造を確認した [3]。興味深いのは、彼らが VRP を解かなかったことである - 「どの地域を巡回するか」と「地域内でどう巡回するか」を階層分離 (DP -> VRP) しており、Lespay 2022 は逆にこれを統合して解く方向に動いている [20]。この「分離 vs 統合」の選択は、橋梁補修バンドリングにおいて bundle 決定と bundle 内動員計画を分離するか統合するかの判断に直接反映できる。

**Regionalization とのニュアンスの差** は文献によって相反する。ACM SSTD 2025 では Spatial Regionalization を contiguity 必須の「空間多角形集約問題」と総括し、政治区割りや教育区割りを代表例として挙げる [68]。一方、ScienceDirect トピックページでは Regionalization を「building block zones を criteria に応じて集約するより広範な discipline」とし、必ずしも contiguity を要求しない手順も含むとしている [66]。District Optimization は両者の中でも **contiguity を必須とし、目的関数に workload/demand balance を明示的に含む** という特徴で位置付けられる。本研究はこの厳密な DP の定義系列に準拠するのが妥当である。

> **観察 -> メカニズム -> 含意 -> 推奨**: 本研究の bridge bundling 問題は、Clustering ではなく (basic units = 橋梁という離散対象物)、VRP ではなく (契約ロットを「地域」として決める段階で個別工事車両経路は未定)、Facility Location ではなく (新規拠点を作らない) ことが明確である。Regionalization との差は contiguity と workload balance の強制度合いに表れる。本研究は OR 系の Districting Problem の厳密定義に従うことで、論文タイトル / introduction において既存系列との差異が明確化する。

## 4. 適用領域と発展研究分野

District Optimization は単一の分野ではなく、複数の学術コミュニティで個別に発展してきた。橋梁補修研究の位置付けを明確にするため、文献を分野横断で整理する。

### 4.1 Operations Research (OR)

OR 分野では districting を組合せ最適化 / 整数計画問題として扱う系譜が最も長い。Hess による 1965 年の投票区研究に起源を持ち、Weaver / Hess の後、Garfinkel / Nemhauser が 1970 年に整数計画として定式化、Kalyanasundaram / Russell (1994) がグラフ理論としての定式化を提案したとされる [24]。現代ではタブー探索 (Bozkaya 2003)、GRASP / VND / GA / SA (Assis 2014)、そして MIP 厳密解 (Sandoval 2020) まで、メタヒューリスティクスから厳密解まで完全に網羅している。近年は Swamy らが multilevel MIP によるスケーラブル解を提案し、Wisconsin 州 72 選挙区を多目的最適化した [1]。

### 4.2 GIS / 空間情報科学

GIS 分野では contiguity を扱うための多種アルゴリズム (Normalized Cut, FN アルゴリズム, Spectral Clustering) が発展してきた。Ma らは CSDRA 法で道路ネットワークを line sub-area と surface sub-area の 2 階層に分割し、FN アルゴリズム + Spectral + k-means のハイブリッドで多目的最適化(modularity + 負荷分散 + コンパクト性)を実現している [41]。Ji らは都市交通ネットワークを Normalized Cut で分割し、各サブネットワークでの MFD (Macroscopic Fundamental Diagram) を均質化することを試みた [52]。Google は inertial-flow アルゴリズムによる道路ネットワークの大規模分割を実装し、橋梁・トンネル (beacons) を境界ノードとして検出して経路計算を高速化している [39]。

### 4.3 Public Administration

行政実務の観点では、選挙区割り (George 1997, ニュージーランド) や警察管区最適化 (Camacho-Collados 2015) が代表例である。Camacho-Collados らはスペイン国家警察管区を再構築し、応答時間・負荷分散・コンパクト性を多目的最適化することで現行管区を上回る結果を得た [11]。米国では CLEARROADS が州単位の雪氷作業地区設計を「ネットワークをサービス地域に分割 -> 車両配分 -> 個車ルート設計」の 3 階層問題として整理している [60]。

### 4.4 Transportation

Transportation 分野では Bertsimas らの Boston 学区スクールバス最適化が代表的であり、スクール bell time と経路を同時に最適化するアルゴリズムで年 5M USD の節約を達成した (2019) [12]。これは transportation と districting を同時に扱う統合最適化の一例であり、橋梁補修でも「bundle 設計 + bundle 内動員計画」を統合する研究余地を示している (Lespay 2022 と同型の構造)。

### 4.5 Infrastructure Management

インフラ維持管理では FHWA が Bridge Bundling を制度的に推進している。FHWA は「a defined set of bridges that are planned for preservation/preventative maintenance, rehabilitation, or replacement in a timely and efficient manner」と定義し、近接性・道路種別・交通量・作業帯管理・環境許認可を bundle 化の判断軸として挙げている [33]。NYSDOT Region 1 では予防保全 bundle をハイウェイ地区単位で組成し、Design-Build 契約ロットとして発注している [30]。しかし、現状の bundle 化は「行政地区ヒューリスティクス」または「劣化度優先順位 (workload ベース単一基準)」に依拠しており、複合目的関数 + OR 的厳密解 / メタヒューリスティクスを組み込んだ学術研究は未開拓な研究ギャップとなっている。

> **ケーススタディ: NYSDOT Region 1 Preventative Maintenance Bridge Bundling**. NYSDOT は州全体ではなく Region 1 単位で年単位の bundle を組成する。bundle 化で得られる便益は、(1) 動員コスト削減 (近接橋梁を連続で施工)、(2) 少額補修を早期に一括処理することでの長寿命化、(3) 契約管理コスト低減 (単一大規模契約 vs 個別小契約) の 3 点に整理されている [30]。この実務運用は「地理的近接性」を主要判断軸とする典型的な service districting であり、OR 流の定式化に変換することで改善余地が生まれる余地を示唆している。

> **観察 -> メカニズム -> 含意 -> 推奨**: District Optimization は 5 つの分野 (OR, GIS, Public Administration, Transportation, Infrastructure Management) で個別に発展してきた。橋梁補修バンドリングはこれら 5 分野の **OR x Infrastructure Management の接点** に位置する。論文としては、OR 系 (Kalcsics, Bozkaya, Swamy 系譜の定式化)、GIS 系 (contiguity / 道路ネットワーク)、Transportation 系 (bundle 内動員計画) の手法を組合せて活用する文脈設計が望ましい。

## 5. 橋梁補修契約バンドリングとの接続と研究ギャップ

### 5.1 接続の核 - Districting としての橋梁バンドリング

本研究の橋梁補修契約バンドリング問題は、「既存の橋梁オブジェクト ($N$ 件) を地理的に意味のある $K$ 個の bundle (= 契約ロット) に集約する」という構造を持つ。これは Kalcsics の basic units -> districts 構造と完全に対応する [5]。従来の橋梁実務 (FHWA の bundle、NYSDOT Region 1 の bundle) はヒューリスティックスまたは行政区ベースで bundle を組成するが [30]、本研究はこれを組合せ最適化問題として明示的に定式化する立場を取る。

入力側は以下のようにモデル化できる。

- basic units: 各橋梁オブジェクト
- 特性 / 負荷量: 劣化度, 補修コスト推定, 交通量, 架設年
- 距離尺度: 橋梁間の道路ネットワーク距離 (Ma 2023 の edge graph 流) またはユークリッド距離 [41]
- 候補 depot (保守基地): 各 bundle の代表点 (NYSDOT 流の region 拠点)

出力側は bundle 集合 (契約ロット) であり、各 bundle は contiguity (施工動員可能な近接性)、compactness (移動コスト最小化)、workload balance (補修需要量均衡) を満たす。

### 5.2 既存研究に対する差異 = 研究ギャップ

既存文献を体系的に整理すると、橋梁補修を districting / territory design の組合せ最適化として明示的に扱った研究は極めて限定される。最も近い研究系列は以下の通り。

|研究系列|問題|bridge bundling との差|
|---|---|---|
|Police districting (Camacho-Collados 2015)|警察管区を応答時間 / balance / compactness で最適化|需要は「事件リスク」、地理制約は管区境界|
|Meter reading districting (Assis 2014)|電力メータ巡回地区を ILS / VND で最適化|巡回距離が支配、地区内 visit sequence が後段 VRP|
|Sales territory design (Sandoval 2020)|飲料配送地区を p-center dispersion で最適化|拠点 1 個 - 配送地区という 2 層構造|
|Multi-period VRP with territory design (Lespay 2022)|配送地区 + 期間ルート計画統合|動的需給変動と時間枠を扱う|
|Snowplow route optimization (CLEARROADS)|州内 snow fleet 地区 + ルート|multi-vehicle routing を含む|
|道路ネットワーク分割 (Ji 2012, Ma 2023)|都心混雑サブネットワーク、MFD 均質化|動的 / モジュラリティ重視|

出典: [11], [3], [2], [20], [60], [52].

**橋梁補修 bundle 特有の差異** は以下の 4 点に集約される。

1. **劣化状態の不均質性**: 多くの既往研究は demand を均一または既知確率分布で扱うが、橋梁 bundle では個別の状態評価 (NBI 評価, 塩害地域, 床版劣化) が異なるため、需要空間分布の異質性が大きい。
2. **既存行政境界との整合**: FHWA では「ハイウェイ地区単位」が bundle の目安となるが、境界を硬直的に固定すると動員効率が損なわれる。禁忌制約 (Bozkaya 2003 流) として扱うか、緩和制約として扱うかの選択が必要 [24]。
3. **補修種別の同時 bundle 化**: 単一 bundle 内に予防保全 / 補修 / 架替の複数種別が混在すると、作業隊の specialized skill や機材効率に影響する。Assis 2014 の単一 workloadではなく multi-attribute の balance 制約が必要 [3]。
4. **長期 maintenance schedule 同期**: 1 回の bundle に閉じず、複数年にわたる予防保全計画と整合する必要がある。Lespay 2022 の multi-period VRP 流の定式化が参考になる [20]。

> **ケーススタディ: 既存研究と本研究の接合点 (Sandoval 2020 -> 橋梁 bundle)**. Sandoval らは飲料配送会社の商業地区設計を厳密解で解き、capacitated p-center dispersion 最小化 + cut-generation による contiguity 確保の定式化を採用した [2]。橋梁 bundle にもこの capacitated p-center 流の定式化を導入すると、「bundle 内の代表的橋梁 (depot 相当) からの最大動員距離を最小化しつつ、補修需要量 workload の capacity constraint を満たし、contiguity を cut-generation で確保する」という MIP が構成できる。これは従来 FHWA 実務で「地区単位 bundle」と呼ばれてきた対象を、見直しうる「数学的に最適な bundle」として再構成する可能性を開く。

### 5.3 研究ギャップの戦略的位置付け

結論として、研究ギャップは次の 3 層に整理できる。

- **理論ギャップ**: 既存 districting の定式化 (Kalcsics, Bozkaya, Sandoval) と FHWA 実務バンドリングの間に、橋梁補修需要を明示的に扱った定式化論文がほぼ存在しない。
- **実務ギャップ**: FHWA bundle / NYSDOT bundle はヒューリスティックスに依拠し、組合せ最適化の解との厳密比較がなされていない。
- **統合機会**: 既存 maintenance scheduling (AASHTOWare BrM, assetintel manageX) は個別橋梁の優先度付けに留まり、bundle 化の組合せ最適化層を持たない [75].

> **観察 -> メカニズム -> 含意 -> 推奨**: 橋梁 bundle は districting の応用カテゴリとして、1) 既存需要の異質性、2) 行政境界との部分的整合 (禁忌制約 vs 緩和制約)、3) 複数補修種別の同 bundle 内共存、4) 長期 maintenance schedule との同期という 4 つの既存研究にない特徴を持つ。本研究はこれらを明示的に制約として組み込むことで、Kalcsics-Bozkaya-Sandoval 流の DP 最適化系列に「インフラ維持管理」の応用先を開く位置付けとなる論文となり得る。

## 6. 統合分析: 既往 districting 系列と橋梁 bundle の位置付け

本研究の橋梁補修契約バンドリング問題を District Optimization の系列の中に位置付けるために、文献上の応用事例を 3 次元で対比する。

### 6.1 3 次元対比表

- **次元 1 (目的関数の主軸)**: 政治区割り = コンパクト性 + 公平性、配送地区 = コスト最小、保守 / メータ = workload balance、道路分割 = モジュラリティ / MFD 均質化。
- **次元 2 (解法の厳密性)**: Bozkaya 2003 = メタヒューリスティクス (タブー)、Sandoval 2020 = 厳密 MIP、Swamy 2023 = 多目的厳密 MIP、Ma 2023 = ハイブリッド (FN + Spectral + k-means)。
- **次元 3 (集約対象の性質)**: Political = 人 (投票)、Territory = 顧客需要、Service = 巡回対象、Network = リンク属性、Bridge = 劣化状態。

|応用|目的主軸|解法厳密性|集約対象|橋梁 bundle との距離|
|---|---|---|---|---|
|Political (Bozkaya, Swamy)|compactness + fairness|メタ/MIP|人・統計単位|中 (定式化は類似、応用は遠い)|
|Territory Design (Sandoval, Lespay)|p-center dispersion|厳密 MIP|配送顧客|近 (定式化は類似、対象は流動的)|
|Service Districting (Assis, Camacho-Collados)|workload balance|メタ / 多目的|巡回 / 事件リスク|極近 (定式化構造はそのまま使える)|
|Network / Transportation (Ji, Ma, Bertsimas)|modularity / MFD / cost|ハイブリッド / 厳密|リンク / バス|近 (ネットワーク構造の扱いは参考)|
|Bridge Bundling (本研究)|workload + compactness + 行政整合|提案 (OR 定式化)|橋梁オブジェクト|-|

### 6.2 緊張と対立点

文献横断分析から見える 3 つの緊張点を明示的に扱っておく必要がある。

- **緊張点 1: contiguity の厳密度 vs 実務柔軟性**. Kalcsics / Sandoval / Bozkaya 系は contiguity を hard constraint とすることが多い。一方で FHWA 実務 bundle は行政地区境界を絶対視しつつも、非連続の bundle を許容する場面も存在する。これは contiguity を **hard constraint** にするか **soft constraint (罰金項)** にするかの選択問題として、整理される。
- **緊張点 2: 厳密解とメタヒューリスティクスの選択**. Sandoval 2020 の capacitated p-center 流 MIP は厳密だが、橋梁 $N=数千規模$ の実務では計算時間がかかる。Swamy 2023 の multilevel decomposition はスケーラビリティ問題を解決するが、bundle 間の fairness は別途考慮が必要。本研究では multilevel DP (Swamy 流) + 厳密 MIP (Sandoval 流) の 2 層構成が候補となる。
- **緊張点 3: bundle 数の固定 vs 自由 (max-p)**. FHWA bundle は予算制約から最大 bundle 数 (max-p) で運用される。一方、政治区割り (Bozkaya) は p-fixed が通常。橋梁 bundle では予算 (改修予算) と bundle 数の関係がパラメタ化できる。

### 6.3 含意 (4 ステップの observation -> mechanism -> implication -> recommendation)

|Step|内容|
|---|---|
|Observation|既存 districting 系列には、政治 (人) / 配送 (顧客) / 保守 (巡回対象) の 3 大応用があり、それぞれ目的関数の主軸が異なる。|
|Mechanism|目的関数主軸の違いは、集約対象の状態空間の違いから来る - 政治は投票分布、配送は需要分布、保守は劣化 / リスク分布。|
|Implication|橋梁 bundle の目的関数は (a) 劣化ベースの workload balance、(b) compactness ベースの動員コスト、(c) 行政整合、の 3 重となる。|
|Recommendation|本研究は Sandoval 2020 の capacitated p-center 定式化を骨格に、workload balance (Assis 2014) と行政整合禁忌 (Bozkaya 2003) を統合する MIP として定式化する。アルゴリズムには multilevel 構造 (Swamy 2023) を採用し、大規模橋梁集合にスケールさせる。これは既存 districting 文献と FHWA 実務バンドリングを直接接合する位置付けとなる。|

## References

1. Multiobjective Optimization for Politically Fair Districting. [https://pubsonline.informs.org/doi/10.1287/opre.2022.2311](https://pubsonline.informs.org/doi/10.1287/opre.2022.2311)
2. An improved exact algorithm for a territory design problem .... [https://www.sciencedirect.com/science/article/abs/pii/S095741741930867X](https://www.sciencedirect.com/science/article/abs/pii/S095741741930867X)
3. A redistricting problem applied to meter reading in power .... [https://www.sciencedirect.com/science/article/pii/S0305054813002086](https://www.sciencedirect.com/science/article/pii/S0305054813002086)
4. Optimization Models for the Political Districting Problem. [https://preserve.lehigh.edu/system/files/derivatives/coverpage/453261.pdf](https://preserve.lehigh.edu/system/files/derivatives/coverpage/453261.pdf)
5. Districting Problems. [https://ideas.repec.org/h/spr/sprchp/978-3-030-32177-2_25.html](https://ideas.repec.org/h/spr/sprchp/978-3-030-32177-2_25.html)
6. 4.5 Geometry and Compactness. [https://web.stevenson.edu/mbranson/m4tp/version1/gerrymandering-math-topic-compactness.html](https://web.stevenson.edu/mbranson/m4tp/version1/gerrymandering-math-topic-compactness.html)
7. Generating balanced workload allocations in hospitals. [https://www.sciencedirect.com/science/article/abs/pii/S2211692323000139](https://www.sciencedirect.com/science/article/abs/pii/S2211692323000139)
8. LP Objective function for distributing workload. [https://or.stackexchange.com/questions/8101/lp-objective-function-for-distributing-workload](https://or.stackexchange.com/questions/8101/lp-objective-function-for-distributing-workload)
9. Compactness: An R Package for Measuring Legislative .... [https://gking.harvard.edu/software/compactness-an-r-package-for-measuring-legislative-district-compactness-if-you-only-know-it-when-you-see-it/](https://gking.harvard.edu/software/compactness-an-r-package-for-measuring-legislative-district-compactness-if-you-only-know-it-when-you-see-it/)
10. Compactness. [https://ballotpedia.org/Compactness](https://ballotpedia.org/Compactness)
11. A multi-criteria Police Districting Problem for the efficient .... [https://www.sciencedirect.com/science/article/abs/pii/S0377221715004130](https://www.sciencedirect.com/science/article/abs/pii/S0377221715004130)
12. Optimizing schools' start time and bus routes. [https://www.pnas.org/doi/10.1073/pnas.1811462116](https://www.pnas.org/doi/10.1073/pnas.1811462116)
13. Infrastructure Management. [https://www.pima.gov/1681/Infrastructure-Management](https://www.pima.gov/1681/Infrastructure-Management)
14. Bus Routing Optimization Helps Boston Public Schools .... [https://analyticsbetterworld.org/journals/bus-routing-optimization-helps-boston-public-schools-design-better-policies/](https://analyticsbetterworld.org/journals/bus-routing-optimization-helps-boston-public-schools-design-better-policies/)
15. Why School Bus Routing Breaks Down (and How to Fix It). [https://www.everdriven.com/resources/blog/school-bus-routing/](https://www.everdriven.com/resources/blog/school-bus-routing/)
16. Gerrymandering and computational redistricting - PMC - NIH. [https://pmc.ncbi.nlm.nih.gov/articles/PMC6777516/](https://pmc.ncbi.nlm.nih.gov/articles/PMC6777516/)
17. Constraint-based electoral districting using a new .... [https://www.sciencedirect.com/science/article/pii/S0305054822001575](https://www.sciencedirect.com/science/article/pii/S0305054822001575)
18. Optimization Models for the Political Districting Problem. [https://preserve.lehigh.edu/flysystem/fedora/2025-08/Ruskeylehigh0105A13153.pdf](https://preserve.lehigh.edu/flysystem/fedora/2025-08/Ruskeylehigh0105A13153.pdf)
19. A History of One-Winner Districts for Congress. [https://fairvote.org/archives/a-history-of-one-winner-districts-for-congress/](https://fairvote.org/archives/a-history-of-one-winner-districts-for-congress/)
20. Territory Design for the Multi-Period Vehicle Routing .... [https://www.sciencedirect.com/science/article/abs/pii/S0305054822001393](https://www.sciencedirect.com/science/article/abs/pii/S0305054822001393)
21. Territory Design for Dynamic Multi-Period Vehicle Routing .... [https://arxiv.org/abs/2012.10506](https://arxiv.org/abs/2012.10506)
22. On the computational tractability of a geographic clustering .... [https://ui.adsabs.harvard.edu/abs/arXiv:2009.00188](https://ui.adsabs.harvard.edu/abs/arXiv:2009.00188)
23. Vehicle routing problem. [https://en.wikipedia.org/wiki/Vehicleroutingproblem](https://en.wikipedia.org/wiki/Vehicleroutingproblem)
24. A tabu search heuristic and adaptive memory procedure for .... [https://www.sciencedirect.com/science/article/abs/pii/S0377221701003800](https://www.sciencedirect.com/science/article/abs/pii/S0377221701003800)
25. A genetic algorithm framework for algorithmic design through .... [https://link.springer.com/article/10.1007/s40324-025-00398-4](https://link.springer.com/article/10.1007/s40324-025-00398-4)
26. Fast and Effective Redistricting Optimization via Composite .... [https://arxiv.org/html/2605.06682v1](https://arxiv.org/html/2605.06682v1)
27. Tabu search. [https://en.wikipedia.org/wiki/Tabu_search](https://en.wikipedia.org/wiki/Tabu_search)
28. Genetic Algorithm for Optimizing Urban District and Block .... [https://www.mdpi.com/2075-5309/14/12/3898](https://www.mdpi.com/2075-5309/14/12/3898)
29. Territory Planning for Field Sales & Service. [https://carto.com/solutions/territory-planning/](https://carto.com/solutions/territory-planning/)
30. NYSDOT Region 1 Preventative Maintenance Bridge .... [https://www.fhwa.dot.gov/ipd/alternativeprojectdelivery/defined/bundledfacilities/casestudynysdotpreventativemaintenancebridge.aspx](https://www.fhwa.dot.gov/ipd/alternativeprojectdelivery/defined/bundledfacilities/casestudynysdotpreventativemaintenancebridge.aspx)
31. Regional Road Maintenance ESA Program | CRAB. [https://crab.wa.gov/engineering/operations/regional-road-maintenance-esa-program](https://crab.wa.gov/engineering/operations/regional-road-maintenance-esa-program)
32. Bridge Bundling. [https://www.ilsoy.org/focus-areas/market-development/bridge-bundling/](https://www.ilsoy.org/focus-areas/market-development/bridge-bundling/)
33. Federal Bridge Bundling. [https://minnesotacountyengineers.org/wp-content/uploads/2022/06/Federal-Bridge-Bundling.pdf](https://minnesotacountyengineers.org/wp-content/uploads/2022/06/Federal-Bridge-Bundling.pdf)
34. Essen an Service. [https://www.mma.org/wp-content/uploads/2018/07/regionalizationmurrayadvocatev25-30.pdf](https://www.mma.org/wp-content/uploads/2018/07/regionalizationmurrayadvocatev25-30.pdf)
35. Learn About Districts. [https://www.csda.net/about-special-districts/learn-about](https://www.csda.net/about-special-districts/learn-about)
36. Special Districts | City of Colorado Springs. [https://coloradosprings.gov/planning-and-development/page/special-districts](https://coloradosprings.gov/planning-and-development/page/special-districts)
37. Sharing and/or Regionalizing Local Services. [https://massmarpa.org/resources/regionalization/](https://massmarpa.org/resources/regionalization/)
38. What is network infrastructure? Design and Current Trends. [https://drivenets.com/resources/education-center/what-is-network-infrastructure/](https://drivenets.com/resources/education-center/what-is-network-infrastructure/)
39. Efficient Partitioning of Road Networks. [https://research.google/blog/efficient-partitioning-of-road-networks/](https://research.google/blog/efficient-partitioning-of-road-networks/)
40. A flexible road network partitioning framework for traffic .... [https://www.sciencedirect.com/science/article/pii/S1093968726001660](https://www.sciencedirect.com/science/article/pii/S1093968726001660)
41. Research on Road Network Partitioning Considering the .... [https://www.mdpi.com/2220-9964/12/8/327](https://www.mdpi.com/2220-9964/12/8/327)
42. Road Networks Explained: Turning Geography into a .... [https://ricofritzsche.me/road-networks-explained-turning-geography-into-a-navigable-graph/](https://ricofritzsche.me/road-networks-explained-turning-geography-into-a-navigable-graph/)
43. Sales Territory Optimization Defined. [https://www.oracle.com/cx/sales/sales-territory-optimization/](https://www.oracle.com/cx/sales/sales-territory-optimization/)
44. Sales Territory Planning Best Practices: A 2026 Guide. [https://www.xactlycorp.com/blog/territory-management/sales-territory-planning-best-practices](https://www.xactlycorp.com/blog/territory-management/sales-territory-planning-best-practices)
45. Sales Territory Optimization: Best Practices and Benefits. [https://www.captivateiq.com/blog/sales-territory-optimization-best-practices](https://www.captivateiq.com/blog/sales-territory-optimization-best-practices)
46. How to Plan and Assess Your Sales Territories for Success .... [https://www.ascentcloud.io/blog/how-to-plan-and-assess-your-sales-territories-for-success-in-2025](https://www.ascentcloud.io/blog/how-to-plan-and-assess-your-sales-territories-for-success-in-2025)
47. Sales Territory Planning Metrics for Revenue Growth. [https://www.abacum.ai/blog/sales-territory-planning](https://www.abacum.ai/blog/sales-territory-planning)
48. Winter Road Maintenance Priority Map. [https://dot.alaska.gov/stwdmno/wintermap/](https://dot.alaska.gov/stwdmno/wintermap/)
49. Spatial Partitioning Algorithms for Solving Location-Allocation .... [https://digital.library.unt.edu/ark:/67531/metadc1609062/](https://digital.library.unt.edu/ark:/67531/metadc1609062/)
50. Winter Road Maintenance. [https://www.pendoreille.gov/public-works/page/winter-road-maintenance](https://www.pendoreille.gov/public-works/page/winter-road-maintenance)
51. Evaluation of Heuristics for the P-Median Problem - PMC. [https://pmc.ncbi.nlm.nih.gov/articles/PMC8341018/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8341018/)
52. On the spatial partitioning of urban transportation networks. [https://www.sciencedirect.com/science/article/abs/pii/S0191261512001099](https://www.sciencedirect.com/science/article/abs/pii/S0191261512001099)
53. 1965 Redistricting in 17 States. [https://library.cqpress.com/cqalmanac/document.php?id=cqal65-1259809](https://library.cqpress.com/cqalmanac/document.php?id=cqal65-1259809)
54. Public Sector. [https://weaver.com/industries/public-sector/](https://weaver.com/industries/public-sector/)
55. Redistricting, Race, and the Voting Rights Act. [https://www.nationalaffairs.com/publications/detail/redistricting-race-and-the-voting-rights-act](https://www.nationalaffairs.com/publications/detail/redistricting-race-and-the-voting-rights-act)
56. Program Services Guide. [https://www.weaverindustries.org/Resource.ashx?id=8](https://www.weaverindustries.org/Resource.ashx?id=8)
57. How Tech Can Optimize Snow Operations. [https://routeware.com/blog/how-tech-can-optimize-snow-removal-for-successful-winter-operations/](https://routeware.com/blog/how-tech-can-optimize-snow-removal-for-successful-winter-operations/)
58. Unified Sanitation Districts - Transforming Residential .... [https://www.fairfaxcounty.gov/publicworks/recycling-trash/unified-sanitation-districts](https://www.fairfaxcounty.gov/publicworks/recycling-trash/unified-sanitation-districts)
59. Artificial Intelligence-Based Optimization of Management of .... [https://www.intrans.iastate.edu/research/completed/artificial-intelligence-based-optimization-of-management-of-snow-removal/](https://www.intrans.iastate.edu/research/completed/artificial-intelligence-based-optimization-of-management-of-snow-removal/)
60. Identifying Best Practices for Snowplow Route Optimization. [https://www.clearroads.org/project/14-07/](https://www.clearroads.org/project/14-07/)
61. Snow Plow Route Optimization : r/gis. [https://www.reddit.com/r/gis/comments/2w4gru/snowplowroute_optimization/](https://www.reddit.com/r/gis/comments/2w4gru/snowplowroute_optimization/)
62. A New Formulation and Resolution Method for the p-Center .... [https://pubsonline.informs.org/doi/10.1287/ijoc.1030.0028](https://pubsonline.informs.org/doi/10.1287/ijoc.1030.0028)
63. The set partitioning problem in a quantum context. [https://optimization-online.org/wp-content/uploads/2023/06/Thesetpartitioningprobleminaquantum_context.pdf](https://optimization-online.org/wp-content/uploads/2023/06/Thesetpartitioningprobleminaquantum_context.pdf)
64. p-Center Problems. [https://repository.bilkent.edu.tr/server/api/core/bitstreams/237bb5bd-614f-4cda-a235-750f49f60c07/content](https://repository.bilkent.edu.tr/server/api/core/bitstreams/237bb5bd-614f-4cda-a235-750f49f60c07/content)
65. Set Partitioning and Applications. [https://www2.imm.dtu.dk/courses/02735/sppintro.pdf](https://www2.imm.dtu.dk/courses/02735/sppintro.pdf)
66. Regionalization - an overview. [https://www.sciencedirect.com/topics/earth-and-planetary-sciences/regionalization](https://www.sciencedirect.com/topics/earth-and-planetary-sciences/regionalization)
67. Political district determination using large-scale network .... [https://www.sciencedirect.com/science/article/abs/pii/S003801219600016X](https://www.sciencedirect.com/science/article/abs/pii/S003801219600016X)
68. Spatial Regionalization: Algorithms and Challenges. [https://dl.acm.org/doi/10.1145/3748777.3748813](https://dl.acm.org/doi/10.1145/3748777.3748813)
69. Regionalization | Definition, Examples & Principles - Lesson. [https://study.com/academy/lesson/the-regionalization-process-definition-examples.html](https://study.com/academy/lesson/the-regionalization-process-definition-examples.html)
70. Spatial regionalization based on optimal information .... [https://www.nature.com/articles/s42005-022-01029-4](https://www.nature.com/articles/s42005-022-01029-4)
71. Successful Approaches to Utilizing Bridge Management .... [https://onlinepubs.trb.org/onlinepubs/nchrp/docs/SCAN20-01.pdf](https://onlinepubs.trb.org/onlinepubs/nchrp/docs/SCAN20-01.pdf)
72. What Is Network Design?. [https://www.cisco.com/site/us/en/learn/topics/networking/what-is-network-design.html](https://www.cisco.com/site/us/en/learn/topics/networking/what-is-network-design.html)
73. Leverage manageX™, an advanced Bridge Management .... [https://www.assetintel.co/blogs/data-driven-bridge-management-prioritize-what-matters-most-with-managex](https://www.assetintel.co/blogs/data-driven-bridge-management-prioritize-what-matters-most-with-managex)
74. Optimizing Strategies in Bridge Asset Management Through .... [https://abc-utc.fiu.edu/wp-content/uploads/2026/03/Final-Report-Optimizing-Strategies-in-Bridge-Asset-Management-Through-Generating-Interactive-Reinforcement-Learning-GI-RL-Methods.pdf](https://abc-utc.fiu.edu/wp-content/uploads/2026/03/Final-Report-Optimizing-Strategies-in-Bridge-Asset-Management-Through-Generating-Interactive-Reinforcement-Learning-GI-RL-Methods.pdf)
75. AASHTOWare Bridge Management. [https://www.aashtoware.org/products/bridge/bridge-management/](https://www.aashtoware.org/products/bridge/bridge-management/)