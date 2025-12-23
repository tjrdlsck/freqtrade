# Project Sentinel: Web UI Expansion Plan (Backtesting & Optimization)

## 1. 개요 (Overview)
본 문서는 기존 'Project Sentinel'의 모니터링 중심 기능을 확장하여, 웹 브라우저 상에서 **백테스팅(Backtesting)**과 **전략 최적화(Hyperopt)**를 수행할 수 있는 "Strategy Lab" 기능을 구축하기 위한 상세 구현 계획입니다.

**목표:** CLI에 의존하지 않고, 직관적인 GUI를 통해 전략을 검증하고 파라미터를 최적화하여 수익성을 극대화한다.

---

## 2. 아키텍처 확장 (Architecture Extension)

### 2.1 Backend (FastAPI)
기존 `main.py`에 다음 기능을 추가합니다.

*   **Job Management:** 백테스팅과 Hyperopt는 장시간 실행되는 프로세스이므로, 비동기 작업 관리자(`BacktestManager`, `HyperoptManager`)를 강화하여 프로세스 상태(실행 중, 완료, 에러)를 추적합니다.
*   **Command Execution:** `docker exec` 명령어를 통해 Core 컨테이너 내부의 `freqtrade` 명령어를 실행합니다.
*   **Result Parsing:** Freqtrade가 생성하는 JSON 결과 파일(`backtest-result-*.json`, `hyperopt_results.pickle` 등)을 읽어 프론트엔드에 적합한 포맷으로 변환합니다.

### 2.2 Frontend (Desktop UI)
`Desktop.js` 내의 `Backtest` 탭을 **"Strategy Lab"**으로 확장하고 두 개의 하위 탭을 구성합니다.

1.  **Backtest Simulator:**
    *   **Config Form:** 전략 선택, 기간 설정, 캔들(Timeframe) 설정, 시드 머니 설정.
    *   **Execution:** 실행 버튼 및 실시간 로그/진행 상태 표시.
    *   **Report:** 누적 수익 곡선(Equity Curve) 차트, 월별 수익률 히트맵, 거래 내역 테이블.
2.  **Hyperopt Optimizer:**
    *   **Config Form:** 최적화할 공간(Spaces: Buy, Sell, ROI, Stoploss 등) 선택, Epoch 수 설정.
    *   **Results:** 최적화된 파라미터 조합 Top 10 리스트, 기존 대비 성능 향상 지표 비교.

---

## 3. 상세 구현 명세 (Implementation Specs)

### 3.1 Backend API Updates (`backend/app/main.py`)

#### A. 전략 관리 (Strategy Management)
*   `GET /api/strategies/detail/{strategy_name}`: 전략 파일의 소스 코드를 읽어 반환 (코드 뷰어용).

#### B. 백테스팅 (Backtesting)
*   `POST /api/backtest/run`: 파라미터 확장 (strategy, timerange, timeframe, fee, enable_protections).
*   `GET /api/backtest/history`: 과거 백테스트 결과 리스트 조회 (`user_data/backtest_results/*.json` 파싱).
*   `GET /api/backtest/result/{filename}`: 특정 결과 상세 조회.
*   **Logic:**
    *   실행 시 `--export trades --export-filename user_data/backtest_results/temp_result.json` 옵션 사용.
    *   결과 JSON을 파싱하여 `profit_total`, `max_drawdown`, `trades` 데이터 추출.

#### C. 최적화 (Hyperopt)
*   `POST /api/hyperopt/run`: Hyperopt 실행.
    *   Parameters: `strategy`, `epochs` (default: 100), `spaces` (list: buy, sell, roi, stoploss, trailing).
    *   Command: `freqtrade hyperopt --strategy {strategy} --hyperopt-loss SharpeHyperOptLoss --spaces {spaces} -e {epochs}`.
*   `GET /api/hyperopt/status`: 현재 진행률(Epoch x/y) 및 로그 조회.
*   `GET /api/hyperopt/results`: 최적화 결과 JSON 반환.

### 3.2 Frontend UI Updates (`frontend/src/`)

#### A. Components (`Desktop.js`, `Shared.js`)
*   **`StrategyLab` Component:** 메인 컨테이너. 탭 메뉴로 Backtest/Hyperopt 전환.
*   **`ConfigForm` Component:**
    *   Strategy: Dropdown (API 연동).
    *   Timerange: DatePicker (Start ~ End) 또는 텍스트 입력 (`20240101-`).
    *   Timeframe: Dropdown (1m, 5m, 15m, 1h, 4h, 1d).
*   **`EquityChart` Component:** `Recharts` 라이브러리를 사용하여 시간 흐름에 따른 잔고 변화 시각화.
*   **`TradeTable` Component:** 거래 내역 리스트 (Paging 처리).

#### B. State Management
*   백테스트/Hyperopt 실행 중에는 "Running..." 상태를 표시하고 중복 실행을 방지(Locking).
*   `setInterval`을 사용하여 3초마다 상태(`status`)를 폴링하여 완료 여부 체크.

---

## 4. 단계별 개발 계획 (Phased Development)

### Phase 1: 백엔드 로직 강화 (Backend Core)
1.  **`BacktestManager` Refactoring:** 단순 실행을 넘어 다양한 파라미터를 받을 수 있도록 `run_process` 메서드 확장.
2.  **`HyperoptManager` Implementation:** Hyperopt 실행 및 프로세스 제어 클래스 신규 작성.
3.  **Result Parser:** Freqtrade 결과 JSON 구조 분석 및 데이터 정제 유틸리티 함수 작성.

### Phase 2: 프론트엔드 - 백테스팅 UI (Frontend Backtest)
1.  **Form UI:** `DesktopBacktest` 컴포넌트를 폼 형태로 변경.
2.  **Chart Integration:** `recharts` 라이브러리 추가(CDN 방식) 및 라인 차트 구현.
3.  **Result View:** 요약 통계(CAGR, Win Rate, MDD) 카드 UI 구현.

### Phase 3: 프론트엔드 - 최적화 UI (Frontend Hyperopt)
1.  **Hyperopt Form:** 최적화 파라미터(Epochs, Spaces) 설정 UI 구현.
2.  **Log Streaming:** 실시간 진행 상황을 보여주는 터미널 뷰 구현 (기존 `DesktopLogs` 재활용).
3.  **Best Params View:** 최적화 완료 후 추천 파라미터 코드 블록 표시.

---

## 5. 예상 파일 구조 변경 (File Structure Changes)

```text
backend/app/
├── main.py           # API 엔드포인트 확장
├── managers.py       # (New) BacktestManager, HyperoptManager 클래스 분리
└── utils.py          # (New) JSON 파싱 및 데이터 처리 헬퍼

frontend/src/
├── components/
│   ├── Desktop.js    # Strategy Lab 탭 통합
│   └── Lab/          # (New) 백테스팅/Hyperopt 관련 컴포넌트 폴더
│       ├── BacktestForm.js
│       ├── HyperoptForm.js
│       ├── ResultsView.js
│       └── EquityChart.js
└── api.js            # 신규 API 함수 추가
```

## 6. 주의사항 (Constraints & Risks)
*   **자원 점유:** Hyperopt는 CPU를 많이 사용하므로, 실행 중에는 봇의 실시간 매매 반응 속도가 느려질 수 있음. (경고 문구 표시 필요)
*   **데이터 용량:** 백테스트 결과 파일이 누적되면 디스크 용량을 차지하므로 주기적인 정리 로직 고려.
*   **Docker 실행 권한:** `docker exec` 실행 시 권한 문제가 발생하지 않도록 `docker.sock` 마운트 설정 재확인.
