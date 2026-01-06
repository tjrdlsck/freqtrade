# 🛡️ Project Sentinel Strategy Lab

**Last Updated:** 2026-01-06
**System Version:** Sentinel Engine v1.0 (Based on Freqtrade 2025.12-dev)

본 저장소는 암호화폐 선물 시장의 변동성을 극복하기 위해 설계된 **SentinelStrategy**의 연구 및 운용 환경입니다. 모든 프로세스는 Docker Compose를 통해 격리되고 안전하게 실행됩니다.

---

## 1. 🚀 빠른 시작 (Quick Start)

### 1.1 데이터 준비
백테스팅 및 최적화를 위해 바이낸스 선물 시장의 과거 데이터를 수집합니다.
```bash
# 최근 30일치 데이터 다운로드 (1h, 5m 타임프레임)
docker compose run --rm sentinel-bot download-data --days 30 -t 1h 5m
```

### 1.2 백테스팅 (Backtesting)
작성된 전략이 과거 시장에서 어떤 퍼포먼스를 보였는지 검증합니다.
```bash
docker compose run --rm sentinel-bot backtesting --strategy SentinelStrategy --timerange 20250101-
```

### 1.3 하이퍼옵트 (Hyperopt)
AI를 통해 전략의 최적 파라미터(RSI, ATR, Timeout 등)를 탐색합니다.
```bash
docker compose run --rm sentinel-bot hyperopt --strategy SentinelStrategy --spaces buy sell --epochs 100 --hyperopt-loss SharpeHyperOptLoss
```

---

## 2. 🛠️ 자동화 파이프라인 (Automation)

본 프로젝트는 대규모 데이터 분석을 위한 전용 파이썬 스크립트를 제공합니다.

1.  **`backtest_automation.py`**: 6개월 단위로 기간을 분할하여 전수 백테스팅을 수행합니다.
2.  **`master_data_extractor.py`**: 생성된 수많은 결과 파일에서 핵심 지표만 추출하여 CSV로 병합합니다.
3.  **`generate_strategy_report.py`**: 추출된 데이터를 바탕으로 통합 성과 보고서를 자동 생성합니다.

---

## 3. 📈 실전 운용 (Dry Run / Live)

검증이 완료된 전략을 실시간 시장에 투입합니다.

```bash
# 봇 실행 (Background 모드)
docker compose up -d

# 로그 실시간 모니터링
docker compose logs -f

# 봇 중지 및 컨테이너 제거
docker compose down
```

---

## 4. 📚 주요 문서
*   [SENTINEL_MASTER_LOG.md](./SENTINEL_MASTER_LOG.md): 전략의 개발 역사, 로직 변경점 및 통합 성과 보고서.
*   [CONVENTIONS.md](./CONVENTIONS.md): 프로젝트 코드 스타일 및 보안 가이드라인.

---
**주의:** 본 시스템은 금융 자산을 다룹니다. `config_dryrun.json`에 포함된 API Key가 외부로 노출되지 않도록 주의하십시오.