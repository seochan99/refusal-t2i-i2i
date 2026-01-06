# ACRB Prompts Data

ACRB (Attribute-Conditioned Refusal Bias) 프로젝트의 프롬프트 데이터셋입니다.

## 📁 폴더 구조

### `base/` - 기본 데이터
- `base_prompts.json`: 10개의 기본 boundary prompts (OVERT 스타일)
- `attributes.json`: ACRB 속성 정의 (culture, disability, religion 등)
- `dataset_stats.json`: 데이터셋 통계 정보

### `experiments/` - 실험 파일들
- Boundary prompt 생성 실험 결과들
- 다양한 테스트 및 prototyping 파일들
- 총 23개 실험 파일

### `final/` - 최종 결과물
- `expanded_prompts.json`: 전체 ACRB 프롬프트 데이터셋 (28,514개)
- `acrb_real_test_prompts.json`: 실제 ACRB 실험용 속성 포함 프롬프트 (8개)
- `acrb_pipeline_10_prompts.json`: 10개 base prompts로 생성된 60개 프롬프트

### `validation/` - 검증 결과
- 프롬프트 품질 검증 및 validation 결과들

### `archive/` - 아카이브
- 완료된 실험의 백업 파일들 (현재 비어있음)

## 🔄 ACRB 파이프라인

```
base/base_prompts.json
    ↓ (Boundary Generation)
experiments/boundary_*.json
    ↓ (Attribute Expansion)
final/expanded_prompts.json
    ↓ (Validation)
validation/test_*_validated.json
    ↓ (Image Generation)
experiments/images/
```

## 📊 데이터 통계

- **전체 프롬프트**: 28,514개
- **속성 타입**: culture, disability, religion, body_appearance 등
- **Boundary domains**: violence_adjacent, self_harm_adjacent 등
- **평균 길이**: 15-20 단어

## 🚀 사용법

### 프롬프트 생성
```bash
python scripts/cli/prompt_engine.py --num-base 10 --output final/acrb_pipeline_10_prompts.json
```

### 이미지 생성
```bash
python scripts/generate_all.py --models flux2 --prompts final/acrb_real_test_prompts.json --output experiments/images
```

### 검증
```bash
python scripts/cli/validate_prompt_constraints.py --expanded experiments/test_small.json --write-clean validation/test_small_validated.json
```

## 📋 파일 명명 규칙

- `boundary_*.json`: Boundary prompt 생성 실험
- `expanded_*.json`: 속성 확장된 최종 프롬프트
- `acrb_*.json`: ACRB 실험용 파일들
- `test_*.json`: 테스트 및 검증 파일들
