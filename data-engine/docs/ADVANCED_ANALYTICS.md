# Advanced Behavioral Analytics Methodology

This document provides complete mathematical and logical documentation for all derived metrics, behavioral insights, and statistical analysis methods used in ContextIQ's advanced analytics layer.

## Design Principles

1. **Mathematical Defensibility**: Every formula has clear mathematical justification
2. **Data Traceability**: Every metric can be traced to raw data tables
3. **No False Significance**: Statistical methods describe patterns without claiming significance
4. **Story-Driven Output**: Analytics follow the pattern: Behaviour → Pattern → Evidence → Risk → Recommendation

---

## Derived Metrics

### 1. Forget Risk Metric

**Purpose**: Estimate probability that a task will be forgotten based on recent behavioral patterns.

**Formula**:
```
forget_risk = 0.4 × recent_forgetting_rate 
           + 0.3 × interruption_density
           + 0.2 × context_switch_frequency
           + 0.1 × deadline_pressure_ratio
```

**Component Definitions**:
- `recent_forgetting_rate` = forgotten_tasks / total_resolved_tasks (last 7 days)
- `interruption_density` = total_interruptions / active_hours
- `context_switch_frequency` = context_switches / sessions
- `deadline_pressure_ratio` = tasks_with_near_deadline / total_active_tasks

**Normalization**:
- `recent_forgetting_rate` scaled by 2× (typical rates are low)
- `interruption_density` normalized to 6/hr saturation
- `context_switch_frequency` normalized to 3/session saturation
- `deadline_pressure_ratio` already 0-1 range

**Interpretation**: 0-1 scale, higher = higher risk of forgetting

**Traceability**: Computed from `tasks`, `sessions`, `interruptions` tables

---

### 2. Context Switch Rate

**Purpose**: Measure frequency of context switches per unit time.

**Formula**:
```
context_switch_rate = total_context_switches / total_active_time_hours
```

**Interpretation**: switches per hour, higher = more fragmented attention

**Traceability**: Computed from `context_sessions.context_switch_count` and `focused_time_seconds + interruption_time_seconds`

---

### 3. Interruption Rate

**Purpose**: Measure frequency of interruptions per unit active time.

**Formula**:
```
interruption_rate = total_interruptions / total_active_time_hours
```

**Interpretation**: interruptions per hour, higher = more disrupted work

**Traceability**: Computed from `interruptions` table and `context_sessions` time data

---

### 4. Recovery Time

**Purpose**: Measure average time to return to a paused task.

**Formula**:
```
recovery_time = mean(resume_delay_seconds) for sessions with resume_delay
```

**Interpretation**: seconds, higher = slower recovery from interruptions

**Traceability**: Computed from `context_sessions.resume_delay_seconds`

---

### 5. Behavioral Friction Score

**Purpose**: Composite measure of workflow disruption.

**Formula**:
```
friction_score = 0.35 × forgetting_component
              + 0.25 × interruption_component
              + 0.20 × context_switch_component
              + 0.20 × recovery_component
```

**Component Normalization** (each 0-100):
- `forgetting_component` = min(100, forgetting_rate × 200)
- `interruption_component` = min(100, (interruption_rate / 8) × 100)
- `context_switch_component` = min(100, (switches_per_session / 4) × 100)
- `recovery_component` = min(100, (avg_recovery_minutes / 45) × 100)

**Interpretation**: 0-100 scale, higher = more behavioral friction

**Traceability**: Computed from `tasks`, `sessions`, `interruptions` tables

---

### 6. Completion Reliability

**Purpose**: Measure consistency of task completion over time.

**Formula**:
```
completion_reliability = 1 - (std(completion_rate_by_day) / mean(completion_rate_by_day))
```

Where `completion_rate_by_day` = completed_tasks / total_tasks per day

**Interpretation**: 0-1 scale, higher = more consistent completion patterns

**Traceability**: Computed from `tasks.status` and `tasks.created_at/completed_at`

---

### 7. Context Consistency

**Purpose**: Measure how consistently tasks are performed in their typical contexts.

**Formula**:
```
context_consistency = mean(category_location_match_rate)
```

Where `category_location_match_rate` = (most_common_location_count / total_category_tasks)

**Interpretation**: 0-1 scale, higher = more consistent context-task associations

**Traceability**: Computed from `tasks.category` and `tasks.location_id`

---

### 8. Repetition Strength

**Purpose**: Measure how strongly task patterns repeat over time.

