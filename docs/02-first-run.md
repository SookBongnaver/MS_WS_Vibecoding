# 선택 예제: Python 에이전트 연결·제작·실행

> 이 장은 제공된 Azure 모델·SQL 기반 예제 코드를 사용하는 경로입니다. 모든 참가자의 필수 따라하기가 아닙니다. 자유 제작은 [시작 가이드](00-workshop.md)를 따릅니다.

[이전: 환경 준비](01-environment.md) · [시나리오 선택](../README.md#어떤-에이전트를-만들까요)

## Step 1. 제작할 시나리오 선택

VS Code 터미널에서 아래 중 **하나**를 실행합니다. 이 변수는 현재 PowerShell 창에서만 유지됩니다. 새 창을 열면 다시 지정합니다.

```powershell
$scenario = "walkerhill"
```

선택 가능: `walkerhill`, `mintit`, `speedmate`, `incross`, `intellix`.

다른 시나리오를 골랐다면 `config.local.json`의 `scenario`도 같은 값으로 바꾸고 해당 데이터를 관리자에게 적재받습니다.

## Step 2. 환경 연결 확인

```powershell
.\.venv\Scripts\python.exe -m workshop check --local
.\.venv\Scripts\python.exe -m workshop check --model
.\.venv\Scripts\python.exe -m workshop check --db
```

`--local`은 로컬 자료만, `--model`은 실제 Azure 모델만, `--db`는 실제 SQL과 조회 권한을 확인합니다. 어느 단계가 실패했는지 구분합니다.

## Step 3. 미완성 부분 확인

```powershell
code ".\workshop\students\$scenario.py"
.\.venv\Scripts\python.exe -m workshop example --scenario $scenario --mode starter
```

**처음 정상 상태:** `NotImplementedError: Implement calculate ...`가 나옵니다. 설치 오류가 아니라 **참가자가 자연어로 만들어야 하는 업무 계산 도구가 아직 비어 있다는 표시**입니다.

제공하는 것: 모델 연결, DB 조회, 도구 선택·실행 반복 구조, 저장·권한 제한.

참가자가 만드는 것: 선택 시나리오의 `calculate` 업무 함수, 업무 지침 개선, 추가 기능.

전체 프로젝트를 빈 화면에서 만드는 것이 아니라 기본 골격에서 시작합니다. 완성된 제품에 질문만 입력하는 것도 아닙니다.

## Step 4. 선택한 코딩 도우미에 제작 요청

Codex CLI는 저장소 루트에서 `codex`, GitHub Copilot CLI는 터미널에서, GitHub Copilot은 VS Code의 Agent 대화창을 엽니다.

아래의 `walkerhill`을 본인 시나리오 이름으로 바꿔 붙여넣습니다.

```text
이 저장소의 README와 docs/02-first-run.md를 먼저 읽어줘.
나는 walkerhill 시나리오의 업무 에이전트를 만들고 있어.

1. data/walkerhill.json의 합성 데이터 구조를 읽어줘.
2. workshop/catalog.py에서 이 시나리오의 CALC_ARGS와 EXAMPLES를 확인해줘.
3. workshop/students/walkerhill.py의 calculate 함수를 구현해줘.
   함수 인자 이름과 records 입력 구조는 바꾸지 마.
4. docs/scenarios/01-walkerhill.md의 업무 규칙과 확인값을 따라줘.
5. 실제 계산은 Python에서 수행하고 근거 record_id를 결과에 포함해줘.
6. 모르는 값, 존재하지 않는 ID, 조건 위반을 성공으로 처리하지 마.
7. 구현을 시작하기 전에 변경할 파일과 처리 순서를 설명해줘.
8. 다른 시나리오, 인증, DB 연결, runtime의 안전 제한은 수정하지 마.
9. 해답을 import하거나 --mode solution으로 몰래 바꾸지 마.

새 패키지 설치, 클라우드 리소스 생성, 삭제 작업은 하지 마.
확인이 필요하면 질문해줘. 코드 작성 후 실행할 명령을 알려줘.
```

다른 시나리오는 데이터·학생 파일·문서 경로를 함께 바꿉니다. 정확한 제작 프롬프트는 각 시나리오 문서에 있습니다.

## Step 5. 클라우드 없이 계산부터 확인

코딩 도우미의 변경을 확인한 후 **실행용 PowerShell**에서 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m workshop example --scenario $scenario --mode starter
```

**정상:** `OFFLINE CALCULATION ONLY`와 JSON 결과가 표시됩니다. 각 시나리오의 확인값과 비교합니다. 이 명령은 로컬 합성 데이터로 계산만 하므로 모델 사용료가 없고, Azure SQL 연결 확인을 대신하지 않습니다.

막혔을 때만 강사 참고 결과를 비교할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -m workshop example --scenario $scenario --mode solution
```

`solution`은 **강사 완성 구현을 사용한 것**이며 본인 제작 완료가 아닙니다. 결과 모양이 조금 달라도 업무 계산·근거·예외 처리 기준이 같아야 합니다.

## Step 6. 실제 에이전트 실행

```powershell
.\.venv\Scripts\python.exe -m workshop run --scenario $scenario --mode starter
```

`You>`가 나오면 선택 시나리오 문서의 **실행 질문**을 입력합니다. 이 단계는 실제 Foundry 모델과 실제 Azure SQL을 사용하고 비용이 발생할 수 있습니다.

**정상 흐름 예시 — 실제 캡처가 아닌 설명**

```text
You> [시나리오의 업무 질문]
[tool] list_records
[tool] calculate_itinerary_cost
Agent> [도구 결과를 근거로 작성한 답변]
```

모델에 따라 도구 호출 순서·횟수·문장은 달라질 수 있습니다. 숫자는 코드 계산과 같아야 합니다. 계산 도구를 사용하지 않았다면 “암산하지 말고 계산 도구로 확인해줘”라고 요청하고, 업무 지침도 개선합니다.

## Step 7. 결과 파일 저장

완료된 답변 뒤 `You>`에 아래를 입력합니다.

```text
/save
```

파일명 질문에 `briefing-01.txt`, 확인 질문에 `SAVE`를 입력합니다. `outputs` 폴더에서 결과를 엽니다. 같은 파일명은 덮어쓰지 않으므로 다음에는 `briefing-02.txt`를 사용합니다.

파일 저장은 모델에 임의 쓰기 도구를 주지 않고 **사용자 명령과 확인으로 실행**하도록 기본 구현했습니다.

종료하려면:

```text
exit
```

## Step 8. 지침 수정과 재실행

```powershell
code ".\workshop\instructions\$scenario.txt"
```

코딩 도우미에 추가할 업무 기준을 설명하고 이 파일을 수정하게 합니다. 변경 후 에이전트를 종료·재실행해야 새 지침을 읽습니다.

마지막으로 [동료와 논의하고 개선하기](03-improve-and-share.md)를 진행합니다.
