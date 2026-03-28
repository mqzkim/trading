---
name: vercel-deploy
description: "Vercel 배포 설정, 트러블슈팅, cron 관리 스킬"
---

# Vercel Deploy

Vercel 배포 전문 스킬. ShipKit 프로젝트의 배포 설정, 트러블슈팅, cron 관리를 담당한다.

## 역할

Vercel Hobby 플랜 제약 조건을 숙지한 배포 전문가. 모든 Vercel 관련 작업(배포, cron, 환경변수, 트러블슈팅)에서 반드시 이 스킬을 참조한다.

## 프로젝트 구성

| 항목 | 값 |
|------|-----|
| Vercel 프로젝트명 | `claude-workspace` |
| Root Directory | `shipkit` |
| Framework | Next.js |
| Node.js Version | 24.x |
| 플랜 | **Hobby** (무료) |
| 도메인 | `shipkit.work` (Cloudflare) |
| GitHub 연동 | `mqzkim/claude-workspace` (자동 배포) |

## Hobby 플랜 제약 조건 (절대 규칙)

### Cron Jobs
- **하루 1회만 실행 가능** (`0 H * * *` 형식만 허용)
- `*/5 * * * *`, `0 */6 * * *` 등 하루 2회 이상은 **배포 자체가 실패**
- 타이밍 정밀도: +/- 59분 (정확한 시간 보장 안 됨)
- 최대 100개 cron/프로젝트

### Hobby 플랜 추가 제한
- **빌드**: 32회/시간, 100배포/일
- **함수**: 실행 시간 10초 (Serverless), Edge 30초
- **대역폭**: 100GB/월

### 실패 사례 기록
| 날짜 | 원인 | 결과 | 해결 |
|------|------|------|------|
| 2026-03-02 | `*/5 * * * *` cron (Sprint 11) | PR #21-26 체크 전부 실패 | `0 8 * * *`로 변경 |
| 2026-03-02 | Vercel 인프라 장애 (dxb1 리전) | 모든 배포 "internal error" 0ms | Vercel 복구 대기 (코드 정상) |

### 현재 Cron 설정 (`shipkit/vercel.json`)
```json
{
  "framework": "nextjs",
  "crons": [
    { "path": "/api/cron/cleanup", "schedule": "0 2 * * *" },
    { "path": "/api/cron/alerts", "schedule": "0 8 * * *" }
  ]
}
```

## 환경변수

### 필수 (Vercel 대시보드에서 설정)
| 변수 | 환경 | 용도 |
|------|------|------|
| `NEXT_PUBLIC_SUPABASE_URL` | all | Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | all | Supabase 익명 키 |
| `SUPABASE_SERVICE_ROLE_KEY` | all | Supabase 서비스 역할 키 |
| `STRIPE_SECRET_KEY` | all | Stripe 시크릿 |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | all | Stripe 퍼블릭 |
| `STRIPE_STARTER_PRICE_ID` | all | Stripe 가격 ID |
| `STRIPE_PRO_PRICE_ID` | all | Stripe 가격 ID |
| `STRIPE_WEBHOOK_SECRET` | all | Stripe 웹훅 시크릿 |
| `ANTHROPIC_API_KEY` | all | Claude API |
| `RESEND_API_KEY` | all | 이메일 |
| `RESEND_FROM_EMAIL` | production | 발신자 이메일 |
| `NEXT_PUBLIC_APP_URL` | per-env | 앱 URL |
| `DEMO_USER_EMAIL` | all | 데모 사용자 |
| `NEXT_PUBLIC_DEMO_MODE` | all | 데모 모드 |

### 누락된 환경변수 (추가 필요)
| 변수 | 환경 | 용도 |
|------|------|------|
| `CRON_SECRET` | all | Cron 엔드포인트 인증 |

## 배포 워크플로우

### GitHub Push → 자동 배포
1. `main` push → Vercel Production 배포
2. Feature branch push → Vercel Preview 배포
3. Preview 배포 성공 → Auto-merge 워크플로우 실행 (`.github/workflows/auto-merge-on-deploy.yml`)

### CLI 배포 (수동)
```bash
# 프로덕션 (root에서 실행)
cd /c/workspace/claude-workspace && npx vercel --prod --yes

# 프리뷰
cd /c/workspace/claude-workspace && npx vercel --yes
```

### 배포 전 체크리스트
1. `pnpm typecheck` 통과
2. `pnpm lint` 통과 (미사용 import/변수 = 빌드 실패)
3. `pnpm build` 성공
4. `vercel.json` cron이 **하루 1회 이하**인지 확인
5. 환경변수 누락 없는지 확인

## Cron 엔드포인트 보안 패턴

```typescript
// 모든 cron route에서 사용
const authHeader = request.headers.get("authorization");
if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
  return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
}
```

## 트러블슈팅

### "Deployment failed" + cron pricing 링크
- **원인**: `vercel.json` cron 스케줄이 Hobby 플랜 제한 초과
- **해결**: 모든 cron을 `0 H * * *` (하루 1회) 형식으로 변경

### "We encountered an internal error" + 0ms 빌드
- **원인 1**: Vercel 인프라 장애 (status.vercel.com 확인)
- **원인 2**: `vercel.json` 설정 오류 (cron 등)
- **진단 순서**:
  1. `vercel.json` cron 스케줄 검증 (Hobby = 하루 1회만)
  2. https://vercel-status.com/ 활성 인시던트 확인
  3. `curl -s -o /dev/null -w "%{http_code}" https://shipkit.work/` 로 기존 배포 확인
  4. 기존 배포 정상이면 인프라 문제 → 복구 대기
  5. Hobby 제한 (32빌드/시간) 초과 여부 확인 — CLI 반복 시도 시 소진 가능
- **대응**: 인프라 장애 시 CLI 반복 시도 금지 (빌드 쿼터 낭비). 30분 이상 간격으로 1회만 시도

### CLI 배포 vs GitHub 배포 차이
- CLI: `npx vercel` → 로컬 파일 업로드 (git 상태와 무관)
- GitHub: push → Vercel이 repo clone → Root Directory(`shipkit`) 기준 빌드
- PR 체크: Preview 배포 상태가 GitHub commit status로 반영

## 참고 문서
- [Vercel Cron Pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing)
- [Vercel Hobby Plan Limits](https://vercel.com/docs/limits)
- 기존 커맨드: `.claude/commands/vercel-deploy-optimize.md`, `vercel-env-sync.md`, `vercel-edge-function.md`

## 제약 조건
- Hobby 플랜 제한 절대 준수
- 환경변수는 Vercel 대시보드 또는 CLI로만 관리 (절대 코드에 하드코딩 금지)
- `--no-lint` 빌드 금지
- `vercel.json` 수정 시 반드시 cron 스케줄 검증
