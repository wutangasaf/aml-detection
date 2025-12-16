# Neema Platform - Risk Scoring Methodology
# מתודולוגית דירוג סיכונים - פלטפורמת נימה

**Version:** 1.0 (Draft)
**Date:** 2024-12-15
**Status:** Framework Setup

---

## 1. Executive Summary / תקציר מנהלים

This document establishes the risk scoring methodology for Neema's B2B2C cross-border payment platform. The methodology addresses the unique characteristics of a platform that serves Payment Service Providers (PSPs) who in turn serve end-clients.

מסמך זה מגדיר את מתודולוגיית דירוג הסיכונים עבור פלטפורמת התשלומים הבינלאומיים B2B2C של נימה. המתודולוגיה מתייחסת למאפיינים הייחודיים של פלטפורמה המשרתת ספקי שירותי תשלום (PSPs) אשר בתורם משרתים לקוחות קצה.

---

## 2. Scoring Framework Overview / סקירת מסגרת הדירוג

### 2.1 Risk Assessment Levels / רמות הערכת סיכון

The platform requires risk assessment at **three distinct levels**:

```
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 1: PSP RISK (Inherent + Controls = Residual*)       │
│  סיכון ספק שירותי תשלום                                     │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 2: TRANSACTION RISK                                  │
│  סיכון עסקה                                                 │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 3: END-CLIENT RISK (Indirect/Inherited)             │
│  סיכון לקוח קצה (עקיף/מורש)                                 │
└─────────────────────────────────────────────────────────────┘

* Residual risk analysis out of scope per engagement
```

### 2.2 Scoring Scale / סולם דירוג

| Score | Risk Level | Hebrew | Color Code |
|-------|------------|--------|------------|
| 1 | Low | נמוך | Green |
| 2 | Medium | בינוני | Yellow |
| 3 | High | גבוה | Orange |
| 4 | Very High | גבוה מאוד | Red |

---

## 3. Risk Categories / קטגוריות סיכון

### 3.1 Category Overview

| # | Category | Hebrew | Weight* | Applies To |
|---|----------|--------|---------|------------|
| A | Geographic Risk | סיכון גיאוגרפי | TBD | PSP + Transaction |
| B | PSP Profile Risk | סיכון פרופיל PSP | TBD | PSP |
| C | End-Client Profile Risk | סיכון פרופיל לקוח קצה | TBD | Transaction |
| D | Transaction Characteristics | מאפייני עסקה | TBD | Transaction |
| E | Data Quality Risk | סיכון איכות מידע | TBD | PSP + Transaction |

*Weights to be determined in Phase 2.4

---

## 4. Risk Factor Parameters / פרמטרי גורמי סיכון

### 4.1 Category A: Geographic Risk / סיכון גיאוגרפי

| Parameter | Description | Score 1 | Score 2 | Score 3 | Score 4 |
|-----------|-------------|---------|---------|---------|---------|
| A1: Source Country | FATF status of originating jurisdiction | FATF member, no deficiencies | FATF member with minor deficiencies | Grey list | Black list / High-risk |
| A2: Destination Country | FATF status of destination jurisdiction | FATF member, no deficiencies | FATF member with minor deficiencies | Grey list | Black list / High-risk |
| A3: Corridor Risk | Combined source-destination risk | Both low risk | Mixed risk levels | One high-risk end | Both high risk |
| A4: Sanctions Exposure | Proximity to sanctioned territories | No exposure | Neighboring countries | Partial sanctions | Comprehensive sanctions |
| A5: CPI Score | Corruption Perception Index | >70 | 50-70 | 30-50 | <30 |

### 4.2 Category B: PSP Profile Risk / סיכון פרופיל PSP

