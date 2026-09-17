# 03. SK스피드메이트 차량 관리 접수 준비 에이전트

[시나리오 선택](../../README.md) · [공통 환경 준비](../01-environment.md) · [공통 실행 순서](../02-first-run.md)

차량 진단·정비·보증 협력과 차량 관리 플랫폼 추진에서 착안했습니다. [공식 사업 소개 및 엔카 협력 기사](https://www.sknetworks.co.kr/business/skspeedmate), 열람 2026-09-17.

**만들 결과물:** 정비 이력·보증 확인 항목·방문 후보를 정리하는 접수 준비 에이전트. 진단·주행 안전 판단·실제 예약은 하지 않습니다.

## Step 1. 시나리오 파일 확인

```powershell
$scenario = "speedmate"
code .\data\speedmate.json
code .\workshop\students\speedmate.py
```

실제 차량번호 대신 가상 차량 ID를 사용합니다. DB는 `workshop.Record`의 `scenario='speedmate'`입니다.

| category | 내용 |
|---|---|
| `vehicle` | 차량·주행거리·가상 정비 이력 |
| `service` | 차종별 서비스·소요 시간 |
| `warranty` | 가상 보증 기간·거리·추가 조건 |
| `slot` | 서비스별 가용 날짜·시간·수량 |

## Step 2. 코딩 도우미에 입력

```text
docs/02-first-run.md와 현재 시나리오 가이드를 읽어줘.
data/speedmate.json, workshop/catalog.py의 CALC_ARGS와 EXAMPLES,
workshop/students/speedmate.py를 확인해.
students/speedmate.py의 calculate를 구현해줘.
records는 category별 record_id, category, payload 행 목록이야.
차량 ID와 서비스 ID를 확인하고 호환되지 않는 차종은 오류로 처리해.
start_date 포함, end_date 제외 범위에서 해당 서비스의 가용 슬롯을 찾아줘.
슬롯 길이가 소요 시간 이상이고 capacity>=1인 것만 날짜순 최대 3개 반환해.
각 후보 날짜와 차량 주행거리를 보증 조건과 비교하되 최종 보증은 담당자 확인이야.
이력이 없으면 없음으로 표시하고 실제 수리 내역을 만들지 마.
결과에 candidates, history, warranty_checks, synthetic=true와 근거 ID를 포함해.
공통 연결과 안전 제한은 유지하고 해답을 import하지 마.
```

## Step 3. 계산 확인

```powershell
.\.venv\Scripts\python.exe -m workshop example --scenario speedmate --mode starter
```

기본 입력: `DEMO-003 / SS1 / 2026-09-21 포함~2026-09-28 제외`.

**정답:** 후보는 **ST1 / 2026-09-26 / 10:00 / 60분** 한 개입니다. 보증 SW1의 날짜·주행거리 조건은 만족하더라도 최종 적용은 담당자 확인입니다. `2027-01-01~2027-01-02`처럼 데이터가 없는 기간에는 빈 후보 목록을 반환해야 합니다. 강사 참고 결과는 `--mode solution`으로 비교할 수 있습니다.

## Step 4. 에이전트 실행

```powershell
.\.venv\Scripts\python.exe -m workshop run --scenario speedmate --mode starter
```

**`You>`에 입력**

```text
DEMO-003 차량의 최근 이력과 보증 확인 항목을 알려줘.
SS1 서비스를 2026-09-21부터 2026-09-28 전까지 받을 후보 시간을
DB에서 찾아 도구로 검증해줘. 예약은 하지 마.
```

**확인:** `match_available_slots` 호출, 실제 슬롯 ID, 최종 보증은 담당자 확인이라는 표시.

## Step 5. 저장·개선

`/save` → `speedmate-01.txt` → `SAVE`.

코딩 도우미에게 `workshop/instructions/speedmate.txt`에 “접수 담당자가 물어볼 질문을 마지막에 정리”를 추가하게 합니다. 종료·재실행 후 없는 차량과 빈 정비 이력도 시험합니다.

**논의:** 상담 준비에 충분한가요? 어떤 내용은 반드시 정비 전문가가 판단해야 하나요?

[동료 피드백과 자유 개선](../03-improve-and-share.md)으로 이어갑니다. 실제 모델 실행 화면은 Azure 리허설 후 추가됩니다.
