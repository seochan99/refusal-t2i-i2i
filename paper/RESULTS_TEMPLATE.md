# ACRB Results Template - Easy Data Replacement Guide

This document shows exactly where to update results in `main.tex` after running real experiments.

## 1. Table 2: Refusal Rates by Cultural Attribute (Line 487-508)

**Location**: Section "RQ1: Hard Refusal Disparity Across Cultural Attributes"

```latex
\begin{tabular*}{\columnwidth}{@{\extracolsep{\fill}}lcccccc@{}}
\toprule
\textbf{Model} & \textbf{KR} & \textbf{CN} & \textbf{NG} & \textbf{KE} & \textbf{US} & \textbf{IN} \\
\midrule
GPT Image 1.5     & 4.2  & 3.8  & 12.1 & 10.5 & 2.1 & 5.4  \\  % UPDATE
Imagen 3          & 8.2  & 7.5  & 22.1 & 19.8 & 5.3 & 11.4 \\  % UPDATE
Qwen Image Edit   & 3.5  & 3.1  & 9.8  & 8.7  & 2.0 & 4.2  \\  % UPDATE
FLUX.2 [dev]      & 6.3  & 5.9  & 18.7 & 16.1 & 4.1 & 9.2  \\  % UPDATE
SD 3.5 Large      & 5.8  & 5.4  & 16.9 & 15.2 & 3.8 & 8.9  \\  % UPDATE
Step1X-Edit       & 7.8  & 7.2  & 20.4 & 18.2 & 4.5 & 10.1 \\  % UPDATE
```

**Data Source**:
```python
# After running: python scripts/run_audit.py --mode t2i --all-models
results = pd.read_csv('experiments/refusal_rates_by_culture.csv')
# Extract values for each (model, culture) pair
```

---

## 2. Table 3: Erasure Rates by Attribute Type (Line 512-530)

**Location**: Section "RQ2: Soft Refusal (Cue Erasure) Patterns"

```latex
\begin{tabular*}{\columnwidth}{@{\extracolsep{\fill}}lccccc@{}}
\toprule
\textbf{Attribute} & \textbf{GPT1.5} & \textbf{Img3} & \textbf{Qwen} & \textbf{FLUX2} & \textbf{SD3.5} \\
\midrule
Neutral (baseline) & 3.1  & 5.2  & 2.8  & 4.1  & 3.8  \\  % UPDATE
\midrule
Culture (avg)      & 12.4 & 18.3 & 11.2 & 14.7 & 13.5 \\  % UPDATE
Gender (avg)       & 5.2  & 8.1  & 4.8  & 6.2  & 5.7  \\  % UPDATE
Disability         & 35.6 & 42.1 & 32.4 & 38.5 & 36.8 \\  % UPDATE
Religion           & 18.2 & 25.3 & 16.5 & 21.8 & 19.4 \\  % UPDATE
Age                & 8.4  & 12.4 & 7.2  & 9.8  & 8.9  \\  % UPDATE
```

**Data Source**:
```python
# After running VLM cue retention scoring
erasure_df = pd.read_csv('experiments/erasure_rates_by_attribute.csv')
# For each attribute type, compute: 1.0 - retention_score
```

---

## 3. Table 4: Domain-Specific Disparity (Line 536-556)

**Location**: Section "RQ3: Domain-Specific Disparity Patterns"

```latex
\begin{tabular*}{\columnwidth}{@{\extracolsep{\fill}}lccc@{}}
\toprule
\textbf{Domain} & \textbf{NG (\%)} & \textbf{US (\%)} & \textbf{$\Delta$ (pp)} \\
\midrule
Violence-adjacent  & 21.3 & 3.1 & 18.2 \\  % UPDATE
Unethical/Unsafe   & 24.7 & 8.0 & 16.7 \\  % UPDATE
Substance-related  & 19.4 & 4.2 & 15.2 \\  % UPDATE
Self-harm-adjacent & 18.1 & 3.8 & 14.3 \\  % UPDATE
Religious/Cultural & 14.2 & 2.5 & 11.7 \\  % UPDATE
Privacy-sensitive  & 13.8 & 4.1 & 9.7  \\  % UPDATE
Sexual Wellness    & 12.4 & 3.7 & 8.7  \\  % UPDATE
Copyright Wellness & 10.2 & 4.8 & 5.4  \\  % UPDATE
Body/Appearance    & 7.2  & 3.1 & 4.1  \\  % UPDATE
```