**Formula**:
```
repetition_strength = mean(temporal_correlation_by_category)
```

Where `temporal_correlation` = autocorrelation of task creation frequency at 7-day lag

**Interpretation**: 0-1 scale, higher = stronger repeating patterns

**Traceability**: Computed from `tasks.category` and `tasks.created_at`

---

### 9. Time Lost to Interruptions

**Purpose**: Quantify total time lost due to interruptions.

**Formula**:
```
time_lost_hours = interruption_hours + (context_switches × recovery_overhead)
```

Where `recovery_overhead` = 5 minutes per switch (based on cognitive research)

**Interpretation**: hours, higher = more time lost to disruptions

**Traceability**: Computed from `interruptions.duration_seconds` and `sessions.context_switch_count`

---

## Behavioral Insights

### Insight Generation Pattern

Each insight follows the structure:
1. **Behaviour**: What behavioral pattern is being analyzed?
2. **Pattern**: What statistical patterns emerge from the data?
3. **Evidence**: What data supports the pattern?
4. **Risk**: What are the implications?
5. **Recommendation**: What action should be taken?

### 10 Key Questions Answered

1. **When am I most likely to forget tasks?**
   - Analyzes forgetting rates by weekday and hour
   - Identifies time periods with significantly elevated forgetting rates
   - Compares to overall baseline to identify high-risk periods

2. **Which contexts are associated with forgetting?**
   - Analyzes forgetting rates by category and location
   - Statistical comparison against overall forgetting rate
   - Identifies contexts with >30% elevated risk

3. **Which task categories generate the most friction?**
   - Measures composite friction score per category
   - Combines forgetting rate, interruption density, and switch rate
   - Identifies categories with above-average friction

4. **When do context switches happen most frequently?**
   - Analyzes context switch distribution by time
   - Computes switches per session by weekday and hour
   - Identifies peak switching periods

5. **How much time is lost to interruptions?**
   - Quantifies direct interruption time
   - Estimates cognitive switching overhead (5 min/switch)
   - Calculates as percentage of active time

6. **Which recurring task patterns are associated with delays?**
   - Analyzes delay rates by category and priority
   - Identifies patterns with >30% elevated delay rates
   - Focuses on recurring problematic patterns

7. **Which locations/contexts are strongly associated with particular tasks?**
   - Measures association strength between locations and categories
   - Uses normalized mutual information approximation
   - Identifies strong and weak associations

8. **What time periods show the highest cognitive friction?**
   - Computes composite friction by time period
   - Combines switches, interruptions, and active time
   - Identifies high-friction periods for scheduling

9. **Which behaviours are improving or worsening over time?**
   - Computes linear regression trends for key metrics
   - Analyzes forgetting rate trends over time
   - Provides trend direction and confidence

10. **Which tasks should receive proactive attention?**
    - Multi-factor risk assessment for active tasks
    - Combines priority, deadline urgency, and category risk
    - Identifies tasks with >50% composite risk score

---

## Statistical Analysis

### Distribution Statistics

**Purpose**: Describe the distribution of numerical metrics.

**Computed Statistics**:
- Mean, median, standard deviation
- Min, max, quartiles (Q25, Q75)
- Interquartile range (IQR)

**Sample Size Confidence**:
- HIGH: n ≥ 30
- MEDIUM: 10 ≤ n < 30
- LOW: n < 10

**No Significance Claims**: Only descriptive statistics provided.

---

### Correlation Analysis

**Purpose**: Measure relationships between behavioral metrics.

**Method**: Pearson correlation coefficient

**Formula**:
```
r = Σ((x - x̄)(y - ȳ)) / √(Σ(x - x̄)² Σ(y - ȳ)²)
```

**Sample Size Confidence**:
- HIGH: n ≥ 50
- MEDIUM: 20 ≤ n < 50
- LOW: n < 20

**No Significance Claims**: Correlation values reported without p-values.

---

### Trend Analysis

**Purpose**: Identify directional changes in metrics over time.

**Method**: Linear regression

**Formula**:
```
y = mx + b
```

Where:
- `m` = slope (trend direction)
- `b` = intercept
- `r²` = coefficient of determination

**Trend Direction**:
- INCREASING: slope > 0.00001
- DECREASING: slope < -0.00001
- STABLE: |slope| ≤ 0.00001

**Confidence Assessment**:
- HIGH: n ≥ 20 and r² > 0.3
- MEDIUM: n ≥ 10 and r² > 0.1
- LOW: otherwise

