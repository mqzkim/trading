# DDD Architecture Rules (MANDATORY)

> **이 파일은 모든 AI 에이전트와 개발자가 코드 작성 전 반드시 참조해야 하는 절대 기준이다.**
> **예외 없음. 위반 시 PR 거부.**

## 핵심 원칙 (변경 불가)

1. **레이어 의존성 단방향**: `presentation → application → domain` (역방향 절대 금지)
2. **도메인은 순수**: `domain/` 레이어는 프레임워크, DB, 외부 API에 의존하지 않는다
3. **인터페이스는 도메인에**: Repository·Port 인터페이스는 `domain/`에 정의, 구현은 `infrastructure/`
4. **공개 API는 index만**: 레이어 간 cross-import는 `index.ts` (또는 `__init__.py`)를 통해서만
5. **도메인 이벤트로 통신**: 바운디드 컨텍스트 간 직접 의존 금지, 이벤트로만 통신

## 표준 폴더 구조

### TypeScript / Next.js 프로젝트
```
src/
  domains/
    {domain-name}/          # 바운디드 컨텍스트 단위 (예: auth, billing, user)
      domain/               # 순수 비즈니스 로직 (외부 의존 0)
        entities/           # 식별자를 가진 핵심 객체
        value-objects/      # 불변 값 객체
        aggregates/         # 일관성 경계 (트랜잭션 단위)
        events/             # 도메인 이벤트
        services/           # 도메인 서비스 (여러 엔티티 관여)
        repositories/       # 인터페이스 정의만 (구현은 infrastructure/)
        index.ts            # ★ 유일한 공개 API
      application/          # 유스케이스 조율
        commands/           # 상태 변경 명령
        queries/            # 조회 요청
        handlers/           # 명령/쿼리 핸들러
        dtos/               # 입출력 데이터 구조
        index.ts
      infrastructure/       # 외부 시스템 구현체
        persistence/        # DB 구현 (Prisma, Supabase)
        external/           # 외부 API 클라이언트
        messaging/          # 이벤트 발행/구독
        index.ts
      presentation/         # 인터페이스 어댑터
        api/                # REST / tRPC 라우터
        ui/                 # React 컴포넌트 (도메인 의존)
        index.ts
      DOMAIN.md             # ★ 도메인 설명 (AI 필독)
  shared/                   # Shared Kernel (최소화)
    domain/                 # 공유 도메인 객체
    utils/                  # 순수 유틸
    types/                  # 공유 타입
```

### Python 프로젝트 (trading)
```
src/
  {domain}/               # 바운디드 컨텍스트 (예: regime, scoring, signals, portfolio)
    domain/
      entities.py         # 도메인 엔티티
      value_objects.py    # 값 객체
      events.py           # 도메인 이벤트
      services.py         # 도메인 서비스
      repositories.py     # 인터페이스 (ABC)
      __init__.py         # ★ 공개 API
    application/
      commands.py
      queries.py
      handlers.py
      __init__.py
    infrastructure/
      persistence.py
      external.py
      __init__.py
    DOMAIN.md             # ★ 도메인 설명 (AI 필독)
  shared/
    domain/
    utils/
```

## 네이밍 규칙 (필수 준수)

| 레이어 | 접미사 | 예시 |
|--------|--------|------|
| Entity | `Entity` | `UserEntity`, `OrderEntity` |
| Value Object | `VO` 또는 `Value` | `EmailVO`, `MoneyValue` |
| Aggregate | `Aggregate` | `OrderAggregate` |
| Domain Event | `Event` | `OrderPlacedEvent` |
| Domain Service | `DomainService` | `PricingDomainService` |
| Repository Interface | `Repository` | `IOrderRepository` |
| Repository Impl | `Repository` + 기술명 | `PrismaOrderRepository` |
| Application Handler | `Handler` | `PlaceOrderHandler` |
| Command | `Command` | `PlaceOrderCommand` |
| Query | `Query` | `GetOrderQuery` |
| DTO | `Dto` | `OrderResponseDto` |

## AI 에이전트 필수 체크리스트

코드 수정 전 반드시 확인:

- [ ] 수정하려는 파일이 어느 레이어인가? (`domain/` / `application/` / `infrastructure/` / `presentation/`)
- [ ] 해당 레이어의 `DOMAIN.md`를 읽었는가?
- [ ] 새 의존성이 레이어 규칙을 위반하지 않는가?
- [ ] `domain/` 레이어에 프레임워크/라이브러리 import가 없는가?
- [ ] `index.ts` (또는 `__init__.py`)를 통해 공개 API를 노출하는가?
- [ ] 바운디드 컨텍스트 간 직접 import 대신 이벤트를 사용하는가?

## 금지 사항

```
# ❌ 절대 금지
from infrastructure.persistence import UserRepository  # domain에서 infrastructure import
import prisma from '@prisma/client'                    # domain 레이어에서 DB 직접 사용
from domains.billing import BillingService             # 컨텍스트 간 직접 import
```

```
# ✅ 올바른 방법
from domain.repositories import IUserRepository        # domain에서 인터페이스 사용
from domains.billing.index import BillingEvent         # index를 통한 공개 API 접근
```

## DOMAIN.md 필수 항목

각 도메인 폴더에 반드시 포함:
```markdown
# {Domain Name}

## 책임
이 바운디드 컨텍스트가 담당하는 비즈니스 영역

## 핵심 엔티티
- Entity1: 설명
- Entity2: 설명

## 외부 의존성
- 의존하는 다른 컨텍스트 (이벤트로만 통신)

## 주요 유스케이스
1. 유스케이스 설명

## 변경 불가 규칙
- 이 도메인에서 절대 변경하면 안 되는 비즈니스 규칙
```

## 상세 가이드

전체 DDD 가이드: `docs/DDD_GUIDE.md`
