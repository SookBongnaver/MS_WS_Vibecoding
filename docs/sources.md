# 공개 자료와 시나리오의 연결 근거

[처음으로](../README.md)

열람일: **2026-09-17**. 아래는 SK네트웍스 공식 사업 사이트 및 공식 보도자료입니다. 일반 언론 보도와 구분합니다. 사이트의 사업 페이지에는 최신 기사가 교체되어 표시될 수 있습니다.

| 시나리오 | 자료에서 확인한 사업 맥락 | Workshop에서 제안한 확장 |
|---|---|---|
| 워커힐 | 가을 축제의 식음·공연·고객 참여 프로그램, AI 와인 큐레이션 소개 | 여러 프로그램을 예산·시간 조건으로 조합하는 직원용 일정 제안 |
| 민팃 | 중고폰 매입, ATM·홈 방식, 추가 보상 프로그램 | 조건별 예상 금액·판매 방식 비교와 상담 안내문 |
| SK스피드메이트 | 엔카와 차량 진단·정비·보증 협력 및 플랫폼 추진 | 이력·보증·방문 시간 조회와 접수 메모 |
| 인크로스 | AI 기반 시장 분석·캠페인 운영·소재 최적화, 사내 AI 활용 | 합성 광고 성과 계산·후속 분석 제안, 선택 확장으로 예산 재배분 |
| SK인텔릭스 | 나무엑스의 말레이시아 진출과 해외 확장 | 가상 유통·서비스 파트너 비교와 실사 질문 |

## 사업 근거

1. [워커힐 가을 축제 보도자료](https://www.sknetworks.co.kr/pr/news-room/BrjdW3ZhfZf8VUGd) — 2026-09-14.
2. [민팃 사업 소개 및 관련 기사](https://www.sknetworks.co.kr/business/mintit).
3. [SK스피드메이트 사업 소개 및 엔카 협력 기사](https://www.sknetworks.co.kr/business/skspeedmate).
4. [인크로스 사업 소개 및 2026 상반기 마케팅 트렌드 결산](https://www.sknetworks.co.kr/business/incross) — 기사일 2026-07-03.
5. [나무엑스 말레이시아 진출 보도자료](https://www.sknetworks.co.kr/pr/news-room/Y6uVZuF7IEBsVm2D) — 2026-09-15.

기업이 이미 이 Workshop의 에이전트를 사용하고 있다는 의미가 아닙니다. 공개 사업 맥락과 교육용 제작 아이디어를 구분합니다. 기사 전문·사진·로고는 저장소에 복제하지 않고 링크와 요약만 제공합니다.

## 기술 참고

- [Foundry 리소스 생성과 모델 배포](https://learn.microsoft.com/en-us/azure/foundry/tutorials/quickstart-create-foundry-resources)
- [Azure OpenAI v1·Entra 인증·Chat Completions](https://learn.microsoft.com/en-us/azure/foundry-classic/openai/how-to/switching-endpoints)
- [VS Code](https://code.visualstudio.com/)
- [Codex CLI 공식 안내](https://developers.openai.com/codex/cli)
- [Azure SQL Database 문서](https://learn.microsoft.com/en-us/azure/azure-sql/database/)
- [App Service·Foundry 기반 기본 참조 아키텍처](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/basic-microsoft-foundry-chat) — 시나리오별 참조안은 공식 구현의 배포본이 아니라 실습 주제별 간소화 제안입니다.
- [Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-overview) · [Static Web Apps](https://learn.microsoft.com/en-us/azure/static-web-apps/overview) · [Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/overview)
- [Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/cosmos-db/introduction) · [Blob Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction) · [AI Search의 Blob 인덱서](https://learn.microsoft.com/en-us/azure/search/search-how-to-index-azure-blob-storage)
- [Azure Logic Apps](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-overview) · [App Service 인증](https://learn.microsoft.com/en-us/azure/app-service/overview-authentication-authorization) · [Managed Identity](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview)

추가 연결을 선택할 때 공식 문서에서 지원 모델·지역·인증·버전 조건을 확인합니다. 서비스 생성과 비용은 고객이 승인한 범위를 따릅니다.

## Workshop 운영 방식 참고

| 참고 자료 | 반영한 운영 원칙 | 적용 범위 |
|---|---|---|
| [Multi Harness 실습](https://github.com/HakjunMIN/multiharness-ghcp) | 환경 사전 점검·파일 기반 다음 단계 안내·재현 가능한 인계·독립 검토 | 기존 교재와 문서 양식에 경량 적용; 고정 기술 스택·외부 스킬·다중 하네스 전환은 필수화하지 않음 |
| [HIRA Billing Copilot](https://github.com/t-hajongkim/hira-billing-copilot) | 업무 요청·자동 처리·사람의 승인 구분, 입력·조작·기대 결과 중심 실습 | 주말 한 장 시연 안내에 적용; 의료 규정·판정 코드·데이터는 반입하지 않음 |

공개 자료의 운영 방식을 참고하여 교재를 작성했으며 해당 저장소의 코드·스킬을 복제하거나 실행하지 않습니다.

## 아키텍처 이미지·아이콘

각 시나리오 폴더와 `samples/weekend-card`의 `architecture.png`는 교재 표시용 이미지이며 `architecture.svg`는 편집·확대용 원본입니다. 이미지에 포함된 제품 아이콘은 [Microsoft Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/icons/)의 **Azure Public Service Icons V24**를 사용합니다.

공식 지침에 따라 제품명과 아이콘을 함께 표시하고 아이콘의 색상·형태·비율을 유지했습니다. Blob Storage에는 공식 Storage Accounts 아이콘, Azure AI Search에는 배포 팩의 Cognitive Search 아이콘, Container Apps에는 Worker Container App 아이콘, 모델 추론에는 Foundry Models 아이콘을 사용합니다.

Microsoft는 해당 아이콘의 아키텍처 다이어그램·교육 자료·문서 내 사용을 허용하며 그 외 권리를 보유합니다. 이 저장소의 아키텍처는 Microsoft 제품을 이용한 교육용 참조 설계이며 실제 배포·Microsoft의 별도 인증을 의미하지 않습니다.
