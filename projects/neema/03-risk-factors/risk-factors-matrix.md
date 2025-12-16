# Neema Platform - Risk Factors Matrix
# מטריצת גורמי סיכון - פלטפורמת נימה

**Version:** 1.0 (Draft)
**Date:** 2024-12-15
**Phase:** 2.3 - Risk Factor Identification

---

## Overview / סקירה כללית

This matrix identifies all risk factors relevant to Neema's B2B2C cross-border payment platform. Risk factors are organized by category and mapped to their assessment level (PSP, Transaction, or Both).

מטריצה זו מזהה את כל גורמי הסיכון הרלוונטיים לפלטפורמת התשלומים הבינלאומיים B2B2C של נימה.

---

## Risk Factor Categories / קטגוריות גורמי סיכון

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NEEMA PLATFORM RISK UNIVERSE                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │  GEOGRAPHIC │  │ PSP PROFILE │  │  END-CLIENT │                 │
│  │    RISK     │  │    RISK     │  │ PROFILE RISK│                 │
│  │   סיכון     │  │   סיכון     │  │   סיכון     │                 │
│  │  גיאוגרפי   │  │ פרופיל PSP  │  │ פרופיל לקוח │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐                                  │
│  │ TRANSACTION │  │ DATA QUALITY│                                  │
│  │    RISK     │  │    RISK     │                                  │
│  │   סיכון     │  │   סיכון     │                                  │
│  │   עסקה      │  │ איכות מידע  │                                  │
│  └─────────────┘  └─────────────┘                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Category A: Geographic Risk / סיכון גיאוגרפי

### A.1 Jurisdiction Risk Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| A1.1 | FATF Rating - Source | דירוג FATF - מקור | FATF mutual evaluation status of originating country | FATF publications | Both |
| A1.2 | FATF Rating - Destination | דירוג FATF - יעד | FATF mutual evaluation status of destination country | FATF publications | Transaction |
| A1.3 | Grey List Status | רשימה אפורה | Jurisdiction under increased monitoring | FATF grey list | Both |
| A1.4 | Black List Status | רשימה שחורה | High-risk jurisdiction - call for action | FATF black list | Both |
| A1.5 | EU High-Risk List | רשימת סיכון EU | EU delegated regulation high-risk third countries | EU publications | Both |

### A.2 Sanctions Risk Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| A2.1 | UN Sanctions | סנקציות או"ם | UN Security Council sanctions regimes | UN website | Both |
| A2.2 | EU Sanctions | סנקציות EU | EU restrictive measures | EU sanctions map | Both |
| A2.3 | US OFAC Sanctions | סנקציות OFAC | US Treasury comprehensive/sectoral sanctions | OFAC lists | Both |
| A2.4 | Israeli Sanctions | סנקציות ישראל | Israel Defense Ministry sanctions | Israeli lists | Both |
| A2.5 | Secondary Sanctions Exposure | חשיפה משנית | Risk of secondary sanctions violation | Analysis | Both |

### A.3 Corruption & Transparency Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| A3.1 | CPI Score | מדד שחיתות | Transparency International CPI | TI annual report | Both |
| A3.2 | Basel AML Index | מדד באזל | Basel Institute AML risk score | Basel Institute | Both |
| A3.3 | Tax Haven Status | מקלט מס | Jurisdiction classification as tax haven | OECD/EU lists | PSP |
| A3.4 | Shell Company Risk | חברות קש | Ease of creating anonymous companies | Analysis | PSP |

### A.4 Corridor-Specific Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| A4.1 | Corridor Volume | נפח מסדרון | Historical ML/TF typology in corridor | FATF typologies | Transaction |
| A4.2 | Informal Value Transfer | העברות בלתי פורמליות | Prevalence of hawala/informal channels | Regional reports | Transaction |
| A4.3 | Currency Controls | בקרת מטבע | Capital/exchange controls in corridor | Central bank data | Transaction |
| A4.4 | Conflict Zone Proximity | קרבה לאזור סכסוך | Proximity to active conflict areas | Geopolitical analysis | Both |

---

## Category B: PSP Profile Risk / סיכון פרופיל PSP

### B.1 Regulatory Status Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| B1.1 | License Type | סוג רישיון | Full license vs registration vs EMI | Regulatory register | PSP |
| B1.2 | Licensing Jurisdiction | תחום שיפוט רישוי | Quality of licensing jurisdiction supervision | Regulatory assessment | PSP |
| B1.3 | Passporting Status | סטטוס פספורטינג | For EU: passported services | Regulatory register | PSP |
| B1.4 | Regulatory History | היסטוריה רגולטורית | Past enforcement, warnings, sanctions | Public records | PSP |
| B1.5 | Pending Actions | הליכים תלויים | Current regulatory investigations | Due diligence | PSP |

