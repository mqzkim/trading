---
name: notebooklm
description: "NotebookLM Enterprise API + Playwright 웹 UI — 노트북 CRUD, 소스 관리, 오디오/비디오/인포그래픽 생성"
argument-hint: "[create|list|get|source add|source list|audio|video|infographic|ask] [args]"
user-invocable: true
allowed-tools: "Read, Write, Bash, Grep, Agent, WebFetch"
---

# NotebookLM

NotebookLM Enterprise API(v1alpha) + Playwright 웹 UI 하이브리드 스킬.
API로 CRUD/소스/오디오, Playwright로 비디오/인포그래픽/Q&A.

## 환경 설정

```bash
# gcloud PATH (Git Bash)
export PATH="$PATH:/c/Users/USER/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin"

# 프로젝트 정보
PROJECT_NUMBER=947717596267
LOCATION=global
BASE_URL="https://global-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_NUMBER}/locations/${LOCATION}"
TOKEN=$(gcloud auth print-access-token)

# 기존 노트북 (웹 UI에서 생성)
NOTEBOOK_ID="9e1120a9-62d9-475e-ae3c-a84bbad6c2de"
```

## API 명령 (Enterprise API)

### 노트북 생성
```bash
curl -s -X POST "${BASE_URL}/notebooks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "노트북 제목"}'
```

### 노트북 조회
```bash
curl -s "${BASE_URL}/notebooks/${NOTEBOOK_ID}" \
  -H "Authorization: Bearer $TOKEN"
```

### 최근 조회 목록 (GET, 최대 500개)
```bash
curl -s -X GET "${BASE_URL}/notebooks:listRecentlyViewed" \
  -H "Authorization: Bearer $TOKEN"
```
> **주의**: GET 메서드 사용 (POST 아님). `notebooks` 전체 목록 API는 없음.

### 노트북 삭제
```bash
curl -s -X POST "${BASE_URL}/notebooks:batchDelete" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"names": ["projects/'"$PROJECT_NUMBER"'/locations/'"$LOCATION"'/notebooks/'"$NOTEBOOK_ID"'"]}'
```

### 소스 추가 — 인라인 텍스트
```bash
curl -s -X POST "${BASE_URL}/notebooks/${NOTEBOOK_ID}/sources:batchCreate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "userContents": [{
      "textContent": {
        "sourceName": "소스 이름",
        "content": "여기에 텍스트 내용"
      }
    }]
  }'
```

### 소스 추가 — 웹 URL
```bash
curl -s -X POST "${BASE_URL}/notebooks/${NOTEBOOK_ID}/sources:batchCreate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "userContents": [{
      "webContent": {
        "url": "https://example.com/article"
      }
    }]
  }'
```

### 소스 추가 — YouTube 비디오
```bash
curl -s -X POST "${BASE_URL}/notebooks/${NOTEBOOK_ID}/sources:batchCreate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "userContents": [{
      "youtubeContent": {
        "url": "https://www.youtube.com/watch?v=VIDEO_ID"
      }
    }]
  }'
```

### 소스 조회
```bash
curl -s "${BASE_URL}/notebooks/${NOTEBOOK_ID}/sources/${SOURCE_ID}" \
  -H "Authorization: Bearer $TOKEN"
```

### 소스 삭제
```bash
curl -s -X POST "${BASE_URL}/notebooks/${NOTEBOOK_ID}/sources:batchDelete" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"names": ["projects/'"$PROJECT_NUMBER"'/locations/'"$LOCATION"'/notebooks/'"$NOTEBOOK_ID"'/sources/'"$SOURCE_ID"'"]}'
```

### 오디오 오버뷰 생성
```bash
curl -s -X POST "${BASE_URL}/notebooks/${NOTEBOOK_ID}/audioOverviews" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sourceIds": [{"id": "SOURCE_ID"}],
    "episodeFocus": "핵심 포인트에 집중",
    "languageCode": "ko"
  }'
```
> 소스 미지정 시 전체 소스 사용. 생성에 수 분 소요.

### 오디오 오버뷰 삭제
```bash
curl -s -X DELETE "${BASE_URL}/notebooks/${NOTEBOOK_ID}/audioOverviews/default" \
  -H "Authorization: Bearer $TOKEN"
```

## Playwright 명령 (웹 UI — API 미지원 기능)

> 아래 기능은 Enterprise API에서 지원하지 않으므로 Playwright 웹 UI 자동화로 수행.

### 비디오 오버뷰 생성
1. `browser_navigate` → `https://notebooklm.google.com/notebook/NOTEBOOK_ID`
2. 스튜디오(Studio) 탭 클릭
3. "비디오 오버뷰 생성" 또는 "Generate video overview" 버튼 클릭
4. 생성 완료 대기 (수 분)
5. 다운로드 버튼 클릭

### 인포그래픽 생성
1. 스튜디오 탭 → "인포그래픽" 섹션
2. "생성" 버튼 클릭
3. 완료 후 다운로드

### AI 질문 (Q&A)
1. 노트북 페이지 열기
2. 채팅 입력란에 질문 입력
3. 응답 텍스트 추출

### 소스 추가 (복사된 텍스트 — 웹 UI)
1. "소스 추가" 버튼 클릭
2. "복사된 텍스트" 선택
3. 텍스트 붙여넣기 + 저장

## 제약 사항

- API v1alpha — 파괴적 변경 가능
- **API 미지원**: Q&A, 요약, 비디오, 인포그래픽
- 노트북당 오디오 오버뷰 **1개만** 동시 존재
- `notebooks` 전체 목록 API 없음 (`listRecentlyViewed`만 가능)
- Enterprise 전용 ($9/user/month, 14일 무료 체험)
- 소스 제한: 문서당 200MB 또는 500,000 단어

## 참고 문서

- [노트북 관리 API](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks)
- [소스 관리 API](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources)
- [오디오 오버뷰 API](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-audio-overview)
- [설정 가이드](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/set-up-notebooklm)
