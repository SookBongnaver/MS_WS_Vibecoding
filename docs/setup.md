# 지정된 코딩 도구 설치·로그인

[워크숍으로 돌아가기](../README.md)

도구 비교·고객 환경 준비는 README에서 설명합니다. 여기서는 **강사가 지정한 경로 하나만** 진행합니다. 실제 참가자 계정의 사용 권한·조직 정책·잔여 사용량을 확인하세요.

## GitHub Copilot — VS Code

1. [VS Code](https://code.visualstudio.com/)를 설치합니다.
2. [공식 설정 안내](https://code.visualstudio.com/docs/copilot/setup)에 따라 Copilot을 설정하고 지정된 GitHub 계정으로 로그인합니다.
3. 새 작업 폴더를 **File → Open Folder**로 엽니다.
4. Chat에서 **Agent 모드**를 선택합니다. 모드가 보이지 않으면 버전·플랜·조직 정책을 확인합니다.
5. README의 첫 요청을 입력해 응답과 프로젝트 접근을 확인합니다.

## GitHub Copilot CLI

1. [공식 CLI 설치 안내](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli)에서 고객 PC에 맞는 설치 방법을 따릅니다.
2. 새 작업 폴더에서 터미널을 엽니다.
3. 아래 명령을 실행하고 로그인 안내를 따릅니다.

```powershell
copilot
```

4. 강사가 지정한 GitHub 계정을 사용하고 README의 첫 요청을 입력합니다.

CLI 설치만으로 Copilot 사용 권한이 생기지는 않습니다. [플랜과 제공 기능](https://docs.github.com/en/copilot/get-started/plans)을 확인합니다.

## Codex CLI

1. [공식 CLI 안내](https://developers.openai.com/codex/cli)와 [Windows 안내](https://developers.openai.com/codex/windows)를 확인합니다.
2. npm 설치 방식을 사용하는 경우 지원되는 Node.js를 먼저 준비하고 다음 명령을 실행합니다.

```powershell
npm.cmd install -g @openai/codex
```

3. 새 작업 폴더의 터미널에서 실행합니다.

```powershell
codex
```

4. 고객이 승인한 계정·인증 방식으로 로그인하고 README의 첫 요청을 입력합니다. API 인증을 사용하는 경우에도 키를 교재·대화·저장소에 넣지 않습니다.

## 공통 확인

- 내가 만든 새 폴더에서 작업하는지 확인합니다.
- 파일 변경·프로그램 설치·외부 서비스 호출은 내용을 확인하고 승인합니다.
- 설치가 차단되면 강사·관리자에게 문의합니다. 무제한 권한 모드나 정책 우회로 해결하지 않습니다.
- 실제 화면은 제품 버전에 따라 달라질 수 있습니다. 이 문서에는 아직 실제 실행 스크린샷이 포함돼 있지 않습니다.