### B.2 Ownership & Control Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| B2.1 | UBO Identification | זיהוי בעל שליטה | Ability to identify ultimate beneficial owners | Corporate documents | PSP |
| B2.2 | Ownership Complexity | מורכבות בעלות | Number of layers to UBO | Structure chart | PSP |
| B2.3 | Nominee Structures | מבני נומיני | Use of nominee shareholders/directors | Due diligence | PSP |
| B2.4 | PEP Ownership | בעלות PEP | PEP involvement in ownership/control | Screening | PSP |
| B2.5 | State Ownership | בעלות ממשלתית | Government ownership or control | Corporate documents | PSP |

### B.3 AML Program Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| B3.1 | AML Policy | מדיניות AML | Documented AML/CFT policy | PSP documentation | PSP |
| B3.2 | MLRO Appointment | מינוי MLRO | Designated compliance officer | Organizational info | PSP |
| B3.3 | Independent Audit | ביקורת עצמאית | External AML audit within 2 years | Audit reports | PSP |
| B3.4 | Training Program | תוכנית הדרכה | Staff AML training evidence | Training records | PSP |
| B3.5 | TM System | מערכת ניטור | Transaction monitoring capability | Questionnaire | PSP |
| B3.6 | SAR Filing History | היסטוריית STR | Evidence of SAR/STR filing (proportionate) | Self-declaration | PSP |

### B.4 Business Model Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| B4.1 | Client Base Type | סוג בסיס לקוחות | Retail vs business vs mixed | Business description | PSP |
| B4.2 | High-Risk Sectors | מגזרים בסיכון | Exposure to gambling, crypto, adult, etc. | Business description | PSP |
| B4.3 | Cash Handling | טיפול במזומן | Physical cash operations | Operational info | PSP |
| B4.4 | Agent Network | רשת סוכנים | Use of sub-agents/distributors | Business model | PSP |
| B4.5 | Nested Services | שירותים מקוננים | PSP serving other PSPs/FIs | Due diligence | PSP |
| B4.6 | Geographic Footprint | טביעת רגל גיאוגרפית | Countries of operation | License/registration | PSP |

### B.5 Operational Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| B5.1 | Years in Business | ותק עסקי | Operational history duration | Corporate records | PSP |
| B5.2 | Transaction Volume | נפח עסקאות | Monthly/annual transaction volumes | Business data | PSP |
| B5.3 | Average Transaction Size | גודל עסקה ממוצע | Typical transaction value | Business data | PSP |
| B5.4 | Growth Rate | קצב צמיחה | Unusual growth patterns | Historical data | PSP |
| B5.5 | Banking Relationships | קשרי בנקאות | Quality of banking partners | Due diligence | PSP |

---

## Category C: End-Client Profile Risk / סיכון פרופיל לקוח קצה

*Note: Neema assesses end-client risk indirectly through PSP data and Travel Rule information*

### C.1 Identity Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| C1.1 | Client Type | סוג לקוח | Natural person vs legal entity | Travel Rule data | Transaction |
| C1.2 | Verification Level | רמת אימות | KYC level applied by PSP | PSP data | Transaction |
| C1.3 | Identity Consistency | עקביות זהות | Name/address matching across transactions | Platform data | Transaction |
| C1.4 | New vs Established | חדש vs קיים | First transaction or repeat customer | Platform history | Transaction |

### C.2 PEP & Sanctions Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| C2.1 | PEP Status | סטטוס PEP | Politically exposed person classification | Screening results | Transaction |
| C2.2 | PEP Level | רמת PEP | Head of state vs local official | Screening results | Transaction |
| C2.3 | Sanctions Match | התאמת סנקציות | Match against sanctions lists | Screening results | Transaction |
| C2.4 | Adverse Media | תקשורת שלילית | Negative news coverage | Screening results | Transaction |
| C2.5 | RCA Status | סטטוס RCA | Relative or close associate of PEP | Screening results | Transaction |

### C.3 Source of Funds Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| C3.1 | Stated Purpose | מטרה מוצהרת | Transaction purpose as declared | Payment data | Transaction |
| C3.2 | Purpose Consistency | עקביות מטרה | Purpose matches profile/history | Analysis | Transaction |
| C3.3 | Industry/Occupation | תעסוקה/ענף | Client's stated occupation/business | PSP data | Transaction |
| C3.4 | Source of Wealth | מקור עושר | For high-value: wealth origin | EDD data | Transaction |

---

## Category D: Transaction Characteristics / מאפייני עסקה

### D.1 Value Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| D1.1 | Single Transaction Value | ערך עסקה בודדת | Amount of individual transaction | Transaction data | Transaction |
| D1.2 | Cumulative Value | ערך מצטבר | Total value over period (day/week/month) | Aggregation | Transaction |
| D1.3 | Threshold Proximity | קרבה לסף | Transactions just below reporting thresholds | Analysis | Transaction |
| D1.4 | Round Amount Indicator | סכום עגול | Round number pattern | Transaction data | Transaction |

### D.2 Velocity Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| D2.1 | Transaction Frequency | תדירות | Number of transactions per period | Aggregation | Transaction |
| D2.2 | Velocity Change | שינוי מהירות | Deviation from historical pattern | Historical analysis | Transaction |
| D2.3 | Burst Activity | פעילות פרצים | Multiple transactions in short timeframe | Real-time monitoring | Transaction |
| D2.4 | Time of Transaction | זמן עסקה | Unusual timing patterns | Transaction data | Transaction |

