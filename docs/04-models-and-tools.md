# 코딩 도구와 실행 모델 선택

[처음으로](../README.md)

## 두 가지를 구분하세요

| 선택 | 역할 | 기본 경로 |
|---|---|---|
| 코딩 도우미 | 에이전트의 Python 코드 작성·수정 | Codex CLI, GitHub Copilot, Claude Code 중 하나 |
| 실행 모델 | 만들어진 에이전트가 판단·도구 선택·응답 생성 | Foundry에서 배포한 함수 호출 지원 모델 하나 |

Foundry가 여러 모델을 제공한다고 해서 코딩 도우미의 라이선스·인증까지 제공되는 것은 아닙니다. 코딩 도구를 Azure 모델로 연결하는 기능도 도구별 지원 여부를 별도로 확인해야 합니다.

## 코딩 도구는 하나만 준비

- **Codex CLI:** [공식 설치 안내](https://developers.openai.com/codex/cli)와 [Windows 안내](https://developers.openai.com/codex/windows)를 따릅니다. Node.js 설치 후 PowerShell에서 `npm.cmd install -g @openai/codex`를 실행하고, 실습 폴더에서 `codex`를 실행합니다. 조직에서 승인한 계정으로 로그인합니다.
- **GitHub Copilot:** [VS Code 공식 안내](https://code.visualstudio.com/docs/copilot/setup)에 따라 계정과 사용 권한을 준비합니다. 실습 폴더를 연 후 Chat에서 파일 변경이 가능한 Agent 모드를 선택합니다.
- **Claude Code:** [공식 설치 안내](https://code.claude.com/docs/en/setup)에 따라 설치하고 사용 권한을 준비합니다. 실습 폴더에서 `claude`를 실행합니다.

가이드의 **“코딩 도우미에 입력”** 블록은 선택한 도구의 대화창에 붙여넣습니다. 도구가 제안한 파일 변경·실행 명령은 확인 후 승인합니다. 무제한 권한 모드로 바꾸거나 조직 보안 정책을 우회하지 않습니다.

## 모델 교체는 선택 실습

먼저 기본 모델 하나로 끝까지 완료하세요. 현재 코드는 **Azure OpenAI v1 Chat Completions + 함수 호출 + Entra 인증**을 사용합니다. Foundry 카탈로그의 모든 모델이 이 코드를 그대로 지원하는 것은 아닙니다.

1. 기본 실행 결과와 도구 호출을 기록합니다.
2. 관리자가 승인한 동일 API·함수 호출 지원 모델을 추가 배포합니다.
3. `config.local.json`의 `deployment`를 새 **배포 이름**으로 바꿉니다.
4. 다른 리소스에 배포했다면 `endpoint`도 실제 OpenAI v1 URL로 바꿉니다.
5. 아래 명령으로 연결을 확인합니다.

```powershell
.\.venv\Scripts\python.exe -m workshop check --model
```

6. 동일한 질문으로 에이전트를 실행해 근거·도구 선택·응답 시간을 비교합니다.
7. 오류가 나면 원래 설정으로 복구합니다. API 차이는 배포 이름만 바꿔 해결되지 않습니다.

실습에서 여러 모델을 동시에 호출하거나 멀티 에이전트를 구성할 필요는 없습니다. 이 과정의 목적은 **코딩 도구와 실행 모델이 독립적인 선택이라는 점**을 이해하는 것입니다.
