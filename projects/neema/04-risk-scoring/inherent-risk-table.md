# Neema Platform - Inherent Risk Table
# טבלת סיכון טבוע - פלטפורמת נימה

**Version:** 1.0 (Template)
**Date:** 2024-12-15
**Status:** Template for Population

---

## Purpose / מטרה

This table provides the inherent risk ratings for each risk parameter, with documented justifications. The table will be populated based on Neema's specific platform characteristics and risk appetite.

טבלה זו מספקת את דירוגי הסיכון הטבוע לכל פרמטר סיכון, עם נימוקים מתועדים.

---

## Section 1: PSP-Level Inherent Risk Assessment

### Category A: Geographic Risk (PSP Level)

| Parameter | Description | Risk Score | Weight | Weighted Score | Justification |
|-----------|-------------|------------|--------|----------------|---------------|
| A1 | Source Country FATF Status | [1-4] | 25% | [calc] | [To be documented based on Neema's corridors] |
| A4 | Sanctions Exposure | [1-4] | 25% | [calc] | [To be documented] |
| A5 | CPI Score | [1-4] | 25% | [calc] | [To be documented] |
| A-Other | Basel AML Index | [1-4] | 25% | [calc] | [To be documented] |
| **Category A Total** | | | 100% | **[calc]** | |

**Category A - PSP Geographic Risk: [TBD]/4.0**

---

### Category B: PSP Profile Risk

| Parameter | Description | Risk Score | Weight | Weighted Score | Justification |
|-----------|-------------|------------|--------|----------------|---------------|
| B1 | License Status | [1-4] | 20% | [calc] | [Dependent on PSP licensing regime] |
| B2 | AML Program Maturity | [1-4] | 25% | [calc] | [Based on due diligence assessment] |
| B3 | Ownership Structure | [1-4] | 15% | [calc] | [UBO verification results] |
| B4 | Operational History | [1-4] | 15% | [calc] | [Years in business, track record] |
| B5 | Business Model | [1-4] | 15% | [calc] | [Client base composition] |
| B6 | Nested Relationships | [1-4] | 10% | [calc] | [Sub-agent/downstream PSP use] |
| **Category B Total** | | | 100% | **[calc]** | |

**Category B - PSP Profile Risk: [TBD]/4.0**

---

### Category E: Data Quality Risk (PSP Level)

| Parameter | Description | Risk Score | Weight | Weighted Score | Justification |
|-----------|-------------|------------|--------|----------------|---------------|
| E1 | Travel Rule Compliance | [1-4] | 40% | [calc] | [PSP's compliance with R16 requirements] |
| E2 | Verification Level | [1-4] | 35% | [calc] | [KYC methodology strength] |
| E4 | Documentation | [1-4] | 25% | [calc] | [Quality of onboarding documentation] |
| **Category E Total** | | | 100% | **[calc]** | |

**Category E - Data Quality Risk (PSP): [TBD]/4.0**

---

### PSP-Level Composite Risk Calculation

| Category | Score | Weight | Weighted Score |
|----------|-------|--------|----------------|
| A: Geographic | [X.X] | 20% | [calc] |
| B: PSP Profile | [X.X] | 50% | [calc] |
| E: Data Quality | [X.X] | 30% | [calc] |
| **PSP Inherent Risk** | | 100% | **[X.X]** |

**PSP Risk Tier: [Low/Medium/High/Very High]**

---

## Section 2: Transaction-Level Inherent Risk Assessment

### Category A: Geographic Risk (Transaction Level)

| Parameter | Description | Risk Score | Weight | Weighted Score | Justification |
|-----------|-------------|------------|--------|----------------|---------------|
| A1 | Source Country | [1-4] | 20% | [calc] | [Per transaction origination] |
| A2 | Destination Country | [1-4] | 20% | [calc] | [Per transaction destination] |
| A3 | Corridor Risk | [1-4] | 30% | [calc] | [Combined corridor assessment] |
| A4 | Sanctions Exposure | [1-4] | 30% | [calc] | [Transaction-specific screening] |
| **Category A Total** | | | 100% | **[calc]** | |

**Category A - Transaction Geographic Risk: [TBD]/4.0**

---

### Category C: End-Client Profile Risk

| Parameter | Description | Risk Score | Weight | Weighted Score | Justification |
|-----------|-------------|------------|--------|----------------|---------------|
| C1 | Client Type | [1-4] | 15% | [calc] | [Natural person vs entity] |
| C2 | PEP Status | [1-4] | 25% | [calc] | [PEP screening results] |
| C3 | Adverse Media | [1-4] | 15% | [calc] | [Media screening results] |
| C4 | Sanctions Screening | [1-4] | 25% | [calc] | [Sanctions hit status] |
| C5 | Industry/Occupation | [1-4] | 10% | [calc] | [Risk of stated occupation] |
| C6 | Source of Wealth | [1-4] | 10% | [calc] | [Wealth explanation clarity] |
| **Category C Total** | | | 100% | **[calc]** | |

**Category C - End-Client Risk: [TBD]/4.0**

---

### Category D: Transaction Characteristics

| Parameter | Description | Risk Score | Weight | Weighted Score | Justification |
|-----------|-------------|------------|--------|----------------|---------------|
| D1 | Transaction Value | [1-4] | 25% | [calc] | [Amount-based risk] |
| D2 | Frequency | [1-4] | 20% | [calc] | [Velocity patterns] |
| D3 | Payment Purpose | [1-4] | 20% | [calc] | [Purpose credibility] |
| D4 | Urgency Indicators | [1-4] | 10% | [calc] | [Unusual time pressure] |
| D5 | Round Amounts | [1-4] | 10% | [calc] | [Structuring indicators] |
| D6 | Counterparty Profile | [1-4] | 15% | [calc] | [Recipient risk level] |
| **Category D Total** | | | 100% | **[calc]** | |

**Category D - Transaction Risk: [TBD]/4.0**

---

### Category E: Data Quality Risk (Transaction Level)

| Parameter | Description | Risk Score | Weight | Weighted Score | Justification |
|-----------|-------------|------------|--------|----------------|---------------|
| E1 | Travel Rule Compliance | [1-4] | 50% | [calc] | [Message field completeness] |
| E2 | Verification Level | [1-4] | 25% | [calc] | [Identity verification depth] |
| E3 | Data Consistency | [1-4] | 25% | [calc] | [Cross-reference matching] |
| **Category E Total** | | | 100% | **[calc]** | |

**Category E - Data Quality Risk (Transaction): [TBD]/4.0**

---

### Transaction-Level Composite Risk Calculation

| Category | Score | Weight | Weighted Score |
|----------|-------|--------|----------------|
| A: Geographic | [X.X] | 15% | [calc] |
| C: End-Client | [X.X] | 30% | [calc] |
| D: Transaction | [X.X] | 35% | [calc] |
| E: Data Quality | [X.X] | 20% | [calc] |
| **Transaction Inherent Risk** | | 100% | **[X.X]** |

**Transaction Risk Tier: [Low/Medium/High/Very High]**

---

## Section 3: Combined Risk Assessment

### Final Risk Determination

```
┌─────────────────────────────────────────────────────────────┐
│           COMBINED RISK CALCULATION                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Option A: Maximum Approach                                 │
│  Combined Risk = MAX(PSP Risk, Transaction Risk)            │
│                                                             │
│  Option B: Weighted Approach                                │
│  Combined Risk = (PSP Risk × 40%) + (Transaction Risk × 60%)│
│                                                             │
│  [Selection: TBD based on risk appetite]                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Section 4: Risk Tier Definitions

### 4.1 PSP Risk Tiers

| Tier | Score Range | Description | Onboarding Action |
|------|-------------|-------------|-------------------|
| Low | 1.0 - 1.5 | Well-regulated, established PSP with mature AML program | Standard due diligence |
| Medium | 1.6 - 2.5 | Adequately regulated PSP with acceptable AML controls | Enhanced documentation |
| High | 2.6 - 3.3 | Elevated risk requiring ongoing enhanced monitoring | EDD + senior approval |
| Very High | 3.4 - 4.0 | Significant concerns requiring risk acceptance at board level | Decline or Board approval |

### 4.2 Transaction Risk Tiers

| Tier | Score Range | Description | Processing Action |
|------|-------------|-------------|-------------------|
| Low | 1.0 - 1.5 | Standard transaction, routine processing | Automated approval |
| Medium | 1.6 - 2.5 | Minor risk indicators, enhanced monitoring | Automated + spot checks |
| High | 2.6 - 3.3 | Multiple risk indicators present | Manual review required |
| Very High | 3.4 - 4.0 | Significant ML/TF risk indicators | Hold + escalation |

---

## Section 5: Override Triggers / טריגרים לדריסה

The following conditions automatically override the calculated risk score:

| Trigger Condition | Override Action | Rationale |
|-------------------|-----------------|-----------|
| FATF Black List (A1/A2 = 4) | Minimum HIGH | Regulatory expectation per FATF call for action |
| Confirmed Sanctions Match (C4 = 4) | AUTO DECLINE | Sanctions compliance requirement |
| Unlicensed PSP (B1 = 4) | Minimum HIGH | Regulatory and reputational risk |
| Senior PEP (C2 = 4) | Minimum HIGH | Enhanced scrutiny required per guidance |
| Travel Rule Non-Compliant (E1 = 4) | Minimum MEDIUM | R16 compliance obligation |
| Structuring Pattern (D5 = 4) | Minimum HIGH | Potential criminal offense indicator |

---

## Section 6: Scoring Examples

### Example 1: Low-Risk PSP Profile

| Parameter | Score | Rationale |
|-----------|-------|-----------|
| B1: License Status | 1 | Full license from recognized EU jurisdiction |
| B2: AML Program | 1 | Recent independent audit, no findings |
| B3: Ownership | 1 | Clear UBO structure, verified individuals |
| B4: History | 1 | 8 years operational, no enforcement |
| B5: Business Model | 2 | Mix of retail and SME clients |
| B6: Nesting | 1 | No sub-agents or downstream PSPs |
| **Weighted Average** | **1.15** | **LOW RISK** |

### Example 2: High-Risk Transaction

| Parameter | Score | Rationale |
|-----------|-------|-----------|
| A3: Corridor | 3 | Israel to high-risk jurisdiction |
| C2: PEP Status | 3 | Domestic PEP identified |
| C4: Sanctions | 1 | Clear screening |
| D1: Value | 4 | $75,000 single transaction |
| D3: Purpose | 2 | Commercial payment, documentation provided |
| E1: Travel Rule | 2 | Minor data gaps in beneficiary address |
| **Weighted Average** | **2.7** | **HIGH RISK - Manual Review** |

---

## Section 7: Documentation Requirements

For each populated risk table, document:

1. **Data Source**: Where the information came from
2. **Assessment Date**: When the assessment was performed
3. **Assessor**: Who performed the assessment
4. **Supporting Evidence**: Reference to documentation
5. **Review Cycle**: When reassessment is required

---

## Appendix A: Scoring Quick Reference

```
Score 1 (LOW):      Best case scenario, no concerns identified
Score 2 (MEDIUM):   Minor concerns, manageable with standard controls
Score 3 (HIGH):     Significant concerns, enhanced measures required
Score 4 (VERY HIGH): Severe concerns, may require decline or escalation
```

---

## Appendix B: Weight Allocation Summary

### PSP Level
- Geographic: 20%
- PSP Profile: 50%
- Data Quality: 30%

### Transaction Level
- Geographic: 15%
- End-Client: 30%
- Transaction: 35%
- Data Quality: 20%

---

## Open Items for Completion

- [ ] Populate with Neema-specific corridor data
- [ ] Calibrate thresholds to Neema transaction values
- [ ] Validate weighting with compliance team
- [ ] Create Excel version for operational use
- [ ] Document scoring rationale for each parameter level
- [ ] Test with sample PSP profiles

---

*This template is to be populated during Phase 2.4 of the Neema engagement*
