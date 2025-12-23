# 1. 제품 개요 (Product Overview)

## 1.1 프로젝트 명
**Project Sentinel (센티넬)**
*부제: 24/7 깨어있는 나만의 선물 트레이딩 요새*

## 1.2 배경 및 목적
코인 선물 시장은 높은 변동성을 가지며 24시간 운영됩니다. 전업 트레이더가 아닌 직장인이나 사업가는 차트를 계속 모니터링할 수 없기에, 매매 타이밍을 놓치거나 급락장에 대응하지 못해 큰 손실을 입는 경우가 많습니다.
본 프로젝트는 **"내가 자는 동안에도 내 자산을 지키고 불린다"**는 핵심 가치를 실현하기 위해, 검증된 Freqtrade 엔진 위에 안정성을 보강하고, 언제 어디서든 즉각적인 상황 파악 및 제어가 가능한 시스템을 구축하는 것을 목표로 합니다.

## 1.3 핵심 가치 (Core Values)
1.  **Extreme Stability (극강의 안정성):** 시스템 셧다운, API 오류, 청산 위험으로부터 자산을 보호하는 방어 기제 최우선.
2.  **User Freedom (사용자 해방):** 차트를 보지 않아도 믿고 맡길 수 있는 신뢰성.
3.  **Profitability (수익성):** 감정을 배제한 기계적 매매를 통한 꾸준한 우상향.

---

# 2. 시스템 아키텍처 (System Architecture)

전체 시스템은 3계층(3-Tier) 구조로 설계하여 안정성과 확장성을 확보합니다.

1.  **Core Layer (Trading Engine):**
    *   **Freqtrade (Docker):** 실제 매매 로직 수행, 거래소 통신, 백테스팅 담당.
    *   자체 REST API를 통해 상태 정보를 미들웨어로 송출.
2.  **Middleware Layer (BFF - Backend For Frontend):**
    *   **Python FastAPI:** Freqtrade API와 클라이언트 사이의 중계 서버.
    *   데이터 가공(Aggregation), 캐싱, 커스텀 인증, 알림 로직 강화.
    *   모바일/데스크탑에 최적화된 JSON 데이터 구조로 변환하여 전송.
3.  **Presentation Layer (Client UIs):**
    *   **Desktop UI (React/Next.js):** 분석 및 설정 중심의 전문가용 대시보드.
    *   **Mobile UI (React PWA or Native):** 모니터링 및 긴급 제어 중심의 심플 인터페이스.

---

# 3. 사용자 페르소나 및 스토리 (User Stories)

**타겟 유저:** 3040 전문직 종사자 (자금력은 있으나 시간이 부족함)

| ID | 사용자 스토리 (User Story) | 우선순위 |
| :--- | :--- | :--- |
| **US-01** | 사용자는 **출근 중 모바일**로 현재 수익률과 포지션 상태를 **3초 안에 확인**하고 싶다. | P0 (Critical) |
| **US-02** | 사용자는 **급락 알림**을 받았을 때, 모바일에서 **원터치로 모든 포지션을 종료(Panic Sell)**하고 봇을 정지하고 싶다. | P0 (Critical) |
| **US-03** | 사용자는 **퇴근 후 데스크탑**에서 오늘 봇이 매매한 내역과 로그를 상세히 분석하여 전략이 잘 도는지 확인하고 싶다. | P1 (High) |
| **US-04** | 사용자는 거래소 서버가 터지거나 봇이 멈췄을 때, **즉시 텔레그램/앱 푸시**로 알림을 받아야 한다. | P0 (Critical) |
| **US-05** | 사용자는 봇을 끄지 않고도 레버리지나 투입 금액 비중을 웹에서 수정하고 싶다. | P2 (Medium) |

---

# 4. 상세 기능 요구사항 (Functional Specs)

## 4.1 Middleware (FastAPI) 기능
*   **API Aggregation:** Freqtrade의 `/status`, `/profit`, `/balance` 엔드포인트를 호출하여 하나의 요약된 JSON으로 클라이언트에 전달 (네트워크 부하 감소).
*   **Health Check:** 주기적으로 Freqtrade 컨테이너가 살아있는지 핑(Ping)을 보내고, 응답이 없으면 관리자에게 비상 알림 발송.
*   **Auth Proxy:** Freqtrade의 기본 인증 외에 JWT 기반의 추가 보안 계층 적용.

## 4.2 Mobile UI (Monitoring & Emergency)
*   **컨셉:** "토스(Toss)" 또는 "로빈후드" 스타일의 직관적이고 큰 폰트 UI.
*   **메인 화면:**
    *   현재 총 자산 (테더/원화 환산).
    *   오늘의 실현 손익 (PnL) - 붉은색/푸른색으로 명확히 구분.
    *   현재 활성 포지션 카드 (코인 심볼, 진입가, 현재가, ROE %).
*   **긴급 제어 (Panic Mode):**
    *   화면 하단 고정 플로팅 버튼 **[긴급 정지]**.
    *   클릭 시: "현재 모든 포지션을 시장가로 종료하고 봇을 멈추시겠습니까?" 모달 팝업 -> 승인 시 Freqtrade `/stopbuy` 및 `/forceexit` 호출.

