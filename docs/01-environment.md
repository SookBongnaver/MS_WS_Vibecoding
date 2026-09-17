# 선택 예제: Foundry·Azure SQL 구성

> **공통 사전 준비가 아닙니다.** 자유 제작 중 Azure 모델과 SQL이 필요하다고 결정했거나, 저장소의 Python 에이전트 예제를 실행하려는 경우에만 사용합니다. 처음 참가했다면 [바이브코딩 시작 가이드](00-workshop.md)부터 진행하세요.

[이전](00-workshop.md) · [다음: 첫 실행](02-first-run.md)

> Windows PowerShell 기준입니다. 이 저장소의 로컬 코드·합성 데이터는 제공되지만, 고객 구독에서의 Azure 생성·모델·DB 통합 실행과 실제 화면 캡처는 아직 진행 전입니다. 포털 UI는 계정·지역·버전에 따라 달라질 수 있습니다. 생성에는 비용이 발생할 수 있으며 구독 관리자의 승인을 먼저 받습니다.

## 먼저 역할을 나누세요

**관리자:** Azure 리소스 생성, 모델 배포, DB 데이터 적재, 참가자 조회 권한 부여.

**참가자:** 코딩 도구 로그인, 저장소 열기, 연결 확인, 에이전트 제작·실행.

한 사람이 환경 구성까지 따라 할 수 있지만, **실행 단계에는 관리자 아닌 조회 전용 계정이 필요**합니다. 프로그램은 쓰기 가능한 DB 계정을 거부합니다. 사내 행사에서는 관리자가 사전에 환경을 만들고 참가자는 지정된 값을 전달받아 시작할 수도 있습니다.

## Step 1. PC에 도구 설치

