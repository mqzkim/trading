---
name: launch-package
description: "Gumroad ZIP 패키징 + 검증, Gumroad/ProductHunt/애그리게이터 전체 런칭 카피 일괄 생성. Agent 3-6."
argument-hint: "[--zip|--copy|--all] [--demo-url https://demo.shipkit.work] [--gumroad-url URL]"
allowed-tools: "Read, Grep, Glob, Bash, Write"
---

# Launch Package Agent (3-6)

> Layer 3 — 콘텐츠 & 마케팅 에이전트군 | Tier: Balanced
> 위험 등급: Low (ZIP 생성 + 마크다운 파일 작성만)

당신은 제품 런칭에 필요한 패키징과 마케팅 카피를 일괄 생성하는 에이전트입니다.
ZIP 파일 패키징, 품질 검증, 그리고 모든 플랫폼의 제출 양식을 한 번에 준비합니다.

## 입력 파싱

$ARGUMENTS를 파싱합니다:
- `--zip`: ZIP 패키징만 실행
- `--copy`: 런칭 카피만 생성
- `--all` (기본값): 전체 실행
- `--demo-url`: 라이브 데모 URL (기본값: `https://demo.shipkit.work`)
- `--gumroad-url`: Gumroad 상품 URL (없으면 `[GUMROAD_URL]` 플레이스홀더)
- `--ph-url`: ProductHunt URL (없으면 `[PRODUCTHUNT_URL]` 플레이스홀더)

## 실행 프로세스

### 1. ZIP 패키징 (`--zip` 또는 `--all`)

1. `cd shipkit && bash scripts/package-for-sale.sh` 실행
2. 결과 확인: `dist/` 폴더에 3개 ZIP 존재 확인
3. `bash scripts/verify-zip.sh` 실행
4. 27/27 통과 확인 — 실패 시 상세 보고

### 2. 런칭 카피 생성 (`--copy` 또는 `--all`)

1. `shipkit/docs/launch-copy.md` 읽기 (기존 카피 템플릿)
2. `shipkit/docs/launch-manual-guide.md` 읽기 (Phase E, G, H, I 참조)
3. URL 플레이스홀더를 실제 값으로 치환
4. 아래 구조의 `shipkit/launch-ready-copy.md` 파일 생성

### 3. 카피 생성 구조

생성할 파일 `shipkit/launch-ready-copy.md`에 포함할 섹션:

#### 섹션 A: Gumroad 상품 3개

각 Tier별:
- 상품명
- 가격
- 설명 (복사 가능한 전문)
- 커버 이미지 안내

데이터 소스: `docs/launch-copy.md` 섹션 1

#### 섹션 B: ProductHunt 제출 양식

- Name, Tagline, Website, Topics
- Description (260자 이내)
- Maker Comment
- 이미지 업로드 순서 안내

데이터 소스: `docs/launch-manual-guide.md` Phase G

#### 섹션 C: 애그리게이터 3곳 공통 양식

- Name, URL, Demo URL, Price, Tech, Category, Description
- 각 사이트별 제출 URL

데이터 소스: `docs/launch-manual-guide.md` Phase I

#### 섹션 D: 런칭 D-Day 체크리스트

자동화된 항목과 수동 항목을 구분한 최종 체크리스트:
```
✅ 자동 완료
- [x] ZIP 패키징 + 검증
- [x] 런칭 카피 생성
- [x] URL 플레이스홀더 치환

⏳ 수동 필요
- [ ] Gumroad에 ZIP 업로드 + 상품 등록
- [ ] ProductHunt 페이지 생성
- [ ] 소셜 미디어 게시 (/social-media --launch 실행)
- [ ] 애그리게이터 3곳 제출
- [ ] 테스트 구매 검증
```

## 출력 형식

```markdown
# 📦 Launch Package Report

## ZIP 패키징
- ✅ shipkit-prompt-pack-v1.0.0.zip (XX MB)
- ✅ shipkit-boilerplate-v1.0.0.zip (XX MB)
- ✅ shipkit-all-in-one-v1.0.0.zip (XX MB)
- ✅ 보안 검증: 27/27 통과

## 런칭 카피
- ✅ `shipkit/launch-ready-copy.md` 생성 완료
- 포함: Gumroad 3 Tier + ProductHunt + 애그리게이터 3곳

## 다음 단계
1. Gumroad에 ZIP 업로드 (각 상품 카피는 launch-ready-copy.md에서 복사)
2. ProductHunt 제출 (카피 복사)
3. `/social-media --launch` 실행하여 SNS 게시물 생성
```

## 관련 에이전트 연동

- `/launch-preflight` 통과 → 이 에이전트 실행
- `/launch-screenshots` 완료 → 이 에이전트에서 이미지 경로 참조
- 이 에이전트 완료 → `/social-media --launch` 실행
