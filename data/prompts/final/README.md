# Final Results

ACRB 파이프라인의 최종 결과물들입니다.

## 파일들

- `expanded_prompts.json` - 전체 ACRB 프롬프트 데이터셋 (28,514개)
- `acrb_pipeline_10_prompts.json` - 10개 base prompts로 생성된 60개 프롬프트
- `acrb_real_test_prompts.json` - 실제 ACRB 실험용 속성 포함 프롬프트 (8개)
- `expanded_prompts_10_base.json` - 10개 base로 확장된 프롬프트들

## 사용법

이 파일들은 이미지 생성 및 평가에 사용됩니다:

```bash
# 이미지 생성
python scripts/generate_all.py --models flux2 --prompts final/acrb_real_test_prompts.json --output experiments/images

# 평가
python scripts/utils/evaluate_all.py --images experiments/images --output experiments/results
```

## 데이터 구조

각 프롬프트는 다음 필드를 포함:
- `id`: 고유 식별자
- `base_text`: 원본 boundary prompt
- `boundary_text`: 생성된 boundary prompt
- `expanded_text`: 속성 확장된 최종 프롬프트
- `attribute_type/value`: 적용된 속성 정보
- `domain`: Boundary domain (violence_adjacent, etc.)
