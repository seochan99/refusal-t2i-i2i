# ACRB 실험 가이드 - 6 Representative Models with Distinct Safety Policies

## Quick Start (서버에서 바로 실행)

```bash
# 1. 프로젝트 클론/이동
cd /path/to/I2I-T2I-Bias-Refusal

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 로컬 모델만 실행 (4개 모델, 무료, ~24시간)
./run_experiment.sh

# 4. 전체 6개 모델 실행 (API 키 필요)
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."
./run_experiment.sh --all

# 또는 빠른 테스트 (10샘플, 1모델, ~30분)
./run_experiment.sh --quick
```

---

## 모델 선정 기준

**목표**: 안전 정렬(Safety Alignment) 정책이 서로 다른 모델들을 비교하여 Refusal Bias 측정

**제외**: Turbo/Flash 변종 (속도 최적화 버전, 동일한 안전 정책)

**포함**: 의미 있게 다른 콘텐츠 검열 정책을 가진 모델

---

## 6개 대표 모델

| 모델 | 제공사 | 정책 | 타입 | ELO | 비용 |
|------|--------|------|------|-----|------|
| GPT-Image-1.5 | OpenAI | Conservative | T2I | 1256 | API |
| Imagen 3 (Nano Banana Pro) | Google | Moderate-Conservative | T2I | 1221 | API |
| FLUX.2 [dev] | BFL | Permissive | T2I | 1131 | FREE |
| Qwen-Image-Edit-2511 | Alibaba | China-aligned | T2I+I2I | 1133 | FREE |
| SD 3.5 Large | Stability AI | Community | T2I | 1050 | FREE |
| Step1X-Edit | StepFun | China-aligned | I2I | 1081 | FREE |

### 정책 스펙트럼

```
Conservative ◄──────────────────────────────────────────► Permissive
     │                    │                    │              │
 GPT-Image           Imagen 3            SD 3.5          FLUX.2
 (OpenAI)            (Google)          (Stability)        (BFL)
                                            │
                            Qwen-Edit, Step1X (China-aligned)
```

---

## 전체 파이프라인 (5단계)

```
┌─────────────────────────────────────────────────────────────────┐
│  [1] 환경 설정 (~1시간)                                           │
│  └── GPU 확인, Python 설정, 의존성 설치, API 키 설정              │
├─────────────────────────────────────────────────────────────────┤
│  [2] 프롬프트 확인 (~5분)                                         │
│  └── data/prompts/expanded_prompts.json (2,592개 이미 생성됨)    │
├─────────────────────────────────────────────────────────────────┤
│  [3] 이미지 생성                                                  │
│  ├── Local (4 models, ~3시간):                                  │
│  │   ├── FLUX.2-dev: 100 prompts × 30sec = ~50분               │
│  │   ├── Qwen-Edit: 100 prompts × 30sec = ~50분                │
│  │   ├── SD 3.5: 100 prompts × 20sec = ~35분                   │
│  │   └── Step1X-Edit: 100 prompts × 25sec = ~45분              │
│  └── API (2 models, ~30분, 비용 발생):                           │
│      ├── GPT-Image-1.5: 100 prompts × ~$0.04 = ~$4             │
│      └── Imagen 3: 100 prompts × ~$0.04 = ~$4                  │
├─────────────────────────────────────────────────────────────────┤
│  [4] 평가 (~8시간)                                                │
│  ├── CLIP Refusal Detection: ~30분                              │
│  └── VLM Cue Retention (Qwen2.5-VL): ~7시간                     │
├─────────────────────────────────────────────────────────────────┤
│  [5] Human Evaluation (별도)                                     │
│  └── 150 samples, Prolific $150-300                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 단계별 상세 가이드

### Step 1: 환경 설정

```bash
# GPU 확인 (24GB+ VRAM 필요)
nvidia-smi

# Python 환경
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# PyTorch CUDA 확인
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0)}')"
```

### Step 2: 프롬프트 확인

프롬프트는 이미 생성되어 있습니다:
- `data/prompts/base_prompts.json` - 108개 base prompts (9 domains × 12)
- `data/prompts/expanded_prompts.json` - 2,592개 expanded prompts

```bash
# 확인
python -c "import json; d=json.load(open('data/prompts/expanded_prompts.json')); print(f'{len(d)} prompts')"
```

### Step 3: 이미지 생성

#### Option A: 로컬 모델만 (무료, 권장)

```bash
# 4개 로컬 모델, 100 샘플씩
./run_experiment.sh

# 또는 직접 실행
python scripts/generate_all.py \
    --models flux2 qwen-edit sd35 step1x \
    --samples 100 \
    --output experiments/images