**Data Source**:
```python
# Group by (domain, culture)
domain_df = results.groupby(['domain', 'culture'])['refusal_rate'].mean()
ng_rates = domain_df.xs('Nigerian', level='culture')
us_rates = domain_df.xs('American', level='culture')
delta = ng_rates - us_rates
```

---

## 4. Table 5: T2I vs I2I Modality Comparison (Line 564-585)

**Location**: Section "RQ4: I2I vs. T2I Modality Differences"

```latex
\begin{tabular*}{\columnwidth}{@{\extracolsep{\fill}}lcccc@{}}
\toprule
\textbf{Metric} & \textbf{T2I} & \textbf{I2I} & \textbf{Ratio} & \textbf{$p$-value} \\
\midrule
Hard Refusal (\%)         & 11.3 & 6.8  & 1.66$\times$ & $< 0.001$ \\  % UPDATE
Soft Erasure (\%)         & 24.7 & 31.2 & 0.79$\times$ & $< 0.001$ \\  % UPDATE
Cultural Disparity ($\Delta_R$) & 13.1 & 10.2 & 1.28$\times$ & 0.012     \\  % UPDATE
Disability Erasure ($\Delta_E$) & 32.4 & 38.9 & 0.83$\times$ & 0.004     \\  % UPDATE
\midrule
\multicolumn{5}{l}{\textit{Attribute-specific breakdown}} \\
\midrule
Nigerian (refusal \%)     & 16.7 & 12.4 & 1.35$\times$ & 0.003     \\  % UPDATE
Wheelchair (erasure \%)   & 36.2 & 42.8 & 0.85$\times$ & 0.008     \\  % UPDATE
Hijab (erasure \%)        & 28.4 & 35.7 & 0.80$\times$ & 0.002     \\  % UPDATE
```

**Data Source**:
```python
# Compute t2i metrics
t2i_refusal = t2i_results['refusal_rate'].mean()
i2i_refusal = i2i_results['refusal_rate'].mean()

# P-values from t-test
from scipy.stats import ttest_ind
_, p_refusal = ttest_ind(t2i_results['refusal_rate'], i2i_results['refusal_rate'])
```

---

## 5. Human-VLM Agreement (Line 589-591)

**Location**: Section "Human-VLM Agreement Analysis"

```latex
Human annotators achieved 82.7% agreement with Qwen3-VL retention classifications
(Cohen's $\kappa = 0.74$, substantial agreement), with highest concordance for
disability markers (89.3%) and lowest for subtle cultural attire (76.1%).
```

**Update These Values**:
- Overall agreement: `82.7%` → UPDATE
- Cohen's κ: `0.74` → UPDATE
- Disability agreement: `89.3%` → UPDATE
- Cultural attire agreement: `76.1%` → UPDATE

**Data Source**:
```python
from sklearn.metrics import cohen_kappa_score, accuracy_score
kappa = cohen_kappa_score(human_labels, vlm_labels)
overall_acc = accuracy_score(human_labels, vlm_labels)

# Stratified by attribute type
disability_acc = accuracy_score(
    human_labels[attr_type == 'disability'],
    vlm_labels[attr_type == 'disability']
)
```

---

## 6. Abstract Key Numbers (Line 56-58)

**Location**: Abstract

```latex
Nigerian cultural markers trigger refusal at \textbf{4.6$\times$ the rate} of
American equivalents ($p < 0.001$), while disability-related cues experience
\textbf{45\% higher erasure rates} than neutral baselines
```

**Update These**:
- Nigerian multiplier: `4.6×` = 16.7% / 3.6% → UPDATE
- p-value: `< 0.001` → UPDATE from statistical test
- Disability increase: `45%` = (37.1 - 25.6) / 25.6 → UPDATE
- Human-VLM κ: `0.74` → UPDATE

---

## 7. Introduction Key Stats (Line 70)

**Location**: Introduction, paragraph 4

```latex
Evaluating six state-of-the-art models [...] across 2,400 prompts and 500 grounded
I2I edits, we uncover severe alignment-induced disparities: Nigerian cultural markers
trigger refusal at \textbf{4.6$\times$ the American baseline} (16.7\% vs. 3.6\%,
$p < 0.001$)
```

**Update All Instances of**:
- Nigerian rate: `16.7%` → UPDATE
- American rate: `3.6%` → UPDATE
- Ratio: `4.6×` → RECALCULATE
- Disability erasure: `37.1%` → UPDATE
- Neutral baseline: `25.6%` → UPDATE
- Religious substitution: `28.4%` vs `13.2%` → UPDATE

---

## 8. Discussion Findings Summary (Line 595-605)

**Location**: Section "Key Findings Summary"

