# ContextIQ — Task Risk Predictions & Recommendations Architecture

This guide explains the design, algorithms, cognitive psychology principles, and data pipelines powering **Task Risk Predictions** and **Contextual Recommendations** in ContextIQ.

---

## 1. Task Risk Predictions (`/predictions`)

### Core Objective
The Prediction Engine estimates the statistical probability that an active pending task will slip from working memory before completion:

$$\mathbf{P}(\text{Task Forgotten} \mid \mathbf{X})$$

Where $\mathbf{X}$ is the feature vector of historical user telemetry, task properties, and current cognitive context.

### Scientific Foundation: The Ebbinghaus Forgetting Curve
Working memory retention ($R$) decays exponentially as a function of elapsed time ($t$) and memory stability ($S$):

$$R = e^{-\frac{t}{S}}$$

ContextIQ models the stability factor $S$ using:
1. **Cognitive Anchor Status**: Tasks flagged as everyday slip points (e.g. *switching off appliances*, *carrying keys*) have low baseline stability under context switching.
2. **Habit Interference**: Routine physical chores (e.g. *vessel washing*, *laundry*) compete with high-salience cognitive work.
3. **Resumption Lag**: High friction from distraction triggers (e.g. *social media reels loops*, *meeting hops*) rapidly degrades working memory anchors.

### Risk Stratification & Explanations (SHAP Attribution)
Every prediction card provides **Model Reasoning** explaining the mathematical factors:

| Risk Level | Score Range | Contributing Features (SHAP Reasons) | Primary Recommended Action |
| :--- | :--- | :--- | :--- |
| **HIGH** | 70% – 100% | • Memory Anchor Flag (+42% impact)<br>• Time-decay since creation (+28%)<br>• Micro-delay disruption (+14%) | Immediate proactive notification & pinned top-of-board |
| **MEDIUM** | 40% – 69% | • Routine Habit Cadence (+30%)<br>• Time-of-day window shift (+28%) | Scheduled habit block before deep focus |
| **LOW** | 0% – 39% | • Explicit Focus Priority (-35%)<br>• Planned work sprint (-20%) | Standard tracking in focus queue |

---

## 2. Contextual Recommendations ("One More Thing" Engine)

### Core Objective
Inspired by real-world human habits, the **Recommendation Engine** (`/recommendations`) detects transition moments (e.g. stepping away from a desk, ending a lecture, concluding a coding sprint) and recommends the exact micro-action needed before leaving.

### Association Mining & Pattern Detection
The engine evaluates associations between:
- **Location Context**: e.g., Tech Campus Desk $\rightarrow$ "Push uncommitted Git branch".
- **Temporal Anchor**: e.g., Leaving home in the morning $\rightarrow$ "Check geyser / appliances".
- **Chore Cadence**: e.g., Post-dinner transition $\rightarrow$ "Vessel washing / Dishwashing".

### User Feedback Loop (Self-Calibrating ML)
Recommendations present two explicit actions:
- **Accept ("Add to tasks")**: Immediately converts the recommendation into an active task in PostgreSQL with pre-filled tags and priority. Increments acceptance confidence for that context.
- **Dismiss**: Suppresses future prompts for that pattern during similar context windows.

Feedback is persisted in PostgreSQL (`recommendation_feedback` table) with timestamps, context tags, and action outcomes.

---

## 3. PostgreSQL Database Schema

```sql
-- Predictions Table
CREATE TABLE predictions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    prediction_type VARCHAR(64) NOT NULL, -- 'FORGET_RISK'
    predicted_value JSONB NOT NULL,       -- reasons, taskTitle, risk_level
    confidence FLOAT NOT NULL,            -- 0.0 to 1.0
    model_version VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recommendations Table
CREATE TABLE recommendations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    recommendation_type VARCHAR(64) NOT NULL, -- 'ONE_MORE_THING'
    associated_task VARCHAR(255) NOT NULL,
    association_confidence FLOAT NOT NULL,
    triggering_behaviour TEXT,
    evidence JSONB,
    status VARCHAR(32) DEFAULT 'PROPOSED',
    priority INT DEFAULT 5,
    explanation TEXT,
    expected_benefit TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. Summary of User Value
- **Zero Blank Pages**: Predictions and recommendations populate directly from the user's signup questionnaire and active tasks.
- **Explainable AI**: Never shows arbitrary risk scores without giving concrete, plain-English reasons.
- **Actionable**: Every recommendation is one click away from becoming an active, tracked task.