```

#### Option B: 전체 6개 모델 (API 키 필요)

```bash
# API 키 설정
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."

# 전체 6개 모델
./run_experiment.sh --all

# 또는 직접 실행
python scripts/generate_all.py \
    --models gpt-image imagen3 flux2 qwen-edit sd35 step1x \
    --samples 100
```

#### Option C: 단일 모델

```bash
# FLUX.2만 (permissive policy)
python scripts/generate_all.py --models flux2 --samples 500

# GPT-Image만 (conservative policy, API 키 필요)
python scripts/generate_all.py --models gpt-image --samples 100
```

#### Option D: 전체 데이터셋 (논문용)

```bash
# 모든 프롬프트 사용 (2,592개 x 6모델 = 15,552 images)
python scripts/generate_all.py \
    --models gpt-image imagen3 flux2 qwen-edit sd35 step1x \
    --samples 2592 \
    --output experiments/images_full
```

### Step 4: 평가

```bash
# 자동 평가 (CLIP + VLM)
python scripts/evaluate_all.py \
    --results-dir experiments/images \
    --vlm qwen-vl

# VLM 없이 (빠름, Hard Refusal만)
python scripts/evaluate_all.py \
    --results-dir experiments/images \
    --skip-cue
```

### Step 5: Disparity 계산

```bash
# 최종 메트릭 계산
python scripts/compute_disparity.py \
    --input experiments/images/evaluation_results.json \
    --output experiments/metrics

# 결과 확인
cat experiments/metrics/disparity_summary.json | python -m json.tool
```

---

## 출력 파일 구조

```
experiments/
├── images/
│   ├── flux2/
│   │   └── {prompt_id}.png
│   ├── qwen-edit/
│   │   └── {prompt_id}.png
│   ├── sd35/
│   │   └── {prompt_id}.png
│   ├── flux2_results.json
│   ├── qwen-edit_results.json
│   ├── sd35_results.json
│   ├── all_results.json
│   └── evaluation_results.json
└── metrics/
    ├── disparity_summary.json
    ├── table_refusal_rates.tex
    └── table_erasure_rates.tex
```

---

## Human Evaluation (별도 진행)

### 샘플 선정

```bash
# 150개 샘플 층화 추출
python -c "
import json
import random

with open('experiments/images/evaluation_results.json') as f:
    results = json.load(f)

# 속성 타입별 30개씩
samples = []
for attr in ['culture', 'gender', 'disability', 'religion', 'age']:
    subset = [r for r in results if r.get('attribute_type') == attr and r.get('output_path')]
    samples.extend(random.sample(subset, min(30, len(subset))))

print(f'Selected {len(samples)} samples for human evaluation')
with open('experiments/human_eval_samples.json', 'w') as f:
    json.dump(samples, f, indent=2)
"
```

### Survey App 실행

```bash
cd survey-app
npm install
npm run dev
# http://localhost:3000 접속
```

---

## 예상 시간 및 비용

| 단계 | GPU 시간 | 실제 시간 | 비용 |
|------|----------|----------|------|
| 환경 설정 | - | 1시간 | $0 |
| 이미지 생성 (300개) | 2-3시간 | 3시간 | $0 |
| CLIP 평가 | 30분 | 30분 | $0 |
| VLM 평가 | 5-8시간 | 8시간 | $0 |
| Human Eval | - | 3-5일 | $150-300 |
| **Total** | **~12시간** | **~2일** | **$150-300** |

**Note**: Human Eval 외에는 모든 비용이 $0입니다.

---

## Troubleshooting

### CUDA Out of Memory

```bash
# 메모리 초과 시 배치 크기 줄이기
python scripts/generate_all.py --models flux2 --samples 50

# 또는 더 작은 모델 사용
python scripts/generate_all.py --models sd35 --samples 100
```

### 모델 다운로드 느림

```bash
# HuggingFace 캐시 확인
du -sh ~/.cache/huggingface/

# 미리 다운로드
huggingface-cli download black-forest-labs/FLUX.2-dev
huggingface-cli download Qwen/Qwen2.5-VL-7B-Instruct
```

### 중간에 중단됨

```bash
# 체크포인트에서 재시작
./run_experiment.sh --resume
```

---

## 실험 완료 후 체크리스트

```
□ experiments/metrics/disparity_summary.json 생성됨
□ experiments/metrics/table_*.tex LaTeX 테이블 생성됨
□ Δ_refusal, Δ_erasure 계산됨
□ 모델별 refusal rate 확인됨
□ Human Eval 샘플 준비됨 (150개)
□ Survey app 작동 확인됨
□ paper/tables/에 테이블 복사됨
```
