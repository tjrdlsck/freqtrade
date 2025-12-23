# 🤖 Project Sentinel: 퀀트 시스템 개발 및 운용 가이드 (V1 ~ V11)

본 문서는 2023년부터 2025년까지의 시장 데이터를 정복하기 위해 수행된 전략 분석, 수정, 최적화 및 검증의 모든 과정을 기록한 마스터 가이드입니다.

---

## 🏛️ 1. 개발 철학 및 워크플로우 (Development Philosophy)

우리는 **'반복적 정교화(Iterative Refinement)'** 프로세스를 채택하여, 단순한 지표의 조합을 넘어 시장의 본질적인 변동성을 수익화하는 알고리즘을 구축했습니다.

### 🔄 순환 구조
1.  **백테스팅(Backtesting):** 과거 데이터를 통한 가설 검증.
2.  **분석(Analysis):** 수익률 저하 구간(Drawdown)의 원인 파악 (휩소, 손익비 불균형 등).
3.  **수정(Modification):** 로직 개편 및 필터 강화.
4.  **최적화(Optimization):** 하이퍼파라미터 튜닝 및 레버리지 조절.
5.  **검증(Validation):** 학습하지 않은 미래 데이터(2025년)로 일반화 성능 확인.

---

## 📈 2. 전략 진화 과정 (Strategy Evolution)

| 버전 | 핵심 개념 (Core Concept) | 성과 및 한계 |
| :--- | :--- | :--- |
| **V1** | RSI 기반 평균 회귀 (Mean Reversion) | 추세장에서 대규모 손실 발생. |
| **V2** | EMA 추세 필터 + 볼린저 밴드 돌파 | 잦은 청산 신호로 인해 수익 보존 실패. |
| **V3** | **에너지 응축 돌파 (Volatility Squeeze)** | **최초 수익권 진입.** 70% 이상의 높은 승률 확보. |
| **V4-V7** | 시간 필터 및 정밀 필터 시도 | 2025년 특유의 변동성에 과적합(Overfitting) 발생. |
| **V8** | 하이퍼 스캘핑 + 5배 레버리지 | 1,600% 이상의 경이로운 수익률 달성 (공격적 모델). |
| **V11** | **비대칭 레버리지 + 거래 소진 청산** | **[최종 완성판]** 안정성(MDD 16%)과 수익성(212%)의 황금 비율. |

---

## 🧪 3. 검증 방법론 (Validation Methodology)

우리는 통계적 유의성을 확보하기 위해 다음의 엄격한 데이터 분리 원칙을 준수했습니다.

1.  **학습 데이터 (Training Set):** `20230101-20241231` (2년)
    *   기초 로직 수립 및 하이퍼파라미터 도출에 사용.
2.  **검증 데이터 (Validation Set):** `20250101-현재` (1년)
    *   학습에 관여하지 않은 데이터로 전략의 실제 생존력 테스트.
3.  **강건성 테스트 (Robustness Test):**
    *   **유니버스 확장:** 10종에서 15종으로 종목 확대 시 성과 유지 확인.
    *   **민감도 분석:** 파라미터 미세 조정(ADX ±1) 시 수익 곡선의 일관성 확인.

---

## 🛠️ 4. 시스템 설정 및 운용 가이드 (Operational Guide)

### 📂 주요 파일 구조
*   `/strategies/SentinelStrategyV11.py`: 현재 가동 중인 최종 병기.
*   `/strategies/SentinelStrategyV8.py`: 고수익 추구 시 사용하는 예비 병기.
*   `config.json`: 거래소 API, 텔레그램, 자산 배분 핵심 설정.

### 🚀 명령어 셋 (CLI Cheat Sheet)

#### 봇 가동 및 관리
```bash
# 봇 배경 실행 (실전/모의매매 시작)
docker compose up -d

# 봇 중지
docker compose down

# 봇 재시작 (설정 변경 후 필수)
docker compose restart freqtrade

# 실시간 로그 모니터링
docker compose logs -f --tail 50 freqtrade
```

#### 백테스팅 실행 (검증용)
```bash
# 2025년 순수 검증 데이터 백테스팅
docker compose run --rm freqtrade backtesting --config /freqtrade/user_data/config.json --strategy SentinelStrategyV11 --timerange 20250101- --timeframe 1h
```

---

## 📱 5. 텔레그램 연동 및 명령 (Telegram Control)

`config.json`의 `telegram` 섹션에 정보를 입력한 후 다음 명령어로 봇을 제어합니다.

*   `/status`: 현재 실행 상태 및 수익 현황.
*   `/balance`: 가상 지갑(Dry-run) 잔고 확인.
*   `/profit`: 누적 손익 리포트.
*   `/start` / `/stop`: 매매 엔진 일시 중지 및 재개.

---

## 💡 6. 마스터 퀀트의 유지보수 조언

1.  **손익비(Risk/Reward Ratio) 관리:**
    평균 수익($R_{avg}$)과 평균 손실($L_{avg}$)의 비율을 최소 1:1.5 이상 유지하십시오.
    $$Profit\,Factor = \frac{\sum Profits}{\sum Losses}$$
    이 수치가 1.2 미만으로 떨어지면 전략을 재점검해야 합니다.

2.  **체제 변화(Regime Change) 대응:**
    시장의 변동성(ATR)이 평소보다 2배 이상 커지거나, 승률이 60% 미만으로 2주 이상 지속될 경우 파라미터 최적화(Hyperopt)를 다시 수행하십시오.

3.  **복리의 마법 활용:**
    현재 `"stake_amount": "unlimited"` 설정이므로, 수익이 나면 투자 단위가 자동으로 커집니다. 계좌가 2배가 될 때마다 원금을 출금하거나 리스크를 낮추는 전략을 권장합니다.

---

**최종 업데이트:** 2025년 12월 23일
**참고 자료:** [Freqtrade Official Docs](https://www.freqtrade.io/) | [Binance Futures API](https://binance-docs.github.io/apidocs/futures/en/)
