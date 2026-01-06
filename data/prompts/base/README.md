# Base Data

기본 프롬프트 데이터와 메타데이터입니다.

## 파일들

- `base_prompts.json` - 10개의 기본 boundary prompts (OVERT 스타일)
- `attributes.json` - ACRB 속성 정의 (culture, disability, religion 등)
- `dataset_stats.json` - 데이터셋 통계 정보

## 사용법

이 파일들은 ACRB 파이프라인의 입력으로 사용됩니다:
```bash
python scripts/cli/prompt_engine.py --num-base 10 --attributes culture:Nigerian disability:wheelchair_user
```