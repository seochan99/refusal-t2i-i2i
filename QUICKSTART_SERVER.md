# ACRB - Server Quick Start Guide

서버에서 바로 실행 가능한 완전한 실험 파이프라인

## 1. 환경 설정 (1회만)

```bash
# 프로젝트 디렉토리로 이동
cd /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal

# 의존성 설치
pip install -r requirements.txt

# (선택) VLM 평가를 위한 API 키 설정
export OPENAI_API_KEY="sk-your-api-key-here"

# 설정 테스트
python scripts/test_setup.py
```

## 2. 빠른 실행 (통합 스크립트)

```bash
# 기본 실행: FLUX.1-dev, 100 샘플
./run_experiment.sh

# 커스텀 모델 및 샘플 수
./run_experiment.sh flux 500
./run_experiment.sh sdxl 1000
```

## 3. 단계별 실행 (상세 제어)

### Step 1: 이미지 생성

```bash
# FLUX.1-dev (권장)
python scripts/generate_all.py --models flux --samples 100

# 여러 모델 동시 실행
python scripts/generate_all.py --models flux sd35 sdxl --samples 100

# I2I 모드 (소스 이미지 필요)
python scripts/generate_all.py \
  --models instruct-pix2pix \
  --mode i2i \
  --source-images-dir data/external/ffhq \
  --samples 100
```

**출력**: `experiments/generation/images/` 폴더에 이미지 생성

### Step 2: 평가 (CLIP + VLM)

```bash
# 전체 평가 (CLIP 거부 감지 + VLM 속성 유지 점수)
python scripts/evaluate_all.py --results-dir experiments/generation

# CLIP만 (API 키 불필요)
python scripts/evaluate_all.py --results-dir experiments/generation --skip-cue

# 테스트 (50개 샘플만)
python scripts/evaluate_all.py \
  --results-dir experiments/generation \
  --max-samples 50
```

**출력**: `experiments/generation/evaluation_results.json`

### Step 3: 결과 계산 및 테이블 생성

```bash
# 논문용 테이블 생성
python scripts/compute_results.py \
  --input experiments/generation/evaluation_results.json \
  --output paper/tables

# CSV만 출력
python scripts/compute_results.py \
  --input experiments/generation \
  --format csv \
  --output experiments/tables
```

**출력**:
- `paper/tables/disparity_metrics.json` - 전체 메트릭
- `paper/tables/summary_table.csv` - 요약 테이블
- `paper/tables/attribute_table.csv` - 속성별 분석

## 4. 결과 확인

```bash
# 메트릭 확인
cat paper/tables/disparity_metrics.json | python -m json.tool

# CSV 테이블 확인
column -t -s, paper/tables/summary_table.csv

# 생성된 이미지 확인
ls -lh experiments/generation/images/ | head -20
```

## 5. 고급 사용법

### 중단된 실험 재개

```bash
python scripts/generate_all.py \
  --models flux \
  --samples 1000 \
  --resume
```

### 커스텀 프롬프트 사용

```bash
# 1. 프롬프트 JSON 파일 준비
# data/prompts/custom_prompts.json

# 2. 생성
python scripts/generate_all.py \
  --models flux \
  --prompts-file data/prompts/custom_prompts.json
```

### 거부 감지 임계값 조정

```bash
python scripts/evaluate_all.py \
  --results-dir experiments/generation \
  --refusal-threshold 0.3  # 기본값: 0.25
```

## 6. 문제 해결

### GPU 메모리 부족

```bash
# 더 작은 모델 사용
python scripts/generate_all.py --models sdxl --samples 100

# 샘플 수 줄이기
python scripts/generate_all.py --models flux --samples 10
```

### VLM API 속도 제한

```bash
# VLM 평가 건너뛰기
python scripts/evaluate_all.py --skip-cue --results-dir experiments/generation

# 또는 샘플 제한
python scripts/evaluate_all.py --max-samples 50 --results-dir experiments/generation
```

### 의존성 설치 오류

```bash
# CLIP 수동 설치
pip install git+https://github.com/openai/CLIP.git

# PyTorch 재설치 (CUDA 11.8 예시)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## 7. 예상 실행 시간 및 비용

### 로컬 GPU (RTX 4090 기준)

| 모델 | 샘플 수 | 생성 시간 | 평가 시간 | VLM 비용 |
|------|---------|-----------|-----------|----------|
| FLUX | 100 | ~47분 | ~5분 | ~$0.10 |
| FLUX | 1000 | ~8시간 | ~30분 | ~$1.00 |
| SD3.5 | 100 | ~58분 | ~5분 | ~$0.10 |
| SDXL | 100 | ~33분 | ~5분 | ~$0.10 |

### 논문 실험 (권장)

```bash
# 각 모델당 1000 샘플
./run_experiment.sh flux 1000
./run_experiment.sh sd35 1000
./run_experiment.sh sdxl 1000

# 총 실행 시간: ~20-25 시간
# 총 VLM 비용: ~$3
```

## 8. 체크리스트

실험 시작 전 확인:

- [ ] GPU 메모리 16GB 이상
- [ ] 디스크 공간 50GB 이상 (1000 샘플 기준)
- [ ] PyTorch GPU 버전 설치 확인
- [ ] (선택) OPENAI_API_KEY 환경변수 설정
- [ ] 테스트 실행 성공: `python scripts/test_setup.py`

## 9. 지원 모델

### T2I (Text-to-Image)

| 모델 키 | 이름 | 메모리 | 속도 | 품질 |
|---------|------|--------|------|------|
| `flux` | FLUX.1-dev | 12GB | 28s/img | 최고 |
| `sd35` | SD 3.5 Large | 14GB | 35s/img | 높음 |
| `sdxl` | SDXL | 8GB | 20s/img | 중간 |

### I2I (Image-to-Image)

| 모델 키 | 이름 | 메모리 | 속도 |
|---------|------|--------|------|
| `instruct-pix2pix` | InstructPix2Pix | 6GB | 15s/img |

## 10. 디렉토리 구조

```
I2I-T2I-Bias-Refusal/
├── scripts/
│   ├── generate_all.py          # 이미지 생성
│   ├── evaluate_all.py          # 평가
│   ├── compute_results.py       # 결과 계산
│   └── test_setup.py            # 설정 테스트
├── acrb/                        # 핵심 라이브러리
├── data/                        # 데이터
├── experiments/                 # 실험 결과
├── paper/tables/                # 논문 테이블
├── requirements.txt             # 의존성
├── run_experiment.sh            # 통합 실행 스크립트
└── EXPERIMENT_README.md         # 상세 문서
```

## 11. 다음 단계

실험 완료 후:

1. 결과 분석: `paper/tables/disparity_metrics.json` 확인
2. 시각화: `scripts/plot_results.py` 실행 (선택)
3. 논문 작성: `paper/main.tex` 업데이트
4. 추가 실험: 다른 모델로 반복

## 문의

- 프로젝트 문서: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/EXPERIMENT_README.md`
- 알고리즘 설명: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/ALGORITHM_IMPLEMENTATION.md`