| Parameter | Description | Score 1 | Score 2 | Score 3 | Score 4 |
|-----------|-------------|---------|---------|---------|---------|
| B1: License Status | Regulatory authorization | Full license in recognized jurisdiction | Registration-based regime | Pending/provisional | Unlicensed/unregulated |
| B2: AML Program Maturity | PSP's AML/CFT controls | Established program, independent audit | Basic program in place | Developing program | No formal program |
| B3: Ownership Structure | Transparency of UBO | Clear, verified UBOs | Complex but verifiable | Nominee structures | Opaque/unverifiable |
| B4: Operational History | Track record | >5 years, no enforcement | 2-5 years, clean | <2 years or minor issues | Enforcement actions |
| B5: Business Model | PSP's client base | Retail consumers only | Mix retail/SME | High-risk sectors present | Predominantly high-risk |
| B6: Nested Relationships | Sub-agents/downstream PSPs | None | Limited, disclosed | Multiple layers | Undisclosed nesting |

### 4.3 Category C: End-Client Profile Risk / סיכון פרופיל לקוח קצה

| Parameter | Description | Score 1 | Score 2 | Score 3 | Score 4 |
|-----------|-------------|---------|---------|---------|---------|
| C1: Client Type | Nature of end-client | Natural person, verified | Legal entity, standard | Complex structure | Anonymous/bearer |
| C2: PEP Status | Political exposure | No PEP connection | Family/associate of PEP | Domestic PEP | Foreign/International PEP |
| C3: Adverse Media | Negative news | None identified | Historical, resolved | Current, non-financial | Current financial crime |
| C4: Sanctions Screening | Screening results | Clear | Potential match, cleared | Close match, monitoring | Confirmed match |
| C5: Industry/Occupation | Source of funds risk | Low-risk employment | Standard business | Cash-intensive | High-risk (gambling, crypto, etc.) |
| C6: Source of Wealth | Wealth origin clarity | Clear, documented | Reasonable explanation | Partially documented | Unexplained/inconsistent |

### 4.4 Category D: Transaction Characteristics / מאפייני עסקה

| Parameter | Description | Score 1 | Score 2 | Score 3 | Score 4 |
|-----------|-------------|---------|---------|---------|---------|
| D1: Transaction Value | Single transaction amount | <$1,000 | $1,000-$10,000 | $10,000-$50,000 | >$50,000 |
| D2: Frequency | Transaction velocity | Occasional (<5/month) | Regular (5-20/month) | Frequent (20-50/month) | Very frequent (>50/month) |
| D3: Payment Purpose | Stated purpose | Family support | Commercial payment | Investment | Unclear/inconsistent |
| D4: Urgency Indicators | Time pressure | Normal processing | Same-day request | Urgent/immediate | Emergency with pressure |
| D5: Round Amounts | Structuring indicators | Varied amounts | Occasional round | Frequent round | Pattern of just-under threshold |
| D6: Counterparty Profile | Recipient risk | Known, verified | New but verifiable | Limited information | Anonymous/unknown |

### 4.5 Category E: Data Quality Risk / סיכון איכות מידע

| Parameter | Description | Score 1 | Score 2 | Score 3 | Score 4 |
|-----------|-------------|---------|---------|---------|---------|
| E1: Travel Rule Compliance | Data completeness | Full originator & beneficiary data | Minor gaps, obtainable | Significant gaps | Non-compliant |
| E2: Verification Level | Identity verification strength | Documentary + biometric | Documentary only | Self-declared | Unverified |
| E3: Data Consistency | Cross-reference matching | Full match across sources | Minor discrepancies | Inconsistencies present | Conflicting information |
| E4: Documentation | Supporting documents | Complete file | Key documents present | Partial documentation | No documentation |

---

## 5. Weighting Model / מודל משקלות

### 5.1 Category Weights (Proposed)

```
PSP-Level Risk Assessment:
├── Geographic (A):     20%
├── PSP Profile (B):    50%
└── Data Quality (E):   30%
                       ───
                       100%

Transaction-Level Risk Assessment:
├── Geographic (A):     15%
├── End-Client (C):     30%
├── Transaction (D):    35%
└── Data Quality (E):   20%
                       ───
                       100%
```

### 5.2 Weight Justification

