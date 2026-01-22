#!/usr/bin/env python3
"""
AMT 인간 평가 점수를 VLM 점수와 같은 형식으로 정리하는 스크립트

Firebase에서 export한 amt_evaluations 데이터를 입력으로 받아서
500sample_human_score 폴더를 생성합니다.
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def load_amt_sampling_data():
    """AMT 샘플링 데이터 로드"""
    with open('data/amt_sampling/exp1_amt_sampled.json', 'r') as f:
        return json.load(f)

def load_firebase_amt_data(firebase_export_path):
    """Firebase에서 export한 AMT 평가 데이터 로드 (JSON 또는 NDJSON 지원)"""
    data = []

    with open(firebase_export_path, 'r') as f:
        content = f.read().strip()

        # NDJSON 형식인지 JSON 형식인지 확인
        if content.startswith('[') and content.endswith(']'):
            # JSON 배열 형식 (Firebase Console export)
            firebase_data = json.loads(content)

            # Firebase export 데이터를 firestore 문서 형식으로 변환
            for item in firebase_data:
                # Firebase export 형식에서 firestore 문서 형식으로 변환
                doc = {
                    'fields': {}
                }

                for key, value in item.items():
                    if key != '__id__':  # __id__ 필드는 제외
                        # 값 타입에 따라 적절한 형식으로 변환
                        if isinstance(value, str):
                            doc['fields'][key] = {'stringValue': value}
                        elif isinstance(value, int):
                            doc['fields'][key] = {'integerValue': value}
                        elif isinstance(value, bool):
                            doc['fields'][key] = {'booleanValue': value}
                        else:
                            doc['fields'][key] = {'stringValue': str(value)}

                data.append(doc)

            return data

        elif '\n' in content and not content.startswith('{'):
            # NDJSON 형식 (각 줄이 JSON 객체)
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f'⚠️  JSON 파싱 오류 (건너뜀): {e}')
            return data
        else:
            # 단일 JSON 객체
            return json.loads(content)

def extract_field_value(field_data):
    """Firebase 필드 값에서 실제 값 추출"""
    if isinstance(field_data, dict):
        if 'stringValue' in field_data:
            return field_data['stringValue']
        elif 'integerValue' in field_data:
            return int(field_data['integerValue'])
        elif 'booleanValue' in field_data:
            return field_data['booleanValue']
        elif 'timestampValue' in field_data:
            return field_data['timestampValue']
    return field_data

def extract_human_scores(amt_data, firebase_data):
    """Firebase 데이터에서 인간 평가 점수 추출 및 AMT 샘플과 매핑 (다중 평가 지원)"""

    # Firebase 데이터를 originalItemId -> list of evaluations로 매핑
    firebase_scores = defaultdict(list)

    for doc in firebase_data:
        fields = doc.get('fields', {})

        # originalItemId 추출 (exp1_step1x_B02_SoutheastAsian_Female_40s)
        original_item_id = extract_field_value(fields.get('originalItemId', {}))

        if original_item_id:
            # 작업자 정보 추출
            worker_id = extract_field_value(fields.get('userId', {}))
            task_id = extract_field_value(fields.get('taskId', {}))

            # edited 버전 점수 추출
            edited_scores = {
                'edit_success': extract_field_value(fields.get('edited_edit_success', {})),
                'skin_tone': extract_field_value(fields.get('edited_skin_tone', {})),
                'race_drift': extract_field_value(fields.get('edited_race_drift', {})),
                'gender_drift': extract_field_value(fields.get('edited_gender_drift', {})),
                'age_drift': extract_field_value(fields.get('edited_age_drift', {}))
            }

            # preserved 버전 점수 추출
            preserved_scores = {
                'edit_success': extract_field_value(fields.get('preserved_edit_success', {})),
                'skin_tone': extract_field_value(fields.get('preserved_skin_tone', {})),
                'race_drift': extract_field_value(fields.get('preserved_race_drift', {})),
                'gender_drift': extract_field_value(fields.get('preserved_gender_drift', {})),
                'age_drift': extract_field_value(fields.get('preserved_age_drift', {}))
            }

            # 평가 정보 저장
            evaluation = {
                'worker_id': worker_id,
                'task_id': task_id,
                'edited': edited_scores,
                'preserved': preserved_scores
            }

            firebase_scores[original_item_id].append(evaluation)

    # AMT 샘플과 인간 평가 점수 매핑 (다중 평가 지원)
    human_scores = []

    for amt_item in amt_data['items']:
        amt_id = amt_item['id']  # exp1_flux_B01_Latino_Female_40s
        evaluations = firebase_scores.get(amt_id, [])

        # 각 평가를 개별적으로 저장 (다중 평가 지원)
        for evaluation in evaluations:
            result_item = {
                'amt_item': amt_item,
                'human_scores': evaluation['edited'],  # AMT는 edited 버전 평가
                'worker_id': evaluation['worker_id'],
                'task_id': evaluation['task_id'],
                'version': 'edited'
            }
            human_scores.append(result_item)

    return human_scores

def create_human_score_folders(human_scores):
    """500sample_human_score 폴더 생성"""

    # 폴더 생성
    os.makedirs('500sample_human_score', exist_ok=True)

    # 모델별로 그룹화 및 저장
    models = ['flux', 'qwen', 'step1x']

    for model in models:
        model_scores = [s for s in human_scores if s['amt_item']['model'] == model]

        if model_scores:
            output_file = f'500sample_human_score/{model}_human_scores.json'
            with open(output_file, 'w') as f:
                json.dump(model_scores, f, indent=2)

            print(f'✅ {model}: {len(model_scores)}개 인간 평가 점수 저장')

def main():
    """메인 함수"""

    print('=== AMT 인간 평가 점수 정리 스크립트 ===')
    print()

    # Firebase export 파일 경로 (기본값 설정 또는 사용자 입력)
    default_path = 'firebase_amt_export.json'
    if os.path.exists(default_path):
        firebase_export_path = default_path
        print(f'📁 기본 파일 발견: {default_path}')
    else:
        firebase_export_path = input('Firebase export 파일 경로를 입력하세요 (예: firebase_amt_export.json): ')

    if not os.path.exists(firebase_export_path):
        print(f'❌ 파일을 찾을 수 없습니다: {firebase_export_path}')
        return

    try:
        # 데이터 로드
        print('📥 데이터 로드 중...')
        amt_data = load_amt_sampling_data()
        firebase_data = load_firebase_amt_data(firebase_export_path)

        print(f'✅ AMT 샘플링 데이터: {len(amt_data["items"])}개')
        print(f'✅ Firebase 평가 데이터: {len(firebase_data)}개 문서')

        # Firebase 데이터 샘플 확인
        if firebase_data:
            sample_doc = firebase_data[0]
            print(f'📋 샘플 문서 필드: {list(sample_doc.get("fields", {}).keys())[:10]}...')

        # 인간 평가 점수 추출
        print('🔄 인간 평가 점수 추출 및 매핑 중...')
        human_scores = extract_human_scores(amt_data, firebase_data)

        print(f'✅ 매핑된 인간 평가: {len(human_scores)}개')

        # 폴더 생성 및 저장
        print('💾 500sample_human_score 폴더 생성 중...')
        create_human_score_folders(human_scores)

        print()
        print('🎉 완료! 500sample_human_score 폴더가 생성되었습니다.')
        print()
        print('📊 폴더 구조:')
        print('500sample_human_score/')
        print('├── flux_human_scores.json')
        print('├── qwen_human_scores.json')
        print('└── step1x_human_scores.json')

    except Exception as e:
        print(f'❌ 오류 발생: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()