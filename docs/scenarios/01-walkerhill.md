# 01. 워커힐 고객 일정 제안 에이전트

[시나리오 선택](../../README.md) · [공통 환경 준비](../01-environment.md) · [공통 실행 순서](../02-first-run.md)

워커힐의 식음·공연·고객 참여 프로그램과 AI 큐레이션 소개에서 착안했습니다. [공식 가을 축제 기사](https://www.sknetworks.co.kr/pr/news-room/BrjdW3ZhfZf8VUGd), 2026-09-14.

**만들 결과물:** 고객 조건에 맞는 일정과 비용을 확인하는 직원용 에이전트. 가격·일정은 실제 상품이 아닌 교육용 합성 데이터입니다. 실제 예약은 하지 않습니다.

## Step 1. 시나리오 파일 확인

공통 환경 준비를 먼저 완료합니다. 터미널에서:

```powershell
$scenario = "walkerhill"
code .\data\walkerhill.json
code .\workshop\students\walkerhill.py
```

DB는 `workshop.Record`에 `scenario='walkerhill'`로 저장됩니다.

| category | 내용 | 샘플 ID |
|---|---|---|
| `program` | 가격·소요 시간·실내외 | WP1~WP4 |
| `slot` | 날짜·시간·잔여 수량·이동 여유 | WS1~WS4 |

`list_records`와 `get_record` SQL 조회 도구는 이미 제공됩니다. 참가자는 `calculate_itinerary_cost`가 호출할 `calculate` 함수를 구현합니다.

## Step 2. 코딩 도우미에 입력

```text
공통 가이드 docs/02-first-run.md와 현재 시나리오 가이드를 읽어줘.
data/walkerhill.json, workshop/catalog.py의 CALC_ARGS와 EXAMPLES,
workshop/students/walkerhill.py를 확인해.

students/walkerhill.py의 calculate 함수를 구현해줘.
records는 category별 record_id, category, payload를 가진 행 목록이야.
인자 이름과 공통 런타임·DB 연결·다른 시나리오는 바꾸지 마.
선택 slot_ids로 프로그램 가격을 조회해 people을 곱하고 합산해.
date, 방문 start/end, 각 프로그램 duration, capacity를 검사해.
다음 슬롯의 transfer_minutes는 이전 일정 종료 후 필요한 이동 시간이야.
시간 겹침·이동 시간 부족·수량 부족·예산 초과이면 feasible=false와 이유를 반환해.
가격·이동 시간 누락, 없는 ID, 중복 ID, 잘못된 인자는 명시적 오류로 처리해.
결과에는 synthetic=true, total, feasible, issues와 근거 ID를 포함해.
해답을 import하거나 solution 모드로 변경하지 말고 직접 구현해줘.
먼저 수정 계획을 설명하고, 코드 작성 뒤 오프라인 예제를 실행해줘.
```

## Step 3. 계산 확인

```powershell
.\.venv\Scripts\python.exe -m workshop example --scenario walkerhill --mode starter
```

기본 입력은 `WS1, WS2 / 2026-09-26 / 2명 / 200,000원 / 14:00~18:00`입니다.

**정답:** WP1 45,000원 × 2 + WP2 35,000원 × 2 = **160,000원**, 시간·이동·수량 조건을 만족하므로 `feasible=true`.

실패하면 오류를 코딩 도우미에게 전달해 수정합니다. 강사 참고 결과는 `--mode solution`으로 볼 수 있지만 자신의 제작 결과와 구분하세요.

## Step 4. 에이전트 실행

```powershell
.\.venv\Scripts\python.exe -m workshop run --scenario walkerhill --mode starter
```

**`You>`에 입력**

```text
2026-09-26에 성인 2명이 14:00~18:00 동안 방문해.
예산은 20만 원이고 실내 식사와 공연을 원해.
DB에서 후보를 찾아 계산 도구로 일정과 총액을 검증해줘.
```

**확인:** 실제 조회와 `calculate_itinerary_cost` 호출 후 160,000원과 근거 ID가 제시됩니다. 다음에는 예산을 12만 원으로 바꾸고 불가능한 조합을 그대로 추천하지 않는지 봅니다.

## Step 5. 저장·개선

`/save` → `walkerhill-01.txt` → `SAVE`를 입력해 결과를 저장합니다.

`workshop/instructions/walkerhill.txt`에 “조건에 맞는 안이 없으면 바꿀 조건을 먼저 물어보기”를 추가하도록 코딩 도우미에게 요청한 뒤 종료·재실행합니다.

**논의:** 이동 시간이 충분한가요? 고객에게 더 물어볼 조건은 무엇인가요? 실제 예약 전에 직원이 확인할 항목은 무엇인가요?

[동료 피드백과 자유 개선](../03-improve-and-share.md)으로 이어갑니다. 실제 모델 실행 화면은 Azure 리허설 후 추가됩니다.
