# AMT HIT Configuration Guide

## Overview

This document describes the Amazon Mechanical Turk (AMT) HIT configuration for the Exp2 human evaluation study.

## HIT Structure

### Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Items per HIT | 10 | Each HIT contains 10 evaluation items |
| Total Items | 500 | 500 unique items to evaluate |
| Total HITs | 50 | 500 / 10 = 50 unique HITs |
| Raters per Item | 3 | Each item evaluated by 3 different workers |
| Total Assignments | 150 | 50 HITs × 3 raters |

### Payment Structure

| Item | Amount |
|------|--------|
| Payment per HIT | $6.00 |
| Base Payment (150 HITs) | $225.00 |
| MTurk Fee (20%) | $45.00 |
| Bonus Pool (10%) | $22.00 |
| Buffer | $8.00 |
| **Total Budget** | **$300.00** |

### Time Estimates

- **Estimated time per HIT**: 30-40 minutes
- **Hourly rate**: ~$10-12/hr

---

## URL Format

### HIT Mode URL

Workers access the survey via a URL with these parameters:

```
https://your-domain.com/eval/exp2?hitId={HIT_ID}&workerId={WORKER_ID}
```

**Parameters:**
- `hitId`: Integer 1-50, determines which 10 items to show
- `workerId`: AMT Worker ID for duplicate prevention

### Example URLs

```
# HIT 1: Items 1-10
/eval/exp2?hitId=1&workerId=A1B2C3D4E5

# HIT 25: Items 241-250
/eval/exp2?hitId=25&workerId=A1B2C3D4E5

# HIT 50: Items 491-500
/eval/exp2?hitId=50&workerId=A1B2C3D4E5
```

---

## Item Assignment Logic

```javascript
// Given hitId, calculate item range
const ITEMS_PER_HIT = 10

function getItemRange(hitId) {
  const startIdx = (hitId - 1) * ITEMS_PER_HIT  // 0-indexed
  const endIdx = startIdx + ITEMS_PER_HIT
  return { startIdx, endIdx }
}

// Example:
// hitId=1  → items[0-9]   (items 1-10)
// hitId=2  → items[10-19] (items 11-20)
// hitId=50 → items[490-499] (items 491-500)
```

---

## Duplicate Prevention

### Worker-HIT Tracking

The system tracks worker-HIT combinations in Firebase:

**Collection**: `exp2_hit_completions`

**Document ID**: `{workerId}_hit{hitId}`

**Fields**:
```json
{
  "workerId": "A1B2C3D4E5",
  "hitId": 1,
  "userId": "firebase-user-id",
  "userEmail": "worker@email.com",
  "completionCode": "AMT-H01-A1B2C3-KR5M8X",
  "completedItems": 10,
  "completedAt": "2026-01-19T10:30:00Z"
}
```

### Prevention Logic

1. When worker accesses HIT URL, system checks if completion record exists
2. If record exists, worker sees "HIT Already Completed" message
3. If not, worker proceeds to evaluation

---

## Completion Code Format

### Code Structure

```
AMT-H{HIT_ID}-{WORKER_HASH}-{TIMESTAMP}
```

**Components**:
- `AMT`: Prefix indicating AMT HIT completion
- `H{HIT_ID}`: 2-digit HIT number (e.g., H01, H25, H50)
- `{WORKER_HASH}`: First 6 characters of Worker ID (uppercase)
- `{TIMESTAMP}`: Base36 timestamp

### Example Codes

```
AMT-H01-A1B2C3-KR5M8X    # HIT 1
AMT-H25-XY9Z01-LT7N2P    # HIT 25
AMT-H50-QW3E4R-MS9K1J    # HIT 50
```

---

## MTurk HIT Template

### External Question XML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd">
  <ExternalURL>https://your-domain.com/eval/exp2?hitId=${hitId}&amp;workerId=${workerId}</ExternalURL>
  <FrameHeight>800</FrameHeight>
</ExternalQuestion>
```

### HIT Properties

```json
{
  "Title": "Image Comparison Study - Evaluate AI-Edited Photos",
  "Description": "Compare original photos with AI-edited versions. Rate changes in skin tone, race, gender, and age. ~35 minutes, $6.00 payment.",
  "Keywords": "image, photo, comparison, AI, rating, survey",
  "Reward": "6.00",
  "AssignmentDurationInSeconds": 3600,
  "LifetimeInSeconds": 604800,
  "MaxAssignments": 3,
  "QualificationRequirements": [
    {
      "QualificationTypeId": "000000000000000000L0",
      "Comparator": "GreaterThanOrEqualTo",
      "IntegerValues": [95]
    },
    {
      "QualificationTypeId": "00000000000000000040",
      "Comparator": "GreaterThanOrEqualTo",
      "IntegerValues": [500]
    },
    {
      "QualificationTypeId": "00000000000000000071",
      "Comparator": "EqualTo",
      "LocaleValues": [{"Country": "US"}]
    }
  ]
}
```

### Qualification Requirements

| Requirement | ID | Condition |
|-------------|-----|-----------|
| Approval Rate | 000000000000000000L0 | ≥ 95% |
| HITs Completed | 00000000000000000040 | ≥ 500 |
| Location | 00000000000000000071 | US only |

---

## Quality Control

### Attention Checks

- 5 gold standard items (10% of 50 HITs)
- Clearly correct answers expected
- Workers failing >1 attention check may be rejected

### Rejection Criteria

| Criterion | Threshold | Action |
|-----------|-----------|--------|
| Attention check accuracy | < 80% | Reject |
| Completion time | < 15 minutes | Review |
| Response variance | Zero variance | Reject |

### Bonus Criteria

| Criterion | Bonus |
|-----------|-------|
| 100% attention check accuracy | +$0.50 |
| Thoughtful open-ended responses | +$0.25 |

---

## Batch Creation

### Creating 50 HITs with 3 Assignments Each

```python
import boto3