| Category | Weight Rationale |
|----------|------------------|
| Geographic | Standard AML risk factor, elevated for cross-border |
| PSP Profile | Primary relationship for Neema, controls quality critical |
| End-Client | Inherited risk through B2B2C model |
| Transaction | Core activity risk |
| Data Quality | Essential for Travel Rule and monitoring capability |

---

## 6. Aggregation Formula / נוסחת צבירה

### 6.1 Weighted Average Method

```
Risk Score = Σ (Category Score × Category Weight)

Where:
- Category Score = Σ (Parameter Score × Parameter Weight within Category) / n
- Final Score rounded to nearest 0.5
```

### 6.2 Risk Tier Thresholds

| Calculated Score | Risk Tier | Hebrew |
|------------------|-----------|--------|
| 1.0 - 1.5 | Low Risk | סיכון נמוך |
| 1.6 - 2.5 | Medium Risk | סיכון בינוני |
| 2.6 - 3.3 | High Risk | סיכון גבוה |
| 3.4 - 4.0 | Very High Risk | סיכון גבוה מאוד |

### 6.3 Override Triggers / טריגרים לדריסה

Certain parameters automatically escalate the overall risk regardless of calculated score:

| Trigger | Automatic Escalation |
|---------|---------------------|
| FATF Black List jurisdiction | Minimum High Risk |
| Confirmed sanctions match | Automatic Decline |
| Unlicensed PSP | Minimum High Risk |
| PEP - Head of State/Government | Minimum High Risk |
| Travel Rule non-compliance | Minimum Medium Risk |

---

## 7. Scoring Process / תהליך הדירוג

### 7.1 PSP Onboarding Assessment

```
1. Collect PSP documentation
2. Score each parameter in Categories A, B, E
3. Calculate weighted average
4. Apply override triggers
5. Determine PSP risk tier
6. Document rationale
7. Approval based on risk appetite matrix (Phase 2.5)
```

### 7.2 Transaction Assessment

```
1. Inherit PSP baseline risk
2. Score transaction-specific parameters (A, C, D, E)
3. Calculate transaction risk score
4. Combine with PSP risk (max or weighted)
5. Apply override triggers
6. Route based on decision matrix (Phase 2.5)
```

---

## 8. Calibration & Validation / כיול ואימות

### 8.1 Initial Calibration

- [ ] Review with Neema compliance team
- [ ] Test on sample PSP portfolio (if available)
- [ ] Adjust thresholds based on risk appetite
- [ ] Document calibration decisions

### 8.2 Ongoing Validation

*Note: Implementation procedures out of scope, but methodology should support:*
- Annual methodology review
- Threshold adjustment based on performance
- Regulatory change incorporation

---

## 9. Appendices

### Appendix A: FATF Lists Reference

**Grey List (as of latest update):**
- Check current FATF website for jurisdictions under increased monitoring

**Black List (High-Risk Jurisdictions):**
- Check current FATF website for call for action jurisdictions

### Appendix B: Regulatory Basis

| Requirement | Source |
|-------------|--------|
| Risk-based approach | FATF Recommendation 1 |
| Correspondent banking DD | FATF Recommendation 13 |
| Wire transfer rules | FATF Recommendation 16 (Travel Rule) |
| PSP oversight | EU AMLD6 / Dutch Wwft |
| Israeli requirements | צו איסור הלבנת הון (חברות תשלום) |

### Appendix C: Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-15 | Handle AI | Initial framework setup |

---

## 10. Open Items for Phase 2.4 Completion

- [ ] Validate risk parameters with Neema
- [ ] Confirm weight allocations
- [ ] Finalize threshold values (especially transaction amounts)
- [ ] Build Inherent Risk Table (Excel deliverable)
- [ ] Write detailed justifications for each score level
- [ ] Translate key sections to Hebrew per client preference

---

*This document is a draft for client review. All ratings and thresholds subject to calibration based on Neema's specific risk appetite and operational requirements.*
