# 02. 민팃 중고폰 판매 상담 에이전트

[시나리오 선택](../../README.md) · [공통 환경 준비](../01-environment.md) · [공통 실행 순서](../02-first-run.md)

민팃의 중고폰 매입·ATM·홈 회수·추가 보상 프로그램에서 착안했습니다. [공식 사업 소개](https://www.sknetworks.co.kr/business/mintit), 열람 2026-09-17.

**만들 결과물:** 기종·가정 등급·판매일별 예상 금액과 방법을 설명하는 상담 에이전트. 가격·정책은 모두 합성 데이터이며 실제 등급 판정이나 지급은 하지 않습니다.

## Step 1. 시나리오 파일 확인

```powershell
$scenario = "mintit"
code .\data\mintit.json
code .\workshop\students\mintit.py
```

DB는 `workshop.Record`의 `scenario='mintit'`입니다.

| category | 내용 | 샘플 ID |
|---|---|---|
| `quote` | 가상 기종·용량·등급별 가격 | MQ1~MQ3 |
| `promotion` | 대상·기간·보상·중복 가능 여부 | MP1~MP4 |
| `option` | 회수 방식·지역·비용 | MO1~MO2 |

기본 조회 도구는 제공됩니다. 참가자는 `calculate_estimate`가 호출할 업무 함수를 구현합니다.

## Step 2. 코딩 도우미에 입력

```text
docs/02-first-run.md와 현재 시나리오 가이드를 읽어줘.
data/mintit.json, workshop/catalog.py의 CALC_ARGS와 EXAMPLES,
workshop/students/mintit.py를 확인해.
students/mintit.py의 calculate를 구현해줘.
records는 category별 record_id, category, payload를 가진 행 목록이야.
quote_id, promotion_ids, option_id, date, region 인자는 유지해.
기준 가격+적용 보상 합계-회수 비용을 Python으로 계산해.
이벤트 시작·종료일은 둘 다 포함하고 기종·등급 조건을 검사해.
중복 불가 이벤트가 있으면 다른 이벤트와 더하지 말고 오류로 알려줘.
없는 ID·누락 가격·지원하지 않는 지역·중복 ID도 오류로 처리해.
결과에 base, bonus, fee, estimated_total, synthetic=true와 근거 ID를 넣어줘.
실제 등급 검사·접수·보상 지급은 구현하지 마.
해답을 import하거나 solution 모드로 바꾸지 말고 이 함수만 직접 구현해줘.
```

## Step 3. 계산 확인

```powershell
.\.venv\Scripts\python.exe -m workshop example --scenario mintit --mode starter
```

기본 입력: `MQ1 / MP1+MP2 / MO1 / 2026-09-26 / Seoul`.

**정답:** 180,000 + 20,000 + 10,000 − 5,000 = **205,000원**. 이는 실제 민팃 견적이 아닙니다.

## Step 4. 에이전트 실행

```powershell
.\.venv\Scripts\python.exe -m workshop run --scenario mintit --mode starter
```

**`You>`에 입력**

```text
가상 기종 M-128, 128GB, B등급을 가정하고 2026-09-26에 Seoul에서 홈 회수로 판매해.
MP1과 MP2의 적용 조건을 확인하고 계산 도구로 예상 순금액을 구해줘.
등급은 실제 검사 전 가정이라는 점도 안내해줘.
```

**확인:** 205,000원과 근거 ID. 다음에는 “MP3도 함께 적용해줘”를 요청합니다. 중복 불가 조건으로 금액을 합산하지 않아야 합니다.

## Step 5. 저장·개선

`/save` → `mintit-01.txt` → `SAVE`.

코딩 도우미에게 `workshop/instructions/mintit.txt`를 수정해 “사용자가 등급을 모르면 등급별 비교를 먼저 제안”하게 요청합니다. 종료·재실행 후 미등록 기종·이벤트 종료일 이후도 시험합니다.

**논의:** 예상 금액을 확정 금액으로 오해하지 않나요? 개인정보 없이 어떤 정보를 더 물어보면 좋을까요?

[동료 피드백과 자유 개선](../03-improve-and-share.md)으로 이어갑니다. 실제 모델 실행 화면은 Azure 리허설 후 추가됩니다.
