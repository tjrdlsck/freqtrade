# Project Sentinel Strategy Lab Guide

**Last Updated:** 2025-12-23
**System Version:** Freqtrade Docker 2025.12-dev

본 문서는 Project Sentinel의 코어 트레이딩 엔진인 **Freqtrade**를 사용하여 전략을 검증(Backtesting)하고 최적화(Hyperopt)하는 방법을 설명합니다. 모든 명령어는 Docker Compose 환경에서 안전하게 실행되도록 구성되었습니다.

---

## 1. 사전 준비 (Prerequisites)

터미널에서 프로젝트 루트 디렉토리(`/home/inseok/docker/auto_stock`)로 이동한 상태여야 합니다.

### 1.1 설정 확인
`user_data/config.json` 파일에 거래할 코인 쌍(Pair)이 등록되어 있는지 확인하십시오.
```json
"pair_whitelist": [
    "BTC/USDT:USDT",
    "ETH/USDT:USDT"
]
```

---

## 2. 데이터 다운로드 (Download Data)

백테스팅과 최적화를 수행하기 위해서는 과거 시장 데이터가 필요합니다.

**명령어:**
```bash
# 최근 30일 치 데이터 다운로드 (Timeframe: 5분, 1시간)
docker compose run --rm freqtrade download-data --config user_data/config.json --days 30 -t 5m 1h
```

*   `--rm`: 작업 완료 후 임시 컨테이너를 삭제합니다.
*   `--days 30`: 다운로드할 기간(일)입니다.
*   `-t 5m 1h`: 전략에 필요한 캔들 시간 단위입니다.

---

## 3. 백테스팅 (Backtesting)

작성된 전략(`SentinelStrategyV1.py`)이 과거 데이터에서 어떤 성과를 냈는지 검증합니다.

**명령어:**
```bash
# 전략 실행 및 성과 분석
docker compose run --rm freqtrade backtesting --config user_data/config.json --strategy SentinelStrategyV1 --timerange 20250101-
```

### 주요 옵션
*   `--strategy`: 테스트할 전략 클래스 이름입니다 (`user_data/strategies/` 폴더 내 파일).
*   `--timerange`: 테스트할 기간입니다. (예: `20250101-` 2025년 1월 1일부터 현재까지)
*   `--fee`: (선택) 거래 수수료를 강제 적용합니다. (예: `0.0005` = 0.05%)

**주의:** 명령어에 `-t 5m` 등 타임프레임 옵션을 직접 넣지 마십시오. 전략 파일 내의 설정을 자동으로 따릅니다.

---

## 4. 옵션 최적화 (Hyperopt)

전략의 수익률을 극대화하는 최적의 파라미터(RSI 값, 손절/익절 비율 등)를 AI가 탐색합니다.

**명령어:**
```bash
# Sharpe Ratio(수익/변동성)를 기준으로 최적값 탐색 (100세대 반복)
docker compose run --rm freqtrade hyperopt --config user_data/config.json --strategy SentinelStrategyV1 --hyperopt-loss SharpeHyperOptLoss --spaces buy sell --epochs 100
```

### 주요 옵션
*   `--hyperopt-loss`: 최적화 기준 함수입니다.
    *   `SharpeHyperOptLoss`: 안정적인 고수익 추구 (추천).
    *   `SortinoHyperOptLoss`: 하락 변동성 최소화.
    *   `ProfitDrawDownHyperOptLoss`: 단순 수익금 위주.
*   `--spaces`: 최적화할 영역을 지정합니다.
    *   `buy`: 매수 지표 (예: `buy_rsi`)
    *   `sell`: 매도 지표 (예: `sell_rsi`)
    *   `roi`: 익절(Take Profit) 구간
    *   `stoploss`: 손절(Stop Loss) 구간
*   `--epochs`: 시뮬레이션 반복 횟수입니다. 실전용 최적화 시 **500 이상** 권장합니다.

### 결과 적용
Hyperopt가 완료되면 터미널 하단에 **Best Result** 코드가 출력됩니다. 이를 복사하여 `SentinelStrategyV1.py` 파일의 해당 섹션에 덮어쓰십시오.

```python
# 예시:
# Buy parameters
buy_rsi = IntParameter(10, 40, default=25, space="buy")  # 30 -> 25로 변경
```

---

## 5. 실전 구동 및 관리

검증이 끝난 전략을 실전(Dry Run 또는 Live)에 투입합니다.

**실행:**
```bash
# 백그라운드 모드로 봇 실행
docker compose up -d
```

**로그 확인:**
```bash
# 실시간 로그 모니터링 (종료하려면 Ctrl+C)
docker compose logs -f
```

**중지:**
```bash
docker compose down
```

---

## 6. 트러블슈팅 (Troubleshooting)

*   **`unrecognized arguments: -t ...` 오류:**
    *   백테스팅/Hyperopt 명령어에서 `-t` 옵션을 제거하십시오. 전략 파일에 정의된 값을 우선합니다.
*   **`No data found` 오류:**
    *   `download-data` 명령어로 데이터를 먼저 받았는지 확인하십시오.
    *   `--timerange`가 다운로드한 데이터 기간 내에 있는지 확인하십시오.
*   **Permission denied 오류:**
    *   `user_data` 폴더의 권한 문제일 수 있습니다. `sudo chown -R $USER:$USER freqtrade/user_data` 명령어로 소유권을 복구하십시오.
# freqtrade