### D.3 Pattern Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| D3.1 | Structuring Indicators | אינדיקציות לפיצול | Pattern suggesting threshold avoidance | Analysis | Transaction |
| D3.2 | Rapid Movement | תנועה מהירה | Quick in-out fund movements | Transaction chain | Transaction |
| D3.3 | Layering Indicators | אינדיקציות לשכבות | Multiple intermediaries without purpose | Analysis | Transaction |
| D3.4 | Counterparty Diversity | גיוון צד נגדי | Many different recipients | Aggregation | Transaction |

### D.4 Payment Type Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| D4.1 | Payment Method | אמצעי תשלום | Bank transfer vs cash vs card | Payment data | Transaction |
| D4.2 | Funding Source Match | התאמת מקור מימון | Consistency of funding method | Historical data | Transaction |
| D4.3 | Urgency Level | רמת דחיפות | Same-day/express payment requests | Service type | Transaction |
| D4.4 | Payment Reference | הפניית תשלום | Quality of payment reference data | Transaction data | Transaction |

---

## Category E: Data Quality Risk / סיכון איכות מידע

### E.1 Travel Rule Compliance Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| E1.1 | Originator Name | שם משלח | Completeness of originator name | Message data | Transaction |
| E1.2 | Originator Account | חשבון משלח | Account number present | Message data | Transaction |
| E1.3 | Originator Address | כתובת משלח | Address or national ID | Message data | Transaction |
| E1.4 | Beneficiary Name | שם מוטב | Completeness of beneficiary name | Message data | Transaction |
| E1.5 | Beneficiary Account | חשבון מוטב | Account number present | Message data | Transaction |
| E1.6 | Ordering Institution | מוסד מזמין | PSP identification complete | Message data | Transaction |
| E1.7 | Beneficiary Institution | מוסד מוטב | Receiving institution identified | Message data | Transaction |

### E.2 Data Verification Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| E2.1 | Identity Verification Method | שיטת אימות זהות | Documentary vs electronic vs none | PSP data | Transaction |
| E2.2 | Document Quality | איכות מסמכים | Quality of supporting documentation | Document review | Both |
| E2.3 | Data Freshness | עדכניות מידע | Age of KYC/KYB data | Timestamps | Both |
| E2.4 | Cross-Reference Validation | אימות צולב | Data validated against external sources | Verification log | Both |

### E.3 Information Consistency Factors

| ID | Risk Factor | Hebrew | Description | Data Source | Assessment Level |
|----|-------------|--------|-------------|-------------|------------------|
| E3.1 | Name Matching | התאמת שם | Name consistency across transactions | Platform data | Transaction |
| E3.2 | Address Consistency | עקביות כתובת | Address matches known data | Platform data | Transaction |
| E3.3 | Profile Consistency | עקביות פרופיל | Transaction pattern matches profile | Historical analysis | Transaction |
| E3.4 | Documentation Consistency | עקביות תיעוד | Documents support stated information | Document review | Both |

---

## Risk Factor Summary Statistics

| Category | Count | PSP-Level | Transaction-Level | Both |
|----------|-------|-----------|-------------------|------|
| A: Geographic | 17 | 2 | 4 | 11 |
| B: PSP Profile | 22 | 22 | 0 | 0 |
| C: End-Client | 13 | 0 | 13 | 0 |
| D: Transaction | 16 | 0 | 16 | 0 |
| E: Data Quality | 15 | 0 | 9 | 6 |
| **Total** | **83** | **24** | **42** | **17** |

---

## Mapping to Scoring Methodology

Each risk factor identified above maps to a scoring parameter in the Risk Scoring Methodology (Phase 2.4):

| Factor Category | Scoring Parameters | Weight Allocation |
|-----------------|-------------------|-------------------|
| A: Geographic | A1-A5 | 15-20% |
| B: PSP Profile | B1-B6 | 50% (PSP level) |
| C: End-Client | C1-C6 | 30% (Transaction level) |
| D: Transaction | D1-D6 | 35% (Transaction level) |
| E: Data Quality | E1-E4 | 20-30% |

---

## Open Items

- [ ] Validate factor completeness with Neema team
- [ ] Confirm data availability for each factor
- [ ] Prioritize factors for MVP implementation
- [ ] Map to existing PSP due diligence questionnaire (if any)
- [ ] Align with Travel Rule message format

---

## Appendix: Factor-to-Typology Mapping

Selected risk factors address specific ML/TF typologies:

| Typology | Relevant Factors |
|----------|------------------|
| Structuring | D1.3, D1.4, D3.1 |
| Trade-Based ML | C3.1, C3.2, D3.2 |
| Shell Companies | A3.4, B2.3, B4.5 |
| PEP Corruption | C2.1-C2.5 |
| Sanctions Evasion | A2.1-A2.5, C2.3 |
| Terrorist Financing | A4.4, C2.3, D2.3 |
| Nested Services | B4.4, B4.5 |

---

*Document prepared by Handle AI for Neema risk assessment engagement*