client = boto3.client('mturk', region_name='us-east-1')

for hit_id in range(1, 51):
    external_url = f"https://your-domain.com/eval/exp2?hitId={hit_id}&workerId=${{workerId}}"

    question = f'''<?xml version="1.0" encoding="UTF-8"?>
    <ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd">
      <ExternalURL>{external_url}</ExternalURL>
      <FrameHeight>800</FrameHeight>
    </ExternalQuestion>'''

    response = client.create_hit(
        Title='Image Comparison Study - Evaluate AI-Edited Photos',
        Description='Compare original photos with AI-edited versions. ~35 min, $6.00',
        Keywords='image,photo,comparison,AI,rating',
        Reward='6.00',
        MaxAssignments=3,
        LifetimeInSeconds=604800,
        AssignmentDurationInSeconds=3600,
        Question=question,
        QualificationRequirements=[
            {'QualificationTypeId': '000000000000000000L0', 'Comparator': 'GreaterThanOrEqualTo', 'IntegerValues': [95]},
            {'QualificationTypeId': '00000000000000000040', 'Comparator': 'GreaterThanOrEqualTo', 'IntegerValues': [500]},
            {'QualificationTypeId': '00000000000000000071', 'Comparator': 'EqualTo', 'LocaleValues': [{'Country': 'US'}]}
        ]
    )

    print(f"Created HIT {hit_id}: {response['HIT']['HITId']}")
```

---

## Firebase Collections

### exp2_evaluations

Individual item evaluations.

```json
{
  "evalId": "A1B2C3_exp2_qwen_B03_White_Male_30s",
  "userId": "firebase-uid",
  "workerId": "A1B2C3D4E5",
  "hitId": 1,
  "isHitMode": true,
  "itemId": "exp2_qwen_B03_White_Male_30s",
  "model": "qwen",
  "promptId": "B03",
  "category": "B",
  "race": "White",
  "gender": "Male",
  "age": "30s",
  "edited_edit_success": 4,
  "edited_skin_tone": 3,
  "edited_race_drift": 1,
  "edited_gender_drift": 1,
  "edited_age_drift": 3,
  "preserved_edit_success": 5,
  "preserved_skin_tone": 3,
  "preserved_race_drift": 1,
  "preserved_gender_drift": 1,
  "preserved_age_drift": 3,
  "duration_ms": 45000,
  "createdAt": "2026-01-19T10:25:00Z"
}
```

### exp2_hit_completions

HIT-level completion tracking.

```json
{
  "workerId": "A1B2C3D4E5",
  "hitId": 1,
  "userId": "firebase-uid",
  "userEmail": "worker@email.com",
  "completionCode": "AMT-H01-A1B2C3-KR5M8X",
  "completedItems": 10,
  "completedAt": "2026-01-19T10:30:00Z"
}
```

---

## Rollout Plan

### Phase 1: Pilot (5 HITs)

1. Create 5 HITs (HITs 1-5)
2. Collect 15 evaluations (5 × 3 workers)
3. Review quality, timing, and feedback
4. Adjust if needed

### Phase 2: Full Launch (45 HITs)

1. Create remaining 45 HITs (HITs 6-50)
2. Monitor completion rate
3. Review and approve/reject submissions
4. Pay bonuses for high-quality work

### Timing

| Phase | Date | HITs | Evaluations |
|-------|------|------|-------------|
| Pilot | Jan 20 | 5 | 15 |
| Full Launch | Jan 21-23 | 45 | 135 |
| **Total** | | **50** | **150** |

---

## Troubleshooting

### Common Issues

1. **Worker sees "HIT Already Completed"**
   - Worker already completed this HIT
   - No action needed, this is expected behavior

2. **Worker cannot login**
   - Ensure Google Auth is enabled
   - Check Firebase authentication settings

3. **Images not loading**
   - Verify image URLs are correct
   - Check Firebase Storage rules

4. **Completion code not generated**
   - Check browser console for errors
   - Verify Firebase Firestore rules allow writes

### Support Contact

For technical issues, contact the research team at [email].

---

*Last Updated: January 18, 2026*
