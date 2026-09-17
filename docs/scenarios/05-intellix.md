# 05. SK인텔릭스 해외 파트너 검토 에이전트

[시나리오 선택](../../README.md) · [공통 환경 준비](../01-environment.md) · [공통 실행 순서](../02-first-run.md)

나무엑스의 말레이시아 진출과 해외 사업 확장에서 착안했습니다. [공식 보도자료](https://www.sknetworks.co.kr/pr/news-room/Y6uVZuF7IEBsVm2D), 2026-09-15.

**만들 결과물:** 가상 유통·서비스 파트너의 근거를 비교하고 실사 질문을 만드는 에이전트. 실제 기업 신용평가·계약 추천 서비스가 아닙니다.

## Step 1. 시나리오 파일 확인

```powershell
$scenario = "intellix"
code .\data\intellix.json
code .\workshop\students\intellix.py
```

DB는 `workshop.Record`의 `scenario='intellix'`입니다.

| category | 내용 |
|---|---|
| `candidate` | 가상 후보·국가 |
| `criterion` | 평가 항목·가중치·필수 조건·최소 점수 |
| `evidence` | 후보별 근거·확인 여부·점수·갱신일 |

## Step 2. 코딩 도우미에 입력

```text
docs/02-first-run.md와 현재 시나리오 가이드를 읽어줘.
data/intellix.json, workshop/catalog.py의 CALC_ARGS와 EXAMPLES,
workshop/students/intellix.py를 확인해.
students/intellix.py의 calculate를 구현해줘.
records는 category별 record_id, category, payload 행 목록이야.
candidate_ids별 평가 근거를 확인하고 verified=true인 점수만 계산에 써.
평가 가중치 합은 1인지, 점수는 0~100인지 검증해.
없는 근거·미확인 근거·null 점수는 0점으로 채우지 말고 missing에 남겨.
미확인 항목이 있으면 weighted_score=null, 알려진 부분의 점수와 평가 범위를 별도로 보여줘.
필수 조건 충족·불충족·미확인을 구분하고 근거 ID와 갱신일을 포함해.
불완전한 점수로 확정 순위를 만들지 말고 ranking=null로 반환해.
결과에 assessments, synthetic=true를 포함해.
공통 연결과 안전 제한은 유지하고 해답을 import하지 마.
```

## Step 3. 계산 확인

```powershell
.\.venv\Scripts\python.exe -m workshop example --scenario intellix --mode starter
```

기본 입력은 `IX1, IX2`입니다. 데이터의 가중치와 확인된 점수를 직접 비교합니다.

**정답:** IX1은 **86점**, 평가 범위 100%입니다. IX2는 IC2가 미확인이므로 전체 점수는 **null**, 확인된 부분 점수 28점·평가 범위 40%입니다. `ranking=null`이며 28점을 86점과 동등한 총점처럼 비교하지 않습니다.

## Step 4. 에이전트 실행

```powershell
.\.venv\Scripts\python.exe -m workshop run --scenario intellix --mode starter
```

**`You>`에 입력**

```text
말레이시아의 가상 파트너 IX1과 IX2를 DB의 기준으로 비교해줘.
계산 도구를 사용하고, 확인된 근거와 미확인 정보를 구분해줘.
서비스 역량을 확인할 실사 질문도 정리해줘. 계약이나 연락은 하지 마.
```

**확인:** `compare_partners` 호출, 근거 ID, 불확실성, 추가 질문.

## Step 5. 저장·개선

`/save` → `intellix-01.txt` → `SAVE`.

코딩 도우미에게 `workshop/instructions/intellix.txt`를 수정해 “실사 질문을 근거 ID와 연결해 표로 작성”하게 요청합니다. 종료·재실행 후 “자료가 없는 후보가 더 나쁜 것 아니야?”라고 질문해 잘못된 단정을 피하는지 봅니다.

**선택 확장:** 새 가중치를 인자로 받도록 도구 스키마와 계산 함수를 함께 수정합니다. 읽기 전용 DB의 가중치를 직접 바꾸게 하지 않습니다.

**논의:** 어떤 근거는 재확인이 필요한가요? 필수 조건과 선호 조건은 누가 정해야 하나요?

[동료 피드백과 자유 개선](../03-improve-and-share.md)으로 이어갑니다. 실제 모델 실행 화면은 Azure 리허설 후 추가됩니다.
