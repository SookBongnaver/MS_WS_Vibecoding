# 04. 인크로스 캠페인 성과 분석·개선 제안 에이전트

[시나리오 선택](../../README.md) · [공통 환경 준비](../01-environment.md) · [공통 실행 순서](../02-first-run.md)

AI 기반 시장 분석·캠페인 운영·광고 최적화에서 착안했습니다. [공식 사업 페이지의 마케팅 트렌드 결산](https://www.sknetworks.co.kr/business/incross), 기사일 2026-07-03.

**기본 결과물:** 채널별 성과를 정확히 계산하고 후속 분석을 제안하는 에이전트. **예산 재배분은 선택 확장**이며 기본 계산 함수에는 없습니다. 실제 광고 집행은 하지 않습니다.

## Step 1. 시나리오 파일 확인

```powershell
$scenario = "incross"
code .\data\incross.json
code .\workshop\students\incross.py
```

DB는 `workshop.Record`의 `scenario='incross'`입니다.

| category | 내용 |
|---|---|
| `campaign` | 가상 캠페인 ID·목표 |
| `daily` | 날짜·채널·비용·노출·클릭·전환·귀속 매출 |

## Step 2. 코딩 도우미에 입력

```text
docs/02-first-run.md와 현재 시나리오 가이드를 읽어줘.
data/incross.json, workshop/catalog.py의 CALC_ARGS와 EXAMPLES,
workshop/students/incross.py를 확인해.
students/incross.py의 calculate를 구현해줘.
records는 category별 record_id, category, payload 행 목록이야.
campaign_id, start_date, end_date 인자를 유지해.
시작일 포함, 종료일 제외로 캠페인 성과를 필터링해.
캠페인·날짜·채널 중복 행은 합산하지 말고 오류로 알려줘.
채널별 합계와 전체 합계를 구한 뒤
CTR=클릭/노출, CPC=비용/클릭, CPA=비용/전환, ROAS=매출/비용으로 계산해.
일별 비율을 평균내지 마. CTR은 0.02 같은 비율로 반환해.
분모가 0이면 value=null과 reason을 반환해.
결과에 channels, totals, metrics, 근거 record_ids, synthetic=true를 포함해.
기본 과제에서는 예산 재배분을 구현하지 마.
공통 연결과 안전 제한은 유지하고 해답을 import하지 마.
```

## Step 3. 계산 확인

```powershell
.\.venv\Scripts\python.exe -m workshop example --scenario incross --mode starter
```

기본 입력: `DEMO-C01 / 2026-08-01 포함~2026-09-01 제외`.

| 지표 | search 채널 정답 |
|---|---|
| 비용 | 400,000원 |
| 노출·클릭·전환 | 40,000 / 500 / 25 |
| CTR | 0.0125 → 화면 표시 1.25% |
| CPC·CPA | 800원 / 16,000원 |
| ROAS | 2.25배 |

전체 비용은 **450,000원**입니다. 9월 1일 `ID5`는 제외합니다. `display`는 전환이 0이므로 CPA를 계산할 수 없습니다. `social`의 0 분모를 오류 없이 명시적으로 처리합니다.

## Step 4. 에이전트 실행

```powershell
.\.venv\Scripts\python.exe -m workshop run --scenario incross --mode starter
```

**`You>`에 입력**

```text
DEMO-C01의 2026-08-01부터 2026-09-01 전까지 성과를 조회해줘.
계산 도구로 채널별 CTR, CPC, CPA, ROAS를 구하고
데이터만으로 판단할 수 없는 점과 후속 분석 질문을 정리해줘.
```

**확인:** `calculate_media_metrics` 호출, 위 정답과 일치, 과거 효율이 미래 성과를 보장하지 않는다는 설명.

## Step 5. 저장·개선

`/save` → `incross-01.txt` → `SAVE`.

코딩 도우미에게 `workshop/instructions/incross.txt`를 수정해 “소액 표본과 전환 집계 지연에 대해 확인할 질문 제시”를 추가하게 합니다. 종료·재실행합니다.

**선택 확장:** 합성 예산 제약을 추가하고 총예산·채널별 최소·최대를 지키는 재배분 도구를 만듭니다. 기존 함수가 재배분을 지원한다고 가정하지 말고 도구 스키마·계산·검증을 함께 추가해야 합니다.

**논의:** 낮은 CPA만으로 좋은 채널인가요? 목표와 표본이 다르면 어떻게 비교해야 하나요?

[동료 피드백과 자유 개선](../03-improve-and-share.md)으로 이어갑니다. 실제 모델 실행 화면은 Azure 리허설 후 추가됩니다.
