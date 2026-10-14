"""Individually read remaining diversification questions and explicit proofs."""

REVIEWS = []


def concept(key, answer, prompt, proof, assumptions, finding="", claims="", kind="text"):
    """Save one scoped review, including its own derivation and source correction."""
    REVIEWS.append({
        "id": key, "answer": answer, "clean_prompt": prompt,
        "claim_ids": claims.split(), "review_note": proof,
        "source_finding": finding, "answer_kind": kind,
        "concept_review": {"derivation": proof, "assumptions": assumptions,
                           "basis": "explicit_conditions_and_independent_reasoning",
                           "current_law_claim": False},
    })


def mc(key, answer, prompt, proof, assumptions, finding="", claims=""):
    """Use the same evidence requirements for a multiple-choice review."""
    concept(key, answer, prompt, proof, assumptions, finding, claims, kind="multiple_choice")


REVIEWS.append({'id': 'MOCK-1-Q096',
 'answer': '②',
 'clean_prompt': '가. 증가하는 오목 기대효용은 위험회피를 나타낸다. 나. X>0에서 U(X)=sqrt(X)는 위험선호형이다. 다. 평균분산 효용 μ-Cσ²/2의 같은 σ>0에서 '
                 'C가 큰 투자자의 등효용선은 더 완만하다. 라. 이 평균분산 효용은 μ가 높고 σ²가 낮을수록 크다. 틀린 것끼리 묶으면? ① 가·나 ② 나·다 ③ 다·라 ④ '
                 '가·라',
 'claim_ids': [],
 'review_note': 'sqrt(X)의 2차미분=-1/(4X^(3/2))<0이므로 나가 틀리다. 등효용선 기울기 Cσ는 C와 함께 증가하므로 다도 틀리다. 가는 Jensen 부등식, 라는 '
                '효용식 부호와 일치한다.',
 'source_finding': '깨진 sqrt 수식과 평균분산 가정·동일 비교점을 명시했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': 'sqrt(X)의 2차미분=-1/(4X^(3/2))<0이므로 나가 틀리다. 등효용선 기울기 Cσ는 C와 함께 증가하므로 다도 틀리다. '
                                  '가는 Jensen 부등식, 라는 효용식 부호와 일치한다.',
                    'assumptions': 'MOCK26쪽 원본에서 제곱근을 직접 확인. C>0·같은 위험좌표 비교.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9-ADD-02',
 'answer': '④',
 'clean_prompt': '두 자산 비중 wX,wY와 표준편차σX,σY가 양수이며 상관0이다. 포트폴리오 표준편차는? ① wX²σX²+wY²σY² ② wXσX+wYσY ③ '
                 '|wXσX-wYσY| ④ sqrt(wX²σX²+wY²σY²)',
 'claim_ids': [],
 'review_note': '상관0이면 공분산항이0이고 분산은 wX²σX²+wY²σY²다. 그 양의 제곱근을 취한④가 표준편차다.',
 'source_finding': '원문① 일반 상관식도 ρ=0 대입 시④와 동치라 복수정답 여지가 있다. ①을 분산식으로 바꾸고 수식 OCR을 복원했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '상관0이면 공분산항이0이고 분산은 wX²σX²+wY²σY²다. 그 양의 제곱근을 취한④가 표준편차다.',
                    'assumptions': 'P3 464쪽 원본 수식 확인. 비퇴화 조건에서 항등식 비교.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9-ADD-04',
 'answer': '②',
 'clean_prompt': '동일기대와공통무위험차입·대출조건을가정하며 M은위험자산의공통접점시장포트폴리오다. 평균분산 효율적투자의과정은? '
                 'ㄱ:지배원리로무위험자산을포함한최종투자기회집합의효율경계를구한다. ㄴ:기대수익률·위험·공분산을추정한다. ㄷ:선택비중에따라무위험자산과M의조합으로투자를실행한다. '
                 'ㄹ:효율경계와무차별효용곡선의접점에서최적포트폴리오를선택한다. ①ㄱ→ㄴ→ㄷ→ㄹ ②ㄴ→ㄱ→ㄹ→ㄷ ③ㄷ→ㄹ→ㄱ→ㄴ ④ㄱ→ㄷ→ㄹ→ㄴ',
 'claim_ids': [],
 'review_note': '추정치가경계계산에선행하고, 그경계중선호와접하는최적점을선택한후해당비중으로실행하므로②이다. '
                '공통무위험자산과공통접점M을가정했으므로최적조합은선택된무위험자산/M비중으로실행된다.',
 'source_finding': '원문마지막단계의무위험자산·시장포트폴리오표현과지배원리·접점을복원했다. 위험자산만의프런티어와무위험자산편입후최종프런티어의혼동을막는가정을명시했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '추정치가경계계산에선행하고, 그경계중선호와접하는최적점을선택한후해당비중으로실행하므로②이다. '
                                  '공통무위험자산과공통접점M을가정했으므로최적조합은선택된무위험자산/M비중으로실행된다.',
                    'assumptions': 'P3 465쪽 원본 ㄱㄴㄷㄹ·선택지 확인. 최종 투자집합에 허용 무위험자산/차입 조건도 먼저 반영한다.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9T08-CORE',
 'answer': '③',
 'clean_prompt': '포트폴리오전략설명중틀린것은? ①지수펀드의벤치마크추종은대표적패시브전략이다. ②단순매입·보유는선택자산을계속보유하는전략이며처음종목선정은무작위또는재량적일수있다. '
                 '③포뮬러플랜의변동비율법은사전비중조절규칙을따르는것이아니라그때그때증권시장을예측해무위험·위험자산비중을조절하는시장투자적기포착전략과동일하다. '
                 '④기대시장초과수익이양수라는CAPM전망에서다른조건이같다면큰베타종목의예상초과수익이더크다.',
 'claim_ids': [],
 'review_note': '사전 규칙은 관측가격·비중 등 입력으로 실행할 수 있으므로 전망을 새로 예측할 필요가 없다는 반례가 있어③이 틀리다. ④는 β×양의 시장프리미엄 관계다.',
 'source_finding': '원문③의포뮬러플랜변동비율법과시장투자적기포착대조를복원했다. 원해설의매입보유=반드시무작위선정및강세전망=실현수익보장은채택하지않는다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '사전 규칙은 관측가격·비중 등 입력으로 실행할 수 있으므로 전망을 새로 예측할 필요가 없다는 반례가 있어③이 틀리다. ④는 β×양의 '
                                  '시장프리미엄 관계다.',
                    'assumptions': 'P3 458쪽. 전략 정의와 조건부 모형 관계를 구별.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9T08-SUP-01',
 'answer': '④',
 'clean_prompt': '별도종목알파예측없이실행하는소극적방식과거리가먼것은? ①단순매입·보유전략:사전에정한분산묶음보유. ②지수펀드투자전략:지정지수추종. '
                 '③평균분할투자전략:같은지수묶음의정액정기매수. ④트레이너-블랙모형이용전략:개별종목예상알파·잔차분산으로액티브비중최적화.',
 'claim_ids': ['L320'],
 'review_note': '④는 종목별 비정상 기대수익 예측을 사용해 벤치마크와 다른 비중을 취하므로 액티브 접근이다. 나머지는 제시한 조건에서 별도 알파예측을 요구하지 않는다.',
 'source_finding': '정액매수나 매입보유라는 행위만으로 모든 운용이 패시브라고 일반화하지 않도록 대상·재량 조건을 한정했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '④는 종목별 비정상 기대수익 예측을 사용해 벤치마크와 다른 비중을 취하므로 액티브 접근이다. 나머지는 제시한 조건에서 별도 '
                                  '알파예측을 요구하지 않는다.',
                    'assumptions': 'P3 459쪽. 최초 묶음 선정과 정액매수 대상도 명시.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9T08-SUP-02',
 'answer': '①',
 'clean_prompt': '적극적투자전략중개별종목선택보다자산군전체노출의시점조절에해당하는것은? ①시장투자적기포착전략:시장전망에따라주식시장묶음과무위험자산간비중조절. '
                 '②베타계수이용전략:목표베타에맞는개별주식선택. ③내재가치추정전략:저평가종목선택. ④트레이너-블랙모형이용전략:개별종목예상알파·잔차분산에따른액티브비중계산.',
 'claim_ids': [],
 'review_note': '①는 주식 묶음 내부 종목을 고르지 않고 시장위험 전체 노출을 조절한다. 나머지는 주어진 설명대로 개별증권 선택·배분이다.',
 'source_finding': '포뮬러 플랜도 반드시 새 시장예측을 한다는 해설의 일반화를 사용하지 않았다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '①는 주식 묶음 내부 종목을 고르지 않고 시장위험 전체 노출을 조절한다. 나머지는 주어진 설명대로 개별증권 선택·배분이다.',
                    'assumptions': 'P3 459쪽. 교재의 이름만이 아니라 각 전략이 수행하는 작업을 명시.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9T08-SUP-03',
 'answer': '④',
 'clean_prompt': '잔차간무상관인Treynor-Black모형에서모든예측알파는양수, 잔차분산v_i>0, q_i=α_i/v_i, w_i=q_i/Σq_j로둔다. 틀린것은? '
                 '①적극적종목선택으로초과수익을추구하면서분산으로잔차위험을줄이고자한다. ②초과수익가능성과잔차위험간균형을고려해최적비중을구한다. '
                 '③CAPM을요구수익기준으로쓰면알파는예측수익률에서SML요구수익률을뺀값이다. ④다른조건을고정할때자기알파가커질수록자기투자비중은낮아진다.',
 'claim_ids': ['L320'],
 'review_note': '잔차무상관에서알파-잔차분산목적함수의FOC는비중을α_i/v_i에비례시킨다. 양의알파조건에서∂w_i/∂α_i=Σj≠i '
                'q_j/(v_i(Σq_j)^2)>0이므로④가틀리다.③은알파의SML기준정의다. '
                '원문예시0.8,-0.5,0.3은알파/표준편차가아닌q값으로주어진별도예시라면1.33,-0.83,0.5의정규화계산을유지할수있지만알파순위만으로비중순위를단정할수없다.',
 'source_finding': '대체되었던원문③SML요구수익계산을복원했다. 평가비율α/잔차표준편차를그대로비중에사용한해설은α/잔차분산으로교정했고④단조성의양의알파조건을명시했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '잔차무상관에서알파-잔차분산목적함수의FOC는비중을α_i/v_i에비례시킨다. 양의알파조건에서∂w_i/∂α_i=Σj≠i '
                                  'q_j/(v_i(Σq_j)^2)>0이므로④가틀리다.③은알파의SML기준정의다. '
                                  '원문예시0.8,-0.5,0.3은알파/표준편차가아닌q값으로주어진별도예시라면1.33,-0.83,0.5의정규화계산을유지할수있지만알파순위만으로비중순위를단정할수없다.',
                    'assumptions': 'P3 460쪽. 2개 이상 양의 알파, 잔차 무상관, 제약없는 기본모형.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9T09-CORE',
 'answer': '③',
 'clean_prompt': '수익률측정중틀린설명은? ①외부흐름없는기간이다른투자안을비교할때기간차이를반영한연복리수익률을사용할수있다. ②같은간격기간수익률이-100%보다크면산술평균은기하평균이상이다. '
                 '③운용자가중도투자·회수를결정한영향까지평가하려는경우에도그현금흐름의시점·규모를제외한기간수익률의기하연결만으로평가하는것이항상더적절하다. '
                 '④과거누적성장률의연평균화에는기하평균이적절하고동일분포단일기간수익률의기대값추정에는산술평균을사용할수있다.',
 'claim_ids': [],
 'review_note': '외부입출금의시점·규모영향까지평가하려면그현금흐름을반영하는금액가중수익률등이필요하므로③의항상더적절하다는주장은틀리다. AM≥GM은1+r>0의산술기하평균부등식이다. '
                '과거복리누적성과미래단일기간평균은각각곱셈·기대값이라는다른대상이다.',
 'source_finding': '원문③의재량권에따른성과지표선택을복원했다. 재량권없음은입출금자체가없다는뜻이아니며, 외부흐름발생시단순보유기간기하평균과TWR구간연결을구별한다. '
                   'IRR은다중해등추가한계가있어유일한지표라고단정하지않는다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '외부입출금의시점·규모영향까지평가하려면그현금흐름을반영하는금액가중수익률등이필요하므로③의항상더적절하다는주장은틀리다. '
                                  'AM≥GM은1+r>0의산술기하평균부등식이다. 과거복리누적성과미래단일기간평균은각각곱셈·기대값이라는다른대상이다.',
                    'assumptions': 'P3 461쪽. 흐름 통제와 흐름 존재를 구분하고 평균의 통계적 전제를 명시.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9-ADD-11',
 'answer': '①',
 'clean_prompt': '개별종목을 고르는 작업이 아닌 것은? ① 사전에 정한 포뮬러 규칙에 따라 주식지수묶음과 채권묶음의 비중 조정 ② 개별주식 내재가치 추정 ③ 목표베타에 맞는 '
                 '개별주식 선별 ④ 기업규모 기준으로 개별주식 선별',
 'claim_ids': [],
 'review_note': '①는 이미 정한 자산군 묶음 사이의 배분 조절이며 나머지는 주어진 설명에서 개별종목을 선별한다.',
 'source_finding': '포뮬러 플랜을 반드시 예측에 의한 초과수익 보장 전략으로 설명하지 않는다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '①는 이미 정한 자산군 묶음 사이의 배분 조절이며 나머지는 주어진 설명에서 개별종목을 선별한다.',
                    'assumptions': 'P3 468쪽. 전략명칭이 아닌 구체적 실행내용 비교.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q029',
 'answer': '포뮬러 플랜',
 'clean_prompt': '다음후보중개별종목의선택대신주식묶음·채권묶음의비중을사전에정한규칙으로조절하는접근은무엇인가? [내재가치추정, RVAR이용, 베타계수이용, 트레이너-블랙모형, '
                 '포뮬러플랜]',
 'claim_ids': [],
 'review_note': '종목선별이 아니라 자산군 간 규칙적 배분인 포뮬러 플랜이다.',
 'source_finding': '원문후보목록을모두보존했다. 각지표가다른목적에전혀쓰이지않는다는배타적주장이아니라주어진실행방식의명칭을묻는다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '종목선별이 아니라 자산군 간 규칙적 배분인 포뮬러 플랜이다.',
                    'assumptions': 'NOTE87쪽. 이 문항에 정의한 규칙적 자산배분 방식.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q030',
 'answer': '높게',
 'clean_prompt': '트레이너-블랙 기본모형에서 종목별 잔차분산 v_i>0, q_i=α_i/v_i, w_i=q_i/Σq_j다. 비교하는 모든 종목의 잔차분산이 같고 알파가 모두 '
                 '양수라면, 초과수익 알파가 큰 증권일수록 최적투자비중은 (높게/낮게) 구성되는가?',
 'claim_ids': ['L320'],
 'review_note': '공통 잔차분산 v이면 w_i=α_i/Σα_j이며 양의 공통분모이므로 알파가 큰 종목의 비중이 높다. 종목별 잔차분산이 다르면 알파만으로 비중순위를 판단할 수 없다.',
 'source_finding': '기존 교정판의 한 종목 알파 변화에 대한 비교정태 문제를 원문의 종목간 비교로 복원했다. 원문의 포트폴리오 비체계적 위험이라는 분모 표현은 종목별 잔차분산으로 '
                   '교정하고 동일분산·양의 알파 조건을 명시했다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '공통 잔차분산 v이면 w_i=α_i/Σα_j이며 양의 공통분모이므로 알파가 큰 종목의 비중이 높다. 종목별 잔차분산이 다르면 '
                                  '알파만으로 비중순위를 판단할 수 없다.',
                    'assumptions': 'NOTE87쪽. 양의 다른 알파 합과 잔차분산 고정 전제.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})


REVIEWS.append({'id': 'MOCK-1-Q097',
 'answer': '②',
 'clean_prompt': '위험자산 A의 기대수익률7%, 표준편차10%다. A40%와 무위험자산60%로 구성한 동일기간 포트폴리오의 표준편차는? ①0% ②4% ③6% ④7%',
 'claim_ids': [],
 'review_note': '무위험자산의 분산·공분산은0이므로 σp=|.4|×.1=.04다.',
 'source_finding': '',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '무위험자산의 분산·공분산은0이므로 σp=|.4|×.1=.04다.',
                    'assumptions': 'MOCK26쪽. 고정비중·무위험수익 확정.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'MOCK-1-Q098',
 'answer': '①',
 'clean_prompt': 'rf=10%, E[Rm]=15%, Var(Rm)=.4, Cov(RA,Rm)=.8이다. CAPM 요구수익률을 할인율로 쓰고, 1년 뒤 배당 D1=1000원 이후 '
                 '연10% 영구성장하는 고든모형 가격은? ①10000원 ②11000원 ③15000원 ④15500원',
 'claim_ids': [],
 'review_note': 'β=.8/.4=2, k=.10+2×(.15-.10)=.20. k>g=.10에서 P=D1/(k-g)=1000/.10=10000원이다.',
 'source_finding': '원문 예상배당금의 시점을 D1로 명확히 했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': 'β=.8/.4=2, k=.10+2×(.15-.10)=.20. k>g=.10에서 P=D1/(k-g)=1000/.10=10000원이다.',
                    'assumptions': 'MOCK27쪽. 배당1000원이 D1이며 모멘트는 같은 단위.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'MOCK-1-Q099',
 'answer': '③',
 'clean_prompt': '표준 CAPM의 가정을 잘못 설명한 것은? ①평균과 분산으로 선택하며 동일분산에서는 높은평균, 동일평균에서는 낮은분산을 선호한다. ②모든 투자자는 공통의 단일 '
                 '투자기간을 가지며 그 이후 결과는 고려하지 않는다. ③모든 위험자산이 거래 가능하고 무위험자산이 존재하며 얼마든지 차입·대출할 수 있으나 차입금리는 대출금리보다 '
                 '높아야 한다. ④경제상황과 미래수익률 분포에 관해 동질적 기대를 가진다.',
 'claim_ids': ['L318'],
 'review_note': '이 표준모형은 동일한 무위험금리로 차입·대출할 수 있다고 가정하므로 ③이 틀리다.',
 'source_finding': '원문①의 평균과분산 선호,②기간이후 무시,③무제한차입대출 및④수익률분포 기대를 복원했다. 원문③의 공개거래금융자산 한정은 표준CAPM 모든위험자산 거래가능 '
                   '가정으로 정리하고 차입대출금리 동일가정 위반을 정답③으로 유지했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '이 표준모형은 동일한 무위험금리로 차입·대출할 수 있다고 가정하므로 ③이 틀리다.',
                    'assumptions': 'MOCK27쪽. 차입제약 등 확장모형 제외.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'MOCK-1-Q100',
 'answer': '③',
 'clean_prompt': 'A,B,C의 기대수익률과 양의 표준편차σ가 같다. 상관 AB=.8, AC=.1, BC=-.3이다. 분산이 가장 작은 선택은? ① A100% ② A50%·B50% '
                 '③ B50%·C50% ④ A50%·C50%',
 'claim_ids': [],
 'review_note': '두 자산 동일비중의 분산은 .5σ²(1+ρ)다. 순서대로 σ²,.9σ²,.35σ²,.55σ²이므로 ③이 최소다.',
 'source_finding': '',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '두 자산 동일비중의 분산은 .5σ²(1+ρ)다. 순서대로 σ²,.9σ²,.35σ²,.55σ²이므로 ③이 최소다.',
                    'assumptions': 'MOCK27쪽 상관표와 선택지 대조. 비교대상은 제시4개이며 전체3자산 최적화가 아니다.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'MOCK-2-Q096',
 'answer': '②',
 'clean_prompt': '효용 U=E[R]-C Var(R)/2, C=8, rf=4%, 위험자산 A의 평균18%·표준편차20%다. A비중y와 무위험비중1-y에서 최적y를 정수%로 '
                 '반올림하면? ①9% ②44% ③56% ④91%',
 'claim_ids': [],
 'review_note': "U=.04+.14y-4×.04y². U'=.14-.32y=0에서 y=.4375. U''=-.32<0이므로 최댓값이며 44%로 반올림한다.",
 'source_finding': '위험회피계수의 효용식과 반올림 기준을 추가했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': "U=.04+.14y-4×.04y². U'=.14-.32y=0에서 y=.4375. U''=-.32<0이므로 최댓값이며 44%로 "
                                  '반올림한다.',
                    'assumptions': 'MOCK53쪽. 평균분산 효용의 1/2 계수 명시.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'MOCK-2-Q097',
 'answer': '③',
 'clean_prompt': '공통 단일기간·동질기대·동일 무위험차입대출을 가정하는 표준 CAPM 균형에서 시장포트폴리오 M의 설명 중 틀린 것은? ①모든 위험자산을 시장가치 비중으로 포함하는 '
                 '분산포트폴리오다. ②토빈의 분리정리 아래 위험자산 묶음으로 공통의 효율적 포트폴리오 M을 선택한다. ③무위험자산과 M을 연결하는 자본시장선 CML은 자본배분선 '
                 'CAL에 속하지 않는다. ④투자자는 위험선호와 관계없이 동일한 위험자산 묶음 M을 선택하고 위험선호에 따라 M과 무위험자산의 비중을 조절한다.',
 'claim_ids': ['L318'],
 'review_note': 'CML은 접점 M을 쓰는 특별한 CAL이다. 따라서 CAL이 아니라고 한 ③이 틀리다.',
 'source_finding': '원문③의 CML을 CAL이라고 부른 진술은 포함관계상 틀렸다고 할 수 없다. '
                   '다른3보기의분리정리·시가가중·공통위험묶음을유지하고③만CAL소속을부정하는오답으로바꿨다. 위험자산보유가0인경우에도조건부공통위험묶음의의미이다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': 'CML은 접점 M을 쓰는 특별한 CAL이다. 따라서 CAL이 아니라고 한 ③이 틀리다.',
                    'assumptions': 'MOCK53쪽. 공통투자집합·동일 차입대출금리의 표준균형.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'MOCK-2-Q098',
 'answer': '②',
 'clean_prompt': 'CAPM에서 rf=6%, E[Rm]=10%, Cov(RJ,Rm)=.0215, Var(Rm)=.01이다. J 요구수익률은? ①6% ②14.6% ③16% ④21.5%',
 'claim_ids': [],
 'review_note': 'β=.0215/.01=2.15. k=.06+2.15×(.10-.06)=.146이다.',
 'source_finding': '',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': 'β=.0215/.01=2.15. k=.06+2.15×(.10-.06)=.146이다.',
                    'assumptions': 'MOCK53쪽. 시장10%는 프리미엄이 아니라 총기대수익률.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'MOCK-2-Q099',
 'answer': '①',
 'clean_prompt': '가. CAPM 균형에서 무위험수익률5%, A의 기대수익률8%·베타.3, B의 기대수익률7%일 때 B의 베타는? 나. 별도로 무위험수익률3%, 시장기대수익률6%이고 '
                 'X의 베타1.5, Y의 베타.5다. 샤프 단일지표모형에서 X와 Y를 동일금액 보유한 포트폴리오 베타는? 두 답의 조합은? ① .2,1.0 ② .26,1.0 ③ '
                 '.2,2.0 ④ .26,2.0',
 'claim_ids': [],
 'review_note': '가: 시장프리미엄=(.08-.05)/.3=.10, βB=.02/.10=.2. 나: βp=.5×1.5+.5×.5=1이다.',
 'source_finding': '원문 해설의 모든 포트폴리오 샤프비율 동일 주장은 사용하지 않고 CAPM의 베타당 초과수익률을 사용했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '가: 시장프리미엄=(.08-.05)/.3=.10, βB=.02/.10=.2. 나: βp=.5×1.5+.5×.5=1이다.',
                    'assumptions': 'MOCK54쪽. 베타의 기준시장 동일.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'MOCK-2-Q100',
 'answer': '①',
 'clean_prompt': '한 기간 실제 수익률이 RA=.24+1.2F, RB=.12+.6F이고 잔차위험이0이며 rf=.06이다. 공매도·차입이 자유롭고 비용이 없다. 초기순투자0, '
                 '요인노출0, 양의 확정이익인 조합은? ① A1억 매수+무위험1억 매수-B2억 공매도 ② A2억 매수-B2억 공매도 ③ A1억 공매도+무위험1억 차입+B2억 매수 '
                 '④ A2억 공매도+B2억 매수',
 'claim_ids': ['L319'],
 'review_note': '① 손익(억원)=1(.24+1.2F)+1(.06)-2(.12+.6F)=.06으로 600만원 확정이다. ③은 -.06, ②④는 요인노출이 남는다.',
 'source_finding': '기대수익과 베타만 같다고 위험이 모두 상쇄되지는 않으므로 실제 요인식·잔차0·비용제외를 명시했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '① 손익(억원)=1(.24+1.2F)+1(.06)-2(.12+.6F)=.06으로 600만원 확정이다. ③은 -.06, ②④는 '
                                  '요인노출이 남는다.',
                    'assumptions': 'MOCK54쪽. 잔차0을 명시한 정확한 복제 예시.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9T04-CORE',
 'answer': '①',
 'clean_prompt': '표준 CAPM에서 위험자산만의 효율곡선 AMX에 Rf=8%에서 그은 접선이 M(평균18%, 표준편차14%)을 지난다. 틀린 것은? ① 무위험자산 편입 후에도 최종 '
                 '효율적 투자집합은 위험자산 곡선 AMX 전체 그대로다. ② 최대 샤프비율의 CAL이 CML이다. ③ 그 기울기는 약.7143이다. ④ M비중0~1은 대출, '
                 '1초과는 차입조합이다.',
 'claim_ids': ['L318'],
 'review_note': '무위험자산과 접점M을 조합한 CML이 새 효율집합이다. 기울기=(.18-.08)/.14=.7142857이고 ①만 틀리다.',
 'source_finding': 'OCR에서 빠진 도표 조건을 텍스트로 복원했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '무위험자산과 접점M을 조합한 CML이 새 효율집합이다. 기울기=(.18-.08)/.14=.7142857이고 ①만 틀리다.',
                    'assumptions': 'P3 444쪽 원본 이미지의 8·18·14와 곡선/접선을 확인. 차입대출금리 동일.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9T04-SUP-02',
 'answer': '②',
 'clean_prompt': '평균-표준편차 도표에서 Rf·M·나를 지나는 접선과 Rf·A를 지나는 더 낮은 기울기의 직선이 있다. 표준 CAPM 전제에서 틀린 설명은? ①Rf·M·나를 지나는 '
                 '선은 CML이다. ②Rf와 A를 연결한 선은 SML이다. ③M은 시장포트폴리오다. ④먼저 공통의 M을 선택하고 이후 위험선호에 따라 무위험자산과 M의 비중을 '
                 '정하여 대출 또는 차입포트폴리오를 선택한다.',
 'claim_ids': ['L318'],
 'review_note': 'Rf-A는 해당 위험포트폴리오의 CAL이다. SML은 베타를 가로축으로 하는 가격선이므로 ②가 틀리다.',
 'source_finding': '누락 도표의 축과 두 직선을 복원했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': 'Rf-A는 해당 위험포트폴리오의 CAL이다. SML은 베타를 가로축으로 하는 가격선이므로 ②가 틀리다.',
                    'assumptions': 'P3 447쪽 원본 축과 점의 위치를 직접 확인.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9T05-SUP-03',
 'answer': '①',
 'clean_prompt': '같은 CAPM SML 도표에서 가와 나는 선 위, 다와 라는 선 아래에 있다. 가의 기대수익은 나보다 높고 베타는 나보다 낮으며 SML 기울기는 양수다. SML '
                 '대비 양의 알파가 가장 큰 자산은? ① 가 ② 나 ③ 다 ④ 라',
 'claim_ids': [],
 'review_note': 'α가-α나=(μ가-μ나)-λ(β가-β나)>0이다. 다·라는 음의 알파이므로 가가 최대다.',
 'source_finding': '가장 저평가를 금액가치의 절대비교로 오해하지 않도록 SML 대비 알파를 기준으로 명시했다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': 'α가-α나=(μ가-μ나)-λ(β가-β나)>0이다. 다·라는 음의 알파이므로 가가 최대다.',
                    'assumptions': 'P3 451쪽 원본 점위치를 확인. 같은 수익률 축에서 알파의 수직거리 비교.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9-ADD-06',
 'answer': '③',
 'clean_prompt': '표준 CAPM 평균-표준편차 도표에서 CML은 시장포트폴리오 T에 접한다. 투자자 d의 최적점은 Rf와 T 사이, e의 최적점은 T 오른쪽이다. 이 도표에서 작은 '
                 'T비중을 더 보수적인 선택이라고 정의할 때 틀린 것은? ①무위험자산을 포함한 최적포트폴리오 선택이다. ②T는 시장포트폴리오다. ③e는 d보다 보수적인 선택이며 '
                 'T비중이1보다 작다. ④위험자산만의 효율곡선 대신 무위험자산을 포함한 CML 위에서 최적 효율적 조합을 선택한다.',
 'claim_ids': ['L318'],
 'review_note': 'e의 표준편차가 T보다 크고 σp=yσT이므로 y>1, 무위험비중1-y<0인 차입조합이다. ③이 틀리다.',
 'source_finding': '원문의 보수적이라는 상대적 용어를 삭제하지 않고 d와e간 위험자산비중 비교로 명시했다. e는 차입조합이고 d는 대출조합이므로③이틀리다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': 'e의 표준편차가 T보다 크고 σp=yσT이므로 y>1, 무위험비중1-y<0인 차입조합이다. ③이 틀리다.',
                    'assumptions': 'P3 466쪽 원본 T,d,e 위치 확인. CML의 양의위험 구간.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9T07-SUP-02',
 'answer': '④',
 'clean_prompt': 'F는 시장수익률 Rm 자체와 구분되는 평균0 공통요인충격이고 잔차 ε의 평균은0이다. 다음 중 단일요인 APT에서 사용하는 공통요인 수익률 생성식은? ① '
                 'E[Rp]=rf+{(E[Rm]-rf)/σm}σp ② E[Ri]=rf+βi(E[Rm]-rf) ③ Ri=αi+βiRm+εi ④ Rp=E[Rp]+bpF+εp',
 'claim_ids': ['L319'],
 'review_note': '①은 CML,②는 CAPM의 SML,③은 시장수익률을 설명변수로 하는 증권특성선/단일지표모형,④는 일반적 평균0 요인충격에 대한 단일요인 수익률 생성식이다. '
                '정답④. 생성식만으로 APT 가격제약이 자동성립하지 않으며 분산가능잔차·무차익 등 추가전제 아래 E[R]=rf+bλ라는 기대수익 가격식을 얻는다. 요인충격F와 '
                '위험프리미엄λ는다르다.',
 'source_finding': '원문네수식을그대로식별대상으로복원하고 APT전체와생성식하나를동일시하는발문만 단일요인APT에서사용하는생성식으로교정. '
                   '선택지에추가됐던거짓조건/가격제약은삭제하고해설에서한계설명.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': '①은 CML,②는 CAPM의 SML,③은 시장수익률을 설명변수로 하는 증권특성선/단일지표모형,④는 일반적 평균0 요인충격에 대한 '
                                  '단일요인 수익률 생성식이다. 정답④. 생성식만으로 APT 가격제약이 자동성립하지 않으며 분산가능잔차·무차익 등 추가전제 아래 '
                                  'E[R]=rf+bλ라는 기대수익 가격식을 얻는다. 요인충격F와 위험프리미엄λ는다르다.',
                    'assumptions': 'P3 457쪽. MIT 단일요인 이론과 대조.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'S3C9T09-SUP-02',
 'answer': '④',
 'clean_prompt': '각 기간이1년이다. t0에 주식1주를10000원 매수하고 t1에 배당1000원을 인출한 직후 같은 주식1주를12000원에 추가매수한다. t2에 2주 합계 '
                 '배당2000원과 매각대금28000원을 인출한다. 비용은 없다. 틀린 것은? ① 기간수익률은30%,25%다. ② 산술평균27.5%다. ③ 연환산 시간가중수익률 '
                 '약27.48%다. ④ 연간 금액가중수익률은 시간가중수익률보다 높다.',
 'claim_ids': [],
 'review_note': 'r1=(12000-10000+1000)/10000=.3; r2=(28000+2000-24000)/24000=.25. '
                'TWR=sqrt(1.3×1.25)-1=.274754878. IRR은 -10000-11000/(1+r)+30000/(1+r)²=0의 r>-1 해 .267278185. '
                '따라서 IRR<TWR이고④가 틀리다.',
 'source_finding': '교재 IRR 약26.8%를26.73%로, 기하평균27.47%를 보통 반올림27.48%로 교정했다. 투입금액이 같으면 기간구분이 없어지는 것은 아니다.',
 'answer_kind': 'multiple_choice',
 'concept_review': {'derivation': 'r1=(12000-10000+1000)/10000=.3; r2=(28000+2000-24000)/24000=.25. '
                                  'TWR=sqrt(1.3×1.25)-1=.274754878. IRR은 -10000-11000/(1+r)+30000/(1+r)²=0의 '
                                  'r>-1 해 .267278185. 따라서 IRR<TWR이고④가 틀리다.',
                    'assumptions': 'P3 463쪽 실제 현금흐름과 표 대조. 경계 배당인출 후 추가납입 및1년 간격 명시.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})


REVIEWS.append({'id': 'NOTE-S3C9-Q001',
 'answer': '5%',
 'clean_prompt': 'X의 수익률은 호황20%(확률30%), 불황-30%(확률20%), 정상10%(확률50%)다. 기대수익률은?',
 'claim_ids': [],
 'review_note': '0.2×0.3-0.3×0.2+0.1×0.5=0.05=5%다.',
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': '0.2×0.3-0.3×0.2+0.1×0.5=0.05=5%다.',
                    'assumptions': 'NOTE84쪽. 세 상태가 배타적이고 전체 확률합1이다.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q002',
 'answer': 'wE(RA)+(1-w)E(RB)',
 'clean_prompt': '초기 투자비중이 A에 w, B에 1-w이고 동일 기간 단순수익률이 RA,RB다. 비용이 없을 때 기대수익률은?',
 'claim_ids': [],
 'review_note': 'Rp=wRA+(1-w)RB에 기대값의 선형성을 적용한다. 상관은 기대값 가중합을 바꾸지 않는다.',
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': 'Rp=wRA+(1-w)RB에 기대값의 선형성을 적용한다. 상관은 기대값 가중합을 바꾸지 않는다.',
                    'assumptions': 'NOTE84쪽. 고정 초기비중과 동일 측정기간.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q003',
 'answer': 'wX²σX²+wY²σY²+2wXwYσXσYρXY',
 'clean_prompt': '고정비중 wX,wY, 수익률 표준편차 σX,σY와 상관ρXY인 두 자산 포트폴리오의 분산을 쓰시오.',
 'claim_ids': [],
 'review_note': 'Var(wX RX+wY RY)를 전개하면 두 분산항과 2wXwY Cov(RX,RY)가 생긴다. Cov=σXσYρXY다.',
 'source_finding': '분산과 표준편차를 구분하고 깨진 수식을 복원했다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': 'Var(wX RX+wY RY)를 전개하면 두 분산항과 2wXwY Cov(RX,RY)가 생긴다. Cov=σXσYρXY다.',
                    'assumptions': 'NOTE84쪽. 유한한 2차 모멘트, 표준편차는 양수.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q004',
 'answer': '낮을수록',
 'clean_prompt': '두 자산의 양의 투자비중과 양의 표준편차를 고정하면, 상관계수가 (높을수록 / 낮을수록) 합산분산이 작아지는가?',
 'claim_ids': [],
 'review_note': '합산분산의 상관에 대한 미분은 2wXwYσXσY>0이므로 상관이 낮을수록 분산이 작다.',
 'source_finding': '숏 비중이면 방향이 달라질 수 있어 양의 비중 조건을 명시했다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '합산분산의 상관에 대한 미분은 2wXwYσXσY>0이므로 상관이 낮을수록 분산이 작다.',
                    'assumptions': 'NOTE84쪽. 비중 부호와 개별위험을 고정한다.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q005',
 'answer': '0',
 'clean_prompt': 'wX,wY,σX,σY가 모두 양수다. 포트폴리오 표준편차가 sqrt(wX²σX²+wY²σY²)이면 상관계수는?',
 'claim_ids': [],
 'review_note': '일반 분산식과 제곱한 제시식을 비교하면 2wXwYσXσYρ=0이다. 계수가 양수이므로 ρ=0이다.',
 'source_finding': 'OCR 누락 수식과 상관을 유일하게 추론할 비퇴화 조건을 복원했다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '일반 분산식과 제곱한 제시식을 비교하면 2wXwYσXσYρ=0이다. 계수가 양수이므로 ρ=0이다.',
                    'assumptions': 'NOTE84쪽. 비중이나 표준편차가0인 퇴화사례 제외.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q006',
 'answer': '+1, -1',
 'clean_prompt': '두 자산의 투자비중과 표준편차가 모두 양수다. 상관계수가 각각 얼마일 때 σp=wXσX+wYσY, σp=|wXσX-wYσY|가 되는가?',
 'claim_ids': [],
 'review_note': '분산식의 교차항이 각각 +2ab,-2ab일 때 (a+b)²,(a-b)²다. 제곱근은 절댓값이므로 순서대로 +1,-1이다.',
 'source_finding': '원문ρ=-1 표준편차식의 절댓값누락을수정했다. 두표준편차가양수여야상관이정의되고역으로±1을유일하게결정할수있으므로이조건도명시.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '분산식의 교차항이 각각 +2ab,-2ab일 때 (a+b)²,(a-b)²다. 제곱근은 절댓값이므로 순서대로 +1,-1이다.',
                    'assumptions': 'NOTE84쪽. 양의 개별 표준편차와 양의 비중.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q007',
 'answer': 'Y',
 'clean_prompt': '(기대수익률,표준편차)가 X=(10%,10%), Y=(10%,5%), Z=(7%,5%)다. 평균은 높고 위험은 낮은 것을 선호할 때 다른 두 자산을 지배하는 '
                 '자산은?',
 'claim_ids': [],
 'review_note': 'Y는 X와 기대수익률이 같고 위험이 낮다. Y는 Z와 위험이 같고 기대수익률이 높으므로 둘 모두 지배한다.',
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': 'Y는 X와 기대수익률이 같고 위험이 낮다. Y는 Z와 위험이 같고 기대수익률이 높으므로 둘 모두 지배한다.',
                    'assumptions': 'NOTE84쪽. 세 개별자산 비교이며 미지의 상관을 사용하는 혼합 최적화는 아니다.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q008',
 'answer': '0.6',
 'clean_prompt': 'σX=0.2, σY=0.3, 상관=-1이다. X비중w, Y비중1-w의 분산을 최소화하는 w는?',
 'claim_ids': [],
 'review_note': 'σp=|0.2w-0.3(1-w)|=|0.5w-0.3|이다. w=0.6에서0으로 최소다.',
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': 'σp=|0.2w-0.3(1-w)|=|0.5w-0.3|이다. w=0.6에서0으로 최소다.',
                    'assumptions': 'NOTE85쪽. 고정비중·동일기간이며 w∈[0,1].',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q009',
 'answer': '오목, 가파르다',
 'clean_prompt': '부 W에 대해 증가하는 기대효용 U(W)의 위험회피는 (오목/볼록)으로 표현된다. 평균-표준편차 효용 μ-Cσ²/2에서 같은 σ>0일 때 C가 큰 투자자의 '
                 '무차별곡선은 더 (완만하다/가파르다).',
 'claim_ids': [],
 'review_note': '오목효용은 Jensen 부등식으로 확실한 평균 부를 위험한 부보다 선호한다. 등효용선 μ=u+Cσ²/2의 기울기는 Cσ이므로 C가 클수록 가파르다.',
 'source_finding': '일반 효용곡선과 평균-위험 무차별곡선의 축 및 비교위치를 명시했다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '오목효용은 Jensen 부등식으로 확실한 평균 부를 위험한 부보다 선호한다. 등효용선 μ=u+Cσ²/2의 기울기는 Cσ이므로 C가 '
                                  '클수록 가파르다.',
                    'assumptions': 'NOTE85쪽. 서로 다른 두 좌표계를 분리하고 같은 σ에서 비교.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q010',
 'answer': 'O',
 'clean_prompt': '부에 대한 효용함수 u(W)가 두 번 미분 가능하고 u′(W)>0, u″(W)<0인 위험회피 투자자라면, 효용이 증가하되 한계효용은 체감하여 그래프가 가로축에 '
                 '대해 오목하다. O/X?',
 'claim_ids': [],
 'review_note': "U'>0은 효용증가, U''<0은 U'의 감소를 뜻하므로 O다.",
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': "U'>0은 효용증가, U''<0은 U'의 감소를 뜻하므로 O다.",
                    'assumptions': 'NOTE85쪽. 양의 한계효용과 엄격한 오목성 가정.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q011',
 'answer': 'O',
 'clean_prompt': '기존 위험자산 포트폴리오를 그대로 선택할 수도 있도록 무위험자산을 추가하면, 기존에 실현 가능했던 목표수익률의 최소분산은 증가하지 않고 더 낮아질 수 있다. '
                 'O/X?',
 'claim_ids': [],
 'review_note': '기존 선택집합이 새 집합의 부분집합이다. 같은 목적함수의 확대집합 최솟값은 원집합 최솟값보다 클 수 없다.',
 'source_finding': '무위험자산 추가가 모든 점의 위험을 반드시 엄격히 줄인다는 표현을 약한 개선으로 교정했다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '기존 선택집합이 새 집합의 부분집합이다. 같은 목적함수의 확대집합 최솟값은 원집합 최솟값보다 클 수 없다.',
                    'assumptions': 'NOTE85쪽. 기존 포트폴리오를 배제하는 새 제약은 없다.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q012',
 'answer': '0.8',
 'clean_prompt': 'E[RX]=8%, σX=5%, rf=4%다. X60%·무위험자산40% 포트폴리오의 샤프비율 (E[Rp]-rf)/σp는?',
 'claim_ids': [],
 'review_note': 'E[Rp]=.6×.08+.4×.04=.064, σp=.6×.05=.03. (.064-.04)/.03=.8이다.',
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': 'E[Rp]=.6×.08+.4×.04=.064, σp=.6×.05=.03. (.064-.04)/.03=.8이다.',
                    'assumptions': 'NOTE85쪽. 동일기간·비용 없음·무위험자산 분산0.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q013',
 'answer': '자본시장선(CML)',
 'clean_prompt': '표준 CAPM 균형의 평균-표준편차 공간에서 무위험자산과 접점 시장포트폴리오를 연결하는 효율적 자본배분선의 더 구체적인 명칭은? (자본배분선 / 자본시장선)',
 'claim_ids': ['L318'],
 'review_note': 'CAL 중 최대 샤프비율인 접점 시장포트폴리오의 선이 CML이다. CML도 CAL에 포함된다.',
 'source_finding': 'CAL과 CML을 서로 배타적인 개념으로 읽지 않도록 특별한 이름을 물었다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': 'CAL 중 최대 샤프비율인 접점 시장포트폴리오의 선이 CML이다. CML도 CAL에 포함된다.',
                    'assumptions': 'NOTE85쪽. 동질적 기대·동일 차입대출금리의 표준 CAPM.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q014',
 'answer': 'O',
 'clean_prompt': '표준 CAPM의 공통 투자기회·동질적 기대·동일 무위험 차입대출금리 조건에서, 투자자는 공통 접점 위험포트폴리오 M과 무위험자산의 비중을 위험회피도에 맞춰 '
                 '결정한다. O/X?',
 'claim_ids': ['L318'],
 'review_note': '위험자산 묶음의 최대 샤프비율 선택과 그 묶음에 대한 전체 투자비중 선택이 분리된다. 균형 접점이 M이다.',
 'source_finding': '모든 현실 투자자에게 조건 없이 적용하는 표현을 모형 전제로 한정했다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '위험자산 묶음의 최대 샤프비율 선택과 그 묶음에 대한 전체 투자비중 선택이 분리된다. 균형 접점이 M이다.',
                    'assumptions': 'NOTE85쪽. 표준 모형 안의 명제다.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q015',
 'answer': '대출, 차입',
 'clean_prompt': '평균-표준편차 도표의 CML에서 M왼쪽으로 시장포트폴리오 비중 y가 0<y<1인 구간과, M오른쪽으로 y>1인 구간의 명칭을 순서대로 쓰시오.',
 'claim_ids': [],
 'review_note': '무위험비중1-y가 양수이면 자금을 빌려주는 대출, 음수이면 무위험금리로 차입해 M을 추가매수한다.',
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': '무위험비중1-y가 양수이면 자금을 빌려주는 대출, 음수이면 무위험금리로 차입해 M을 추가매수한다.',
                    'assumptions': 'NOTE85쪽. 동일금리 차입대출과 양의 시장위험프리미엄.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q016',
 'answer': 'CAPM',
 'clean_prompt': '모든 투자자가 동일한 투자대상집합에 대해 동질적 기대를 갖고 공통 단일기간의 평균분산 선택을 하며, 완전자본시장과 동일 무위험차입대출 등 조건에서 시장균형의 자산 '
                 '적정가격·요구수익률을 시장베타와 시장위험프리미엄으로 설명하는 모형의 약칭은?',
 'claim_ids': ['L318'],
 'review_note': '시장베타의 균형 가격식 E[Ri]-rf=βi(E[Rm]-rf)은 자본자산가격결정모형 CAPM이다.',
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': '시장베타의 균형 가격식 E[Ri]-rf=βi(E[Rm]-rf)은 자본자산가격결정모형 CAPM이다.',
                    'assumptions': 'NOTE86쪽. 표준 모형 정의 확인.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q017',
 'answer': '평균, 분산',
 'clean_prompt': '표준 CAPM에서 투자자는 수익분포의 ( )과 ( )만으로 선택하며, 같은 분산이면 높은 평균을, 같은 평균이면 낮은 분산을 선호한다. 두 빈칸은?',
 'claim_ids': ['L318'],
 'review_note': '첫째 모멘트인 기대수익률과 둘째 중심모멘트인 분산을 사용한다. 평균을 선호하고 분산을 기피한다.',
 'source_finding': '원문두빈칸과평균분산선호를보존하고평균과분산이동시에높을때까지일률지배한다고오해하지않도록동일조건을명시.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '첫째 모멘트인 기대수익률과 둘째 중심모멘트인 분산을 사용한다. 평균을 선호하고 분산을 기피한다.',
                    'assumptions': 'NOTE86쪽. 이 모형의 가정이며 일반 분포의 모든 선호를 두 모멘트로 설명한다는 주장은 아니다.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q018',
 'answer': 'CML, SML',
 'clean_prompt': '표준 CAPM에서 무위험자산과 시장포트폴리오의 효율적 조합을 평균-표준편차로 나타내는 선, 개별증권과 포트폴리오의 균형 기대수익을 베타로 설명하는 선을 순서대로 '
                 '쓰시오.',
 'claim_ids': ['L318'],
 'review_note': '첫 선은 CML이고 둘째는 E[Ri]=rf+βi(E[Rm]-rf)인 SML이다. CML의 모든 점을 M 자체라고 부르지는 않는다.',
 'source_finding': 'CML에 M만 위치한다거나 개별증권은 특수한 경우에도 절대 위치할 수 없다는 원문 단정을 제거했다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '첫 선은 CML이고 둘째는 E[Ri]=rf+βi(E[Rm]-rf)인 SML이다. CML의 모든 점을 M 자체라고 부르지는 않는다.',
                    'assumptions': 'NOTE86쪽. 균형 모형·양의 시장위험프리미엄.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q019',
 'answer': '기대수익률과 표준편차, 기대수익률과 베타',
 'clean_prompt': 'CML과 SML의 두 축을 각각 쓰시오.',
 'claim_ids': ['L318'],
 'review_note': 'CML은 μ=rf+Sharpe(M)σ이므로 기대수익률·표준편차, SML은 μ=rf+β시장프리미엄이므로 기대수익률·베타다.',
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': 'CML은 μ=rf+Sharpe(M)σ이므로 기대수익률·표준편차, SML은 μ=rf+β시장프리미엄이므로 기대수익률·베타다.',
                    'assumptions': 'NOTE86쪽. 표준 CAPM 도표의 축.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q020',
 'answer': '자본시장선(CML), 증권시장선(SML)',
 'clean_prompt': '표준 CAPM에서 효율적 포트폴리오의 기대수익률-표준편차 관계, 개별증권도 포함하는 균형 기대수익률-베타 관계의 이름을 순서대로 쓰시오.',
 'claim_ids': ['L318'],
 'review_note': '총위험σ를 사용하는 효율적 조합은 CML, 시장베타를 사용하는 균형 가격관계는 SML이다.',
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': '총위험σ를 사용하는 효율적 조합은 CML, 시장베타를 사용하는 균형 가격관계는 SML이다.',
                    'assumptions': 'NOTE86쪽. 두 선의 위험지표를 명시.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q021',
 'answer': 'O',
 'clean_prompt': '시장분산이 양수일 때 βi=Cov(Ri,Rm)/Var(Rm)은 시장수익률에 대한 개별수익률의 선형회귀 기울기다. O/X?',
 'claim_ids': [],
 'review_note': '최소제곱 회귀 정상방정식에서 β Var(Rm)=Cov(Ri,Rm)이므로 식이 성립한다.',
 'source_finding': "OCR 수식을 복원하고 '기여분'이라는 모호한 표현을 회귀 기울기로 구체화했다.",
 'answer_kind': 'text',
 'concept_review': {'derivation': '최소제곱 회귀 정상방정식에서 β Var(Rm)=Cov(Ri,Rm)이므로 식이 성립한다.',
                    'assumptions': 'NOTE86쪽. 유한한 2차 모멘트·절편 포함 회귀.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q022',
 'answer': '1.2',
 'clean_prompt': 'CAPM 균형에서 rf=3%, E[RA]=8%, βA=.5, E[RB]=15%다. βB는?',
 'claim_ids': [],
 'review_note': '시장프리미엄=(.08-.03)/.5=.10이므로 βB=(.15-.03)/.10=1.2다.',
 'source_finding': '무차익만으로 개별증권 CAPM이 자동 성립하지 않으므로 균형모형 전제를 명시했다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '시장프리미엄=(.08-.03)/.5=.10이므로 βB=(.15-.03)/.10=1.2다.',
                    'assumptions': 'NOTE86쪽. 공통 CAPM 가격식.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q023',
 'answer': '과소평가',
 'clean_prompt': 'CAPM 요구수익률이10%인데 동일한 미래급부 예측과 현재가격에 따른 기대수익률이12%다. 해당 모형 기준 K증권은 과소평가인가 과대평가인가?',
 'claim_ids': [],
 'review_note': 'α=.12-.10=.02>0이다. 동일 미래급부의 더 낮은 현재가격은 더 높은 기대수익을 만들므로 모형상 과소평가다.',
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': 'α=.12-.10=.02>0이다. 동일 미래급부의 더 낮은 현재가격은 더 높은 기대수익을 만들므로 모형상 과소평가다.',
                    'assumptions': 'NOTE86쪽. 급부예측·요구수익 모형을 고정하며 확정수익을 의미하지 않는다.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q024',
 'answer': '샤프의 단일지표모형',
 'clean_prompt': '마코위츠 평균분산 분석에는 n개 기대수익률, n개 분산과 n(n-1)/2개 서로 다른 공분산의 추정이 필요하다. 이 부담을 줄이기 위해 Ri=αi+βiRm+εi로 '
                 '놓고 시장과 잔차 및 서로 다른 자산의 잔차가 무상관이라고 가정하여 Cov(Ri,Rj)=βiβjVar(Rm)으로 계산하는 모형은?',
 'claim_ids': [],
 'review_note': '공통 시장지표 하나로 공분산 구조를 제한하는 샤프의 단일지표모형이다. 식을 전개하면 시장항만 남는다.',
 'source_finding': '원문자료수와기술적추정부담이라는문제의도를복원했다. 자료가많으면정확추정이논리적으로불가능하다는절대단정은채택하지않으며단일지표모형의잔차무상관가정을명시.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '공통 시장지표 하나로 공분산 구조를 제한하는 샤프의 단일지표모형이다. 식을 전개하면 시장항만 남는다.',
                    'assumptions': 'NOTE87쪽. 잔차 무상관 가정은 실제 자료에서 별도 확인해야 한다.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q025',
 'answer': 'CAPM, APT',
 'clean_prompt': '시장포트폴리오 베타를 이용하는 평균분산 균형모형과, 수익률 요인구조·분산가능 잔차·무차익 조건에서 요인노출의 선형 가격관계를 도출하는 이론의 약칭을 순서대로 '
                 '쓰시오.',
 'claim_ids': ['L318', 'L319'],
 'review_note': '첫째는 CAPM, 둘째는 APT다. APT는 CAPM의 특정 시장포트폴리오나 투자자 효용 가정 없이 무차익 관계를 사용한다.',
 'source_finding': 'APT가 반드시 위험회피 효용을 전제로 하며 무조건 더 현실적이라는 원문 설명을 교정했다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '첫째는 CAPM, 둘째는 APT다. APT는 CAPM의 특정 시장포트폴리오나 투자자 효용 가정 없이 무차익 관계를 사용한다.',
                    'assumptions': 'NOTE87쪽. MIT 수리강의의 모형 전제 대조.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q026',
 'answer': '1.1',
 'clean_prompt': 'X의 베타1.4, Y의 베타0.8이다. X와 Y를 각각50% 보유한 포트폴리오의 베타는?',
 'claim_ids': [],
 'review_note': '공분산 선형성으로 βp=.5×1.4+.5×.8=1.1이다.',
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': '공분산 선형성으로 βp=.5×1.4+.5×.8=1.1이다.',
                    'assumptions': 'NOTE87쪽. 동일 시장 기준과 고정 투자비중.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q027',
 'answer': 'X',
 'clean_prompt': '소극적 투자전략은 주식시장지수를 추종하는 경우까지 포함하여 언제나 시장위험을 전혀 부담하지 않는 전략이다. O/X?',
 'claim_ids': [],
 'review_note': 'X. 주가지수 추종처럼 시장 노출을 유지하는 패시브 전략은 시장위험을 부담한다. 소극적이라는 운용방식만으로 시장위험0이 되지 않는다. 반대로 모든 패시브 운용의 '
                '위험이 항상 주식시장 평균과 같다는 원해설의 일반화도 성립하지 않는다.',
 'source_finding': '모든 패시브전략의 위험이 동일하다는 일반화 대신 지정된 시장지수 추종을 물었다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': 'X. 주가지수 추종처럼 시장 노출을 유지하는 패시브 전략은 시장위험을 부담한다. 소극적이라는 운용방식만으로 시장위험0이 되지 '
                                  '않는다. 반대로 모든 패시브 운용의 위험이 항상 주식시장 평균과 같다는 원해설의 일반화도 성립하지 않는다.',
                    'assumptions': 'NOTE87쪽. 헤지 없는 주식시장지수 추종.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q028',
 'answer': '시장투자적기포착전략',
 'clean_prompt': '사전에 고정한 기계적 비중조정 규칙이 아니라, 향후 시장방향의 예측을 바꿀 때마다 위험자산과 무위험자산 배분을 조정하는 전략은? (포뮬러 플랜 / '
                 '시장투자적기포착전략)',
 'claim_ids': [],
 'review_note': '시장방향 예측으로 위험노출 시점을 조절하므로 시장 타이밍 전략이다. 성과가 반드시 양수라는 뜻은 아니다.',
 'source_finding': 'CD가 항상 무위험이라는 설명과 채권/무위험자산 명칭만으로 전략을 나누는 설명을 사용하지 않았다.',
 'answer_kind': 'text',
 'concept_review': {'derivation': '시장방향 예측으로 위험노출 시점을 조절하므로 시장 타이밍 전략이다. 성과가 반드시 양수라는 뜻은 아니다.',
                    'assumptions': 'NOTE87쪽. 기계적 규칙과 예측에 따른 재량조절을 구분.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
REVIEWS.append({'id': 'NOTE-S3C9-Q031',
 'answer': '리밸런싱',
 'clean_prompt': '시장가격 변동으로 달라진 자산비중을 매매를 통해 기존 목표비중으로 되돌리는 행위는? (리밸런싱 / 업그레이딩)',
 'claim_ids': [],
 'review_note': '목표비중 자체의 변경이 아니라 실현비중을 목표로 복원하는 재조정이므로 리밸런싱이다.',
 'source_finding': '',
 'answer_kind': 'text',
 'concept_review': {'derivation': '목표비중 자체의 변경이 아니라 실현비중을 목표로 복원하는 재조정이므로 리밸런싱이다.',
                    'assumptions': 'NOTE87쪽. 기존 목표비중을 유지한다.',
                    'basis': 'explicit_conditions_and_independent_reasoning',
                    'current_law_claim': False}})