1. [Git for Windows](https://git-scm.com/downloads/win), [Python 3.13](https://www.python.org/downloads/), [VS Code](https://code.visualstudio.com/)를 설치합니다. Python 설치 시 PATH 추가를 선택합니다.
2. [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows)를 설치합니다.
3. [Microsoft ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)를 설치합니다. 64비트 Python에는 64비트 드라이버를 사용합니다.
4. [도구 비교 자료](tools-comparison.md)에 따라 강사가 지정한 코딩 도구를 준비합니다.
5. 설치 후 VS Code와 터미널을 다시 엽니다.

**PowerShell에 입력**

```powershell
git --version
py -3.13 --version
az version
Get-OdbcDriver -Name '*ODBC Driver 18 for SQL Server*'
```

**정상:** 각 도구 버전과 ODBC 드라이버가 출력됩니다. 회사 PC에서 설치가 막히면 IT 관리자에게 문의합니다. 정책이나 실행 제한을 임의로 해제하지 않습니다.

## Step 2. 저장소 열고 Python 준비

아래 명령은 아직 저장소를 내려받지 않았을 때 한 번 실행합니다.

```powershell
Set-Location $HOME
git clone https://github.com/SookBongnaver/MS_WS_Vibecoding.git
Set-Location .\MS_WS_Vibecoding
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
code .
```

VS Code에서 **Terminal → New Terminal**을 열고 현재 위치가 저장소 루트인지 확인합니다.

```powershell
Get-Location
.\.venv\Scripts\python.exe -m workshop check --local
```

**정상 출력**

```text
OK walkerhill: 8 synthetic records
OK mintit: 9 synthetic records
OK speedmate: 9 synthetic records
OK incross: 7 synthetic records
OK intellix: 8 synthetic records
LOCAL ONLY: no Azure, DB or model connection was tested.
```

여기까지는 Azure가 없어도 됩니다. 이 결과는 모델·DB 접속 성공을 의미하지 않습니다. 가상 환경 활성화 스크립트 대신 Python의 전체 상대 경로를 사용하므로 PowerShell 실행 정책을 바꿀 필요가 없습니다.

## Step 3. Foundry 프로젝트 만들기 — 관리자

1. [Microsoft Foundry](https://ai.azure.com/)에 로그인합니다.
2. 프로젝트 선택 메뉴에서 **Create new project / 새 프로젝트**를 선택합니다.
3. 예시 프로젝트 이름 `proj-vibecoding`을 입력합니다.
4. **Advanced options / 고급 설정**에서 사용할 구독과 실습 전용 리소스 그룹을 선택합니다. 예시 그룹 이름은 `rg-vibecoding-workshop`입니다.
5. 모델과 배포 유형이 지원되는 지역을 선택합니다. 지역은 고객 정책·모델 지원·할당량에 따라 관리자와 확정합니다.
6. 기존 업무용 리소스를 잘못 선택하지 않았는지 확인하고 **Create**를 누릅니다.
7. 생성 완료 후 프로젝트 개요를 확인합니다.

**정상:** 프로젝트 이름과 연결 정보가 보입니다. 이 실습은 **모델 API를 직접 호출**하므로 Agent Service에 별도 에이전트를 등록하지 않습니다.

## Step 4. 실행 모델 배포 — 관리자

1. 모델 카탈로그에서 함수 호출과 Chat Completions를 지원하는 Azure OpenAI 모델을 선택합니다. 예: `gpt-4.1-mini`가 해당 지역·구독에 제공되는 경우 사용합니다.
2. **Deploy / 배포**에서 예시 배포 이름 `workshop-chat`을 지정합니다.
3. 승인된 종량제 배포 유형·소규모 용량을 선택하고 생성합니다. 대규모 예약 용량은 만들지 않습니다.
4. 배포된 모델의 테스트 화면에서 “연결 확인이라고 답해줘”를 입력합니다.
5. 모델의 **코드 보기 / 사용 방법**에서 OpenAI v1 API 주소를 확인합니다.

코드에 넣을 주소 형태:

```text
https://YOUR-RESOURCE.openai.azure.com/openai/v1/
```

또는 해당 리소스가 제공하는:

```text
https://YOUR-RESOURCE.services.ai.azure.com/openai/v1/
```

**중요:** `.../api/projects/...` 형태의 프로젝트 엔드포인트는 이 코드에 넣지 않습니다. 실제 모델 코드 예제의 v1 주소를 사용합니다. 리소스 이름만 추측해서 주소를 만들지 않습니다.

6. 관리자는 참가자에게 해당 Azure OpenAI 리소스의 추론 권한(예: **Cognitive Services OpenAI User**)을 최소 범위로 부여합니다. 역할 적용에 시간이 걸릴 수 있습니다.

## Step 5. Azure SQL 만들기 — 관리자

1. [Azure 포털](https://portal.azure.com/)에서 **SQL databases → Create**를 선택합니다.
2. 실습 구독·리소스 그룹, 예시 DB 이름 `sqldb-vibecoding`을 입력합니다.
3. **Server → Create new**에서 전역 고유 서버 이름을 지정합니다.
4. 승인된 지역과 요금제를 선택합니다. 실습 인원에 맞는 소규모 구성을 쓰고 예상 요금을 확인합니다.
5. SQL 서버의 **Microsoft Entra 관리자**를 지정합니다.
6. **Networking**에서 실습 PC의 승인된 IP 또는 조직의 사설 접속 경로만 허용합니다. “모든 IP 허용”이나 방화벽 해제를 하지 않습니다.
7. **Review + create → Create** 후 생성 완료를 확인합니다.

**기록:** 서버 주소 `실제서버.database.windows.net`, DB 이름. SQL 비밀번호를 공유하지 않습니다.

## Step 6. 로컬 설정 입력

저장소 루트의 PowerShell에서 아래 명령을 **처음 한 번만** 실행합니다. 기존 설정 파일이 있으면 복사하지 않습니다.

```powershell
if (-not (Test-Path .\config.local.json)) {
    Copy-Item .\config.example.json .\config.local.json
}
code .\config.local.json
```

다음 필드를 실제 값으로 바꾸고 저장합니다.

```json
{
  "scenario": "walkerhill",
  "endpoint": "https://YOUR-RESOURCE.openai.azure.com/openai/v1/",
  "deployment": "workshop-chat",
  "sql_server": "YOUR-SERVER.database.windows.net",
  "sql_database": "sqldb-vibecoding",
  "tenant_id": ""
}
```

`tenant_id`는 조직에서 지정한 테넌트 GUID를 입력합니다. 기본 테넌트 하나만 사용하면 빈 문자열도 가능합니다. `scenario`에는 선택한 `walkerhill`, `mintit`, `speedmate`, `incross`, `intellix` 중 하나를 입력합니다. 키나 비밀번호 필드는 없습니다.

`config.local.json`은 `.gitignore`에 포함돼 있습니다. Git에 강제로 추가하지 마세요.

## Step 7. 합성 데이터 적재 — DB 관리자

1. VS Code 터미널에서 SQL Entra 관리자 계정으로 로그인합니다. `YOUR-...`는 실제 값을 치환합니다.

```powershell
az login --tenant YOUR-TENANT-ID
az account set --subscription YOUR-SUBSCRIPTION-ID
```

2. 선택 시나리오 하나를 적재합니다. 모든 실습이 필요하면 시나리오 이름을 바꿔 반복합니다.

```powershell
.\.venv\Scripts\python.exe -m workshop seed --scenario walkerhill
```

3. 대상 설정을 확인한 뒤 요청에 `SEED`를 입력합니다.

**정상:** 최초 실행 시 `Inserted: 8 (existing rows unchanged)`가 표시됩니다. 같은 데이터로 재실행하면 기존 행을 덮어쓰지 않고 삽입 수가 0입니다.

실제 테이블은 **`workshop.Record` 하나**입니다. `scenario`, `record_id`, `category`, `payload` 열에 시나리오별 합성 데이터를 저장합니다. SQL의 JSON 열을 이용해 초보자 실습의 스키마 구성 부담을 줄였습니다. 로컬 JSON은 적재 원본이며, `run` 명령은 이 파일 대신 **실제 Azure SQL**을 읽습니다.

## Step 8. 조회 전용 사용자 만들기 — DB 관리자

1. Azure SQL Database의 **Query editor / 쿼리 편집기**에 Microsoft Entra 관리자로 로그인합니다. 포털에서 지원되지 않는 구성은 승인된 SQL 클라이언트를 사용합니다.
2. Entra에 존재하는 참가자 계정 또는 그룹을 확인하고, 아래의 예시 이름을 실제 이름으로 바꿉니다.
3. 정확한 대상 DB에서 실행합니다. 같은 사용자가 이미 있으면 CREATE USER는 다시 실행하지 않습니다.

```sql
CREATE USER [participant@YOUR-DOMAIN] FROM EXTERNAL PROVIDER;
GRANT SELECT ON OBJECT::workshop.Record TO [participant@YOUR-DOMAIN];
DENY INSERT, UPDATE, DELETE, ALTER, CONTROL
    ON OBJECT::workshop.Record TO [participant@YOUR-DOMAIN];
```

이름 중복·디렉터리 조회 권한 오류는 관리자가 해결합니다. 임의 SQL 로그인 비밀번호 공유로 우회하지 않습니다. 자세한 검토용 템플릿은 [sql/permissions.sql](../sql/permissions.sql)을 참고합니다.

**주의:** 모든 시나리오를 한 DB에 적재하면 이 권한은 전체 합성 테이블 조회를 허용합니다. 참가자 간 엄격한 격리가 필요하면 DB를 분리합니다. 시나리오 필터는 보안 경계가 아닙니다.

## Step 9. 참가자 계정으로 전환

관리자 로그인으로 적재했다면 런타임 실행 전에 **조회 전용 참가자 계정으로 `az login`을 다시 실행**합니다.

```powershell
az login --tenant YOUR-TENANT-ID
az account set --subscription YOUR-SUBSCRIPTION-ID
.\.venv\Scripts\python.exe -m workshop check --model
.\.venv\Scripts\python.exe -m workshop check --db
```

**정상:** 모델 응답과 `DB_OK` 범주별 건수가 보입니다. 쓰기 권한이 있으면 `Runtime requires SELECT-only access` 오류로 중단됩니다. 권한 검사를 끄지 말고 계정을 바꾸거나 관리자에게 권한을 조정받습니다.

완료했다면 [첫 실행과 에이전트 제작](02-first-run.md)으로 이동합니다.
