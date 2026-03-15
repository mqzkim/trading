---
name: resend-domain
description: "Playwright로 Resend 대시보드에서 도메인 인증을 자동 수행. DNS 레코드 확인 후 Cloudflare에 자동 추가. Agent 4-10."
argument-hint: "[도메인명] [--registrar cloudflare]"
allowed-tools: "Read, Bash, Glob, Grep, Write, Edit, WebFetch"
---

# Resend Domain Agent (4-10)

> Layer 4 — 운영 에이전트군 | Tier: Balanced
> 위험 등급: Medium (DNS 레코드 추가 포함)

당신은 Playwright MCP를 사용하여 Resend 대시보드에서 도메인 인증을 자동 수행하고,
필요한 DNS 레코드를 Cloudflare에 자동 추가하는 에이전트입니다.

## 입력 파싱

$ARGUMENTS를 파싱합니다:

| 파라미터 | 설명 | 예시 |
|----------|------|------|
| `[도메인]` | 인증할 도메인 | `shipkit.work` |
| `--registrar` | DNS 관리 업체 (기본값: cloudflare) | `cloudflare` |
| `--from-email` | 발신 이메일 (기본값: `noreply@[도메인]`) | `noreply@shipkit.work` |

## 사전 조건

- Playwright MCP 서버가 실행 중이어야 합니다
- Resend 계정이 있어야 합니다
- DNS 관리를 위한 Cloudflare 계정 접근 가능

## 실행 프로세스

### Step 1: Resend 대시보드 접속
1. `browser_navigate` → `https://resend.com/domains`
2. `browser_snapshot` → 로그인 상태 확인
3. 로그인 필요 시:
   - 사용자에게 이메일/비밀번호 질문 (AskUserQuestion)
   - GitHub/Google OAuth 로그인 가능
   - `browser_fill_form` → 자격증명 입력

### Step 2: 도메인 추가
1. **Add Domain** 버튼 클릭
2. 도메인명 입력: `[도메인]`
3. Region 선택 (기본: US East)
4. **Add** 클릭
5. `browser_snapshot` → DNS 레코드 목록 확인

### Step 3: DNS 레코드 추출
Resend가 표시하는 DNS 레코드를 캡처합니다. 일반적으로:

1. **SPF** (TXT 레코드):
   - Type: TXT
   - Name: @ 또는 도메인
   - Value: `v=spf1 include:amazonses.com ~all` (또는 유사)

2. **DKIM** (CNAME 레코드 × 3):
   - Type: CNAME
   - Name: `resend._domainkey.[도메인]` 등
   - Value: Resend 제공 값

3. **DMARC** (TXT 레코드, 선택):
   - Type: TXT
   - Name: `_dmarc`
   - Value: `v=DMARC1; p=none;`

4. `browser_take_screenshot` → DNS 레코드 화면 캡처

### Step 4: Cloudflare에 DNS 레코드 추가
1. `browser_navigate` → Cloudflare DNS 레코드 페이지
   - `https://dash.cloudflare.com/[ACCOUNT_ID]/[도메인]/dns/records`
2. 각 DNS 레코드에 대해:
   - **Add Record** 클릭
   - Type, Name, Value 입력
   - **Proxy status**: DNS Only (회색 구름)
   - **Save** 클릭
3. 모든 레코드 추가 완료 확인

### Step 5: Resend에서 도메인 검증
1. Resend 도메인 페이지로 돌아가기
2. **Verify DNS** 또는 **Check DNS** 버튼 클릭
3. 검증 결과 확인:
   - 모든 레코드 ✅ → 인증 완료
   - 일부 ❌ → DNS 전파 대기 (1~5분 후 재시도)
4. `browser_take_screenshot` → 검증 결과 캡처

### Step 6: 환경변수 업데이트
인증 완료 후:
```bash
vercel env rm RESEND_FROM_EMAIL production --yes
echo "noreply@[도메인]" | vercel env add RESEND_FROM_EMAIL production
```

### Step 7: 결과 보고

## 출력 형식

```markdown
# Resend Domain Report

## 작업: 도메인 인증 — [도메인]

### DNS 레코드
- ✅ SPF (TXT): v=spf1 include:amazonses.com ~all
- ✅ DKIM (CNAME): resend._domainkey → [값]
- ✅ DKIM (CNAME): resend2._domainkey → [값]
- ✅ DKIM (CNAME): resend3._domainkey → [값]
- ✅ DMARC (TXT): v=DMARC1; p=none;

### 검증
- ✅ Resend 도메인 인증 완료
- ✅ RESEND_FROM_EMAIL=noreply@[도메인]

### 다음 단계
→ 이메일 발송 테스트
→ 재배포: `vercel --prod`
```

## Cloudflare 계정 정보

- Account ID: `6f6dbde827cfd51b1480ce7234811294`
- DNS 관리 URL: `https://dash.cloudflare.com/6f6dbde827cfd51b1480ce7234811294/shipkit.work/dns/records`

## 주의사항

- **DNS 전파**: 레코드 추가 후 검증까지 최대 48시간 소요 가능 (보통 1~5분)
- **SPF 충돌**: 기존 SPF 레코드가 있으면 병합 필요 (TXT 레코드는 도메인당 1개만)
- **DMARC**: 선택사항이지만 이메일 전달률 향상에 권장
- **Proxy OFF**: 모든 이메일 관련 DNS 레코드는 반드시 DNS Only (Proxy 끔)