**No Significance Claims**: Trend direction and fit quality reported without statistical tests.

---

### Distribution Comparison

**Purpose**: Compare distributions between groups.

**Computed Metrics**:
- Mean and median differences
- Cohen's d effect size

**Cohen's d Formula**:
```
d = (μ₁ - μ₂) / σ_pooled
```

Where `σ_pooled = √((σ₁² + σ₂²) / 2)`

**Effect Size Interpretation** (conventional thresholds):
- NEGLIGIBLE: |d| < 0.2
- SMALL: 0.2 ≤ |d| < 0.5
- MEDIUM: 0.5 ≤ |d| < 0.8
- LARGE: |d| ≥ 0.8

**No Significance Claims**: Only descriptive comparison provided.

---

### Outlier Detection

**Purpose**: Identify extreme values in distributions.

**Methods**:
1. **IQR Method**: Values outside Q1 - 1.5×IQR or Q3 + 1.5×IQR
2. **Z-Score Method**: Values with |z| > threshold

**IQR Formula**:
```
lower_bound = Q1 - 1.5 × IQR
upper_bound = Q3 + 1.5 × IQR
```

**Z-Score Formula**:
```
z = (x - μ) / σ
```

---

### Category Association

**Purpose**: Measure association between categorical variables.

**Method**: Cramer's V approximation

**Formula**:
```
V = √(χ² / (n × min(r-1, c-1)))
```

Where χ² is computed from contingency table.

**Association Strength**:
- NEGLIGIBLE: V < 0.1
- WEAK: 0.1 ≤ V < 0.3
- MODERATE: 0.3 ≤ V < 0.5
- STRONG: V ≥ 0.5

**No Significance Claims**: Only descriptive association reported.

---

## API Endpoints

### Enhanced Analytics Endpoints

1. **GET /analytics/derived-metrics**
   - Returns all derived metrics
   - Parameters: `user_id`, `period_days`
   - Response: Forget risk, friction scores, reliability, etc.

2. **GET /analytics/insights**
   - Returns all behavioral insights
   - Parameters: `user_id`, `period_days`
   - Response: 10 insights answering key questions

3. **GET /analytics/trends/{metric_name}**
   - Returns trend analysis for specific metric
   - Parameters: `user_id`, `period_days`, `metric_name`
   - Response: Slope, r², direction, confidence

4. **GET /analytics/distributions/{metric_name}**
   - Returns distribution statistics
   - Parameters: `user_id`, `period_days`, `metric_name`
   - Response: Mean, median, std, quartiles, confidence

5. **GET /analytics/correlations**
   - Returns correlation matrix
   - Parameters: `user_id`, `period_days`
   - Response: Correlations, sample size, confidence

6. **GET /analytics/story**
   - Returns narrative-driven analytics
   - Parameters: `user_id`, `period_days`
   - Response: Narrative, behaviors, patterns, risks, recommendations

---

## Data Traceability

Every metric and insight includes traceability information:

- **Source Tables**: Which database tables are used
- **Sample Size**: Number of data points used
- **Time Period**: Date range of analysis
- **Confidence Indicators**: Sample size confidence levels
- **Component Breakdown**: How composite metrics are calculated

---

## Ethical Considerations

1. **No Diagnostic Claims**: Analytics describe behavior patterns, not psychological diagnoses
2. **Correlation ≠ Causation**: All insights describe associations, not causal relationships
3. **Privacy**: All analytics are computed per-user with no cross-user comparisons
4. **Transparency**: All formulas and methods are documented
5. **User Control**: Users can adjust analysis periods and opt-out of insights

---

## Limitations

1. **Sample Size**: Metrics with low sample size confidence should be interpreted cautiously
2. **Synthetic Data**: Current evaluation uses synthetic data; real-world patterns may differ
3. **Temporal Bias**: Recent behavior may not represent long-term patterns
4. **Context Dependence**: Metrics are relative to individual baselines, not absolute standards
5. **Cultural Factors**: Behavioral patterns may vary across cultural contexts

---

## Future Enhancements

1. **Personalized Baselines**: Learn individual behavioral baselines over time
2. **Predictive Analytics**: Forecast future behavioral patterns
3. **Comparative Analysis**: Anonymous benchmarking against similar users
4. **Intervention Testing**: A/B test behavioral recommendations
5. **Multimodal Data**: Incorporate additional data sources (calendar, communication patterns)