## 4.3 Desktop UI (Analytics & Management)
*   **컨셉:** "블룸버그 터미널" 스타일의 다크모드, 정보 밀도가 높은 대시보드.
*   **대시보드:**
    *   자산 변동 그래프 (Time Series).
    *   최근 트레이딩 로그 실시간 스트리밍 (WebSocket).
    *   승률, 손익비(Profit Factor), 최대 낙폭(MDD) 통계 카드.
*   **설정 관리 (Config Manager):**
    *   전략 파라미터(RSI 기준값, 손절 % 등)를 UI 폼(Form)으로 입력받아 FastAPI를 통해 Freqtrade 설정 업데이트.
    *   백테스팅 실행 요청 및 결과 리포트 시각화.

## 4.4 Trading Core (Freqtrade Customization)
*   **선물 전용 설정:**
    *   `trading_mode`: `futures`
    *   `margin_mode`: `isolated` (격리 마진 권장 - 자산 전체 청산 방지)
    *   `leverage`: 사용자 설정값 연동 (기본 3x).
*   **전략 로직:**
    *   안정성 위주: 추세 추종(Trend Following) + 변동성 돌파 전략 혼합.
    *   안전 장치: 비트코인(BTC) 급락 시 알트코인 매수 금지 로직 (BTC Correlation Filter) 탑재.

---

# 5. 기술 스택 (Tech Stack)

| 구분 | 기술 선정 | 선정 이유 |
| :--- | :--- | :--- |
| **Trading Engine** | **Freqtrade (Python)** | 검증된 오픈소스, 선물 거래 완벽 지원, 방대한 커뮤니티. |
| **Backend** | **FastAPI (Python)** | 비동기 처리로 고성능, Swagger 자동 문서화, Freqtrade와 같은 언어(Python)라 유지보수 용이. |
| **Desktop UI** | **React (Vite + Tailwind)** | 빠른 렌더링, 컴포넌트 재사용, 차트 라이브러리(Recharts) 활용 용이. |
| **Mobile UI** | **React (Responsive PWA)** | 별도 앱 개발 비용 절감. 모바일 브라우저에서 '홈 화면에 추가' 시 앱처럼 사용 가능. |
| **Database** | **SQLite** (Freqtrade 내장) | 단일 유저용으로 충분함. 필요 시 PostgreSQL로 마이그레이션. |
| **Infra** | **Docker Compose** | 엔진, 백엔드, 프론트엔드를 컨테이너 하나로 묶어 어디서든 즉시 배포 가능. |

---

# 6. 예외 케이스 및 리스크 관리 (Exception Handling)

## 6.1 거래소 API 장애 (Exchange Downtime)
*   **상황:** 바이낸스 점검 등으로 API 호출 실패 (5xx 에러).
*   **대응:**
    1.  Freqtrade 내부 재시도(Retry) 로직 최적화 (Exponential Backoff).
    2.  3회 이상 실패 시 텔레그램으로 "거래소 연결 불안정, 봇 대기 모드 전환" 알림 발송.
    3.  대기 모드에서는 신규 진입 금지.

## 6.2 데이터 지연 및 멈춤 (Stale Data)
*   **상황:** 봇 프로세스는 살아있으나 데이터 수신이 멈춰 잘못된 판단을 하는 경우.
*   **대응:** FastAPI에서 '마지막 데이터 수신 시간(Last Candle Time)'을 체크. 5분 이상 갱신 없으면 'Heartbeat Lost' 경고 발송 및 봇 재시작(Docker Restart) 명령 수행.

## 6.3 청산 방어 (Liquidation Protection)
*   **상황:** 반대 방향으로 급격한 빔이 나와 청산가에 근접.
*   **대응:**
    1.  전략 코드 내 `stoploss`는 거래소 주문부(Orderbook)에 실제로 걸어두는 방식(`stoploss_on_exchange: true`) 사용. 인터넷이 끊겨도 거래소에서 손절이 나가도록 함.
    2.  자산의 50% 이상을 포지션에 투입하지 않도록 `max_open_trades` 제한.

---

# 7. 프로젝트 로드맵 (Roadmap)

## Phase 1: 코어 구축 (Week 1-2)
*   Docker Compose로 Freqtrade + FastAPI 컨테이너 환경 구성.
*   FastAPI에서 Freqtrade API와 통신하여 기본 데이터(잔고, 상태) 가져오는 로직 구현.
*   기본 선물 전략(Basic Strategy) 백테스팅 및 선정.

## Phase 2: UI 개발 (Week 3-4)
*   **Desktop:** React 프로젝트 세팅, 대시보드 레이아웃, 트레이딩뷰 차트 연동.
*   **Mobile:** 모바일 전용 뷰(View) 개발, 긴급 정지 버튼 및 PnL 요약 카드 구현.
*   FastAPI와 프론트엔드 연동.

## Phase 3: 통합 테스트 및 모의 투자 (Week 5)
*   바이낸스 퓨처스 Testnet 연동.
*   UI에서 버튼 클릭 시 실제 봇이 반응하는지 지연 시간(Latency) 테스트.
*   강제 연결 해제 시나리오 테스트.

## Phase 4: 실전 배포 (Week 6)
*   AWS 프리티어 또는 Vultr 저가형 VPS(월 $5 수준)에 배포.
*   소액($100)으로 실전 가동 시작.