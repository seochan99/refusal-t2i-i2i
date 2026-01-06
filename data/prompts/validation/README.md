# Validation

프롬프트 검증 및 품질 평가 결과입니다.

## 파일들

- `test_small_validated.json` - 검증된 테스트 프롬프트들

## 검증 기준

프롬프트 검증은 다음 기준으로 수행됩니다:

1. **구조 유효성**: JSON 포맷, 필드 존재 여부
2. **형식 검증**: 길이, 중복 검사
3. **의미적 일관성**: base prompt와의 연결성
4. **속성 통합**: attribute의 자연스러운 포함

## 검증 결과

```
✅ 유효한 프롬프트: 12/12
❌ 중복 프롬프트: 0개
📏 평균 길이: 5.5 단어
🏷️ 속성 다양성: culture, disability, religion 등
```

## 사용법

```bash
# 프롬프트 검증 실행
python scripts/cli/validate_prompt_constraints.py --expanded data/prompts/experiments/test_small.json --write-clean data/prompts/validation/test_small_validated.json
```
