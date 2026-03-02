# 법적 문서 호스팅 (Deploy Legal Pages)

Color Sort Master의 개인정보처리방침 및 이용약관을 웹에 호스팅합니다.

## 지시사항

### 1. 법적 문서 확인
- `docs/legal/privacy-policy.md` 읽기
- `docs/legal/terms-of-service.md` 읽기
- 내용이 최신인지, 연락처 정보가 정확한지 확인

### 2. HTML 페이지 생성/갱신
`website/public/` 디렉토리의 다음 파일들을 업데이트하세요:
- `privacy.html` — 개인정보처리방침
- `terms.html` — 이용약관
- `support.html` — 고객 지원 페이지

마크다운을 깔끔한 반응형 HTML로 변환하세요.
스타일: 깔끔하고 읽기 쉬운 디자인, 모바일 친화적.

### 3. 호스팅 옵션 안내
사용자에게 다음 호스팅 옵션을 안내하세요:

**A. GitHub Pages (무료, 추천)**
```bash
# gh-pages 브랜치에 website/public 배포
# 또는 별도 리포지토리로 분리
```

**B. Firebase Hosting**
```bash
npm install -g firebase-tools
firebase init hosting
firebase deploy
```

**C. Vercel / Netlify**
- website/public 디렉토리를 정적 사이트로 배포

### 4. app-ads.txt 확인
`website/public/app-ads.txt` 파일이 존재하고 AdMob Publisher ID가 설정되었는지 확인.

### 5. URL 접근성 테스트
호스팅 후 다음 URL이 접근 가능한지 확인 안내:
- `https://[도메인]/privacy`
- `https://[도메인]/terms`
- `https://[도메인]/support`
- `https://[도메인]/app-ads.txt`