```latex
\textbf{Finding 1: Safety Hierarchy Paradox.}
Imagen 3 shows the widest Nigerian-American gap (22.1\% vs. 5.3\%, $\Delta = 16.8$ pp)

\textbf{Finding 2: Universal Disability Erasure.}
All six models exhibit $> 32\%$ erasure rates, with I2I models reaching 42.8%

\textbf{Finding 3: Domain-Attribute Entanglement.}
Nigerian markers in ``Unethical/Unsafe'' contexts trigger 24.7\% refusal vs. 8.0%

\textbf{Finding 4: I2I Sanitization Strategy.}
I2I models exhibit 1.66$\times$ lower hard refusal but 1.26$\times$ higher soft erasure
```

**Update Per Finding**:
1. Imagen 3 gap: `22.1% vs. 5.3%` → UPDATE
2. Min disability erasure: `32%`, I2I max: `42.8%` → UPDATE
3. Domain refusal: `24.7% vs. 8.0%` → UPDATE
4. Modality ratios: `1.66×` and `1.26×` → RECALCULATE

---

## 9. Conclusion (Line 633-635)

**Location**: Conclusion section

```latex
Nigerian cultural markers trigger 4.6$\times$ higher refusal rates than American
equivalents (16.7\% vs. 3.6\%, $p < 0.001$), disability cues experience 45\% higher
silent erasure (37.1\% vs. 25.6%)
```

**Ensure Consistency**: All numbers here should match Abstract and Introduction.

---

## 10. Appendix Summary Table (Line 735-772)

**Location**: Technical Appendix, Table A1

**All values need updating from experimental results.**

---

## Statistical Tests to Run

### 1. T-tests for Disparity Significance
```python
from scipy.stats import ttest_ind

# Cultural disparity
ng_refusals = results[results['culture'] == 'Nigerian']['refusal']
us_refusals = results[results['culture'] == 'American']['refusal']
t_stat, p_value = ttest_ind(ng_refusals, us_refusals)
# Report p-value in tables

# Disability erasure
disability_erasure = results[results['attribute'] == 'disability']['erasure_rate']
neutral_erasure = results[results['attribute'] == 'neutral']['erasure_rate']
t_stat, p_value = ttest_ind(disability_erasure, neutral_erasure)
```

### 2. Cohen's Kappa for Human-VLM Agreement
```python
from sklearn.metrics import cohen_kappa_score

kappa = cohen_kappa_score(human_annotations, vlm_predictions)
# Report in Section "Human-VLM Agreement"
```

### 3. Effect Sizes
```python
from scipy.stats import ttest_ind

def cohens_d(group1, group2):
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
    return (np.mean(group1) - np.mean(group2)) / pooled_std

d = cohens_d(ng_refusals, us_refusals)
# Include in Discussion if d > 0.8 (large effect)
```

---

## Quick Replacement Checklist

After running experiments, replace values in this order:

1. **Table 2** (Refusal rates) - Line 496-501
2. **Table 3** (Erasure rates) - Line 521-527
3. **Table 4** (Domain disparity) - Line 545-553
4. **Table 5** (T2I vs I2I) - Line 573-582
5. **Human eval stats** - Line 591
6. **Abstract** - Line 57
7. **Introduction** - Line 70
8. **RQ1 text** - Line 485
9. **Discussion findings** - Line 599-605
10. **Conclusion** - Line 633

---

## Automated Replacement Script (Future)

```python
# scripts/update_results.py
import re
import pandas as pd

# Load experimental results
refusal_df = pd.read_csv('experiments/refusal_rates.csv')
erasure_df = pd.read_csv('experiments/erasure_rates.csv')
human_eval_df = pd.read_csv('experiments/human_eval.csv')

# Compute key statistics
ng_rate = refusal_df[refusal_df['culture'] == 'Nigerian']['rate'].mean()
us_rate = refusal_df[refusal_df['culture'] == 'American']['rate'].mean()
disparity_ratio = ng_rate / us_rate

# Read LaTeX file
with open('paper/main.tex', 'r') as f:
    latex_content = f.read()

# Replace placeholders
latex_content = re.sub(
    r'Nigerian cultural markers trigger refusal at \\textbf\{[\d.]+\\\$\\times\$',
    f'Nigerian cultural markers trigger refusal at \\textbf{{{disparity_ratio:.1f}\\$\\times\\$',
    latex_content
)

# Write back
with open('paper/main.tex', 'w') as f:
    f.write(latex_content)
```

---

**Last Updated**: 2025-12-30
**Status**: Ready for experimental data insertion
