# 대구 응급의료 모니터 — 설치 안내

비용 없이(구글 뉴스 RSS + GitHub 무료 기능만 사용) 매일 자동으로 응급의료 뉴스를 수집·게시하는 정적 웹사이트입니다.

## 1. GitHub 저장소(Repository) 만들기
1. github.com 로그인 → 우측 상단 `+` → `New repository`
2. Repository name 예: `daegu-emergency-news`
3. Public 으로 설정 (GitHub Pages 무료 사용을 위해 Public 권장)
4. `Create repository` 클릭

## 2. 파일 업로드
1. 방금 만든 저장소 페이지에서 `Add file` → `Upload files` 클릭
2. 이 폴더 안의 아래 파일/폴더를 그대로 드래그하여 업로드
   - `index.html`
   - `data.json`
   - `scripts/fetch_news.py`
   - `.github/workflows/update-news.yml`
   (폴더째로 끌어다 놓으면 하위 경로가 자동으로 유지됩니다)
3. 하단 `Commit changes` 클릭

## 3. GitHub Pages 활성화 (사이트 주소 만들기)
1. 저장소 상단 `Settings` 탭 클릭
2. 왼쪽 메뉴 `Pages` 클릭
3. `Branch` 를 `main` / `/(root)` 로 설정 후 `Save`
4. 잠시 후 상단에 `https://(계정명).github.io/daegu-emergency-news/` 형태의 주소가 생성됨
   → 이 주소가 팀원들과 공유할 사이트 링크입니다.

## 4. 자동 수집 첫 실행 (수동으로 1회 트리거)
1. 저장소 상단 `Actions` 탭 클릭
2. 처음엔 "Workflows aren't being run on this forked repository" 같은 안내가 뜰 수 있음 → `I understand my workflows, go ahead and enable them` 클릭
3. 왼쪽에서 `응급의료 뉴스 자동 수집` 클릭 → 우측 `Run workflow` 버튼 클릭 → 다시 `Run workflow` 클릭
4. 1분 정도 후 초록색 체크(✓)로 완료되면, 위 3번의 사이트 주소를 새로고침 → 뉴스가 표시됨

## 5. 이후는?
- 매일 한국시간 오전 7시에 GitHub Actions가 자동으로 실행되어 `data.json`을 갱신합니다.
- 아무도 접속하지 않아도, PC를 켜두지 않아도 자동으로 돌아갑니다. (GitHub 서버에서 실행됨)
- 급하게 지금 바로 갱신하고 싶으면 4번의 `Run workflow`를 다시 누르면 됩니다.
- 카테고리나 검색어를 바꾸고 싶으면 `scripts/fetch_news.py` 안의 `CATEGORIES` 목록을 수정 후 다시 업로드(Commit)하면 됩니다.

## 참고
- 이 사이트는 AI 요약 없이 **원문 제목·출처·링크**만 자동 수집합니다. (비용 발생 없음)
- 원문 확인 후 요약이나 보고서가 필요하면, 기존처럼 Claude 채팅에서 "이 뉴스 목록 요약해줘"라고 요청하시면 됩니다 (일반 구독 사용량 내에서 처리됨, 별도 과금 없음).
