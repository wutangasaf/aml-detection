"""
Profile Reverse-Engineering Generator ("Sherlock Holmes" Script)

This script analyzes transaction behavior and generates synthetic customer profiles
that are COHERENT with the observed financial activity.

The key insight: Generate profiles from CLEAN transactions only, so that
LAUNDERING transactions naturally break the narrative.
"""

import os
import json
import certifi
from datetime import datetime
from pymongo import MongoClient
from openai import OpenAI
import random

# ============================================================
# CONFIGURATION
# ============================================================

MONGODB_URI = "mongodb+srv://dev_db_user:EyMpA37VXGa3Kjmc@aml-research.sgpnzv8.mongodb.net/?appName=AML-Research"
DATABASE_NAME = "aml_db"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Sample size for initial testing
CLEAN_ACCOUNTS_SAMPLE = 50
LAUNDERING_ACCOUNTS_SAMPLE = 50

# ============================================================
# PROFILE GENERATION PROMPT
# ============================================================

SHERLOCK_PROMPT = """You are a financial analyst reconstructing a customer profile based solely on their transaction history.

TRANSACTION HISTORY (last {txn_count} transactions):
{transactions}

BEHAVIORAL STATISTICS:
- Average transaction amount: {avg_amount}
- Transaction frequency: {frequency} per month
- Typical payment methods: {payment_methods}
- Domestic vs International: {domestic_pct}% domestic
- Unique counterparties: {unique_counterparties}
- Active time pattern: {time_pattern}

Based ONLY on this financial behavior, deduce the most likely customer profile.

You must output valid JSON with this exact structure:
{{
    "customer_type": "individual" or "business",
    "subtype": "specific type (e.g., 'small_business', 'salaried_employee', 'freelancer', 'corporation')",
    "likely_occupation_or_industry": "best guess based on patterns",
    "estimated_monthly_income_or_revenue": "range in same currency as transactions",
    "account_purpose": "what this account is primarily used for",
    "expected_transaction_range": "typical min-max transaction amounts",
    "expected_counterparty_types": "who they typically transact with",
    "risk_indicators": ["list any yellow flags even in normal behavior"],
    "narrative_summary": "2-3 sentence story explaining who this customer likely is and why their transactions make sense"
}}

Be specific and grounded in the data. Do not invent details not supported by the transactions.
Output ONLY the JSON, no other text.
"""

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_mongo_client():
    """Connect to MongoDB Atlas."""
    return MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=30000,
        tlsCAFile=certifi.where()
    )

def get_openai_client():
    """Get OpenAI client."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=OPENAI_API_KEY)

def analyze_transactions(transactions: list) -> dict:
    """Compute behavioral statistics from transaction list."""
    if not transactions:
        return {}

    # Extract amounts from nested structure
    amounts = []
    for t in transactions:
        amt = t.get("amount", {})
        if isinstance(amt, dict):
            amounts.append(amt.get("sent", 0) or amt.get("received", 0))
        else:
            amounts.append(amt or 0)

    # Payment methods distribution
    payment_methods = {}
    for t in transactions:
        method = t.get("payment_format", "Unknown")
        payment_methods[method] = payment_methods.get(method, 0) + 1

    # Sort by frequency
    payment_methods = dict(sorted(payment_methods.items(), key=lambda x: -x[1]))

    # Counterparties (from nested receiver structure)
    counterparties = set()
    for t in transactions:
        receiver = t.get("receiver", {})
        if isinstance(receiver, dict):
            counterparties.add(receiver.get("account_id", ""))
            counterparties.add(receiver.get("bank_id", ""))

    # Time span
    timestamps = [t.get("timestamp") for t in transactions if t.get("timestamp")]
    if timestamps:
        try:
            dates = []
            for ts in timestamps:
                if isinstance(ts, datetime):
                    dates.append(ts)
                elif isinstance(ts, str):
                    dates.append(datetime.strptime(ts.split()[0], "%Y-%m-%d"))
            if len(dates) >= 2:
                days_span = (max(dates) - min(dates)).days or 1
                frequency = len(transactions) / (days_span / 30)
            else:
                frequency = len(transactions)
        except:
            frequency = len(transactions)
    else:
        frequency = len(transactions)

    # Domestic vs international (simplified - same bank = domestic)
    domestic_count = 0
    for t in transactions:
        sender = t.get("sender", {})
        receiver = t.get("receiver", {})
        if isinstance(sender, dict) and isinstance(receiver, dict):
            if sender.get("bank_id") == receiver.get("bank_id"):
                domestic_count += 1
    domestic_pct = (domestic_count / len(transactions) * 100) if transactions else 0

    return {
        "avg_amount": sum(amounts) / len(amounts) if amounts else 0,
        "min_amount": min(amounts) if amounts else 0,
        "max_amount": max(amounts) if amounts else 0,
        "frequency": round(frequency, 1),
        "payment_methods": ", ".join([f"{k} ({v})" for k, v in list(payment_methods.items())[:3]]),
        "domestic_pct": round(domestic_pct, 1),
        "unique_counterparties": len(counterparties),
        "time_pattern": "business hours" if len(transactions) > 5 else "insufficient data"
    }

def format_transactions_for_prompt(transactions: list, max_txns: int = 20) -> str:
    """Format transactions for the LLM prompt."""
    sample = transactions[:max_txns]
    lines = []
    for t in sample:
        amt = t.get("amount", {})
        if isinstance(amt, dict):
            amount = amt.get("sent", 0) or amt.get("received", 0)
            currency = amt.get("currency_sent", "USD")
        else:
            amount = amt or 0
            currency = "USD"
        method = t.get("payment_format", "Unknown")
        timestamp = t.get("timestamp", "Unknown date")
        receiver = t.get("receiver", {})
        to_bank = receiver.get("bank_id", "?") if isinstance(receiver, dict) else "?"
        lines.append(f"  - {timestamp}: {currency} {amount:,.2f} via {method} to Bank {to_bank}")
    return "\n".join(lines)

def generate_profile(openai_client, transactions: list, stats: dict) -> dict:
    """Use LLM to generate customer profile from transactions."""
    prompt = SHERLOCK_PROMPT.format(
        txn_count=len(transactions),
        transactions=format_transactions_for_prompt(transactions),
        avg_amount=f"{stats['avg_amount']:,.2f}",
        frequency=stats['frequency'],
        payment_methods=stats['payment_methods'],
        domestic_pct=stats['domestic_pct'],
        unique_counterparties=stats['unique_counterparties'],
        time_pattern=stats['time_pattern']
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",  # Cost-effective for this task
        messages=[
            {"role": "system", "content": "You are a financial analyst. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  # Low temperature for consistency
        max_tokens=500
    )

    content = response.choices[0].message.content.strip()

    # Parse JSON (handle potential markdown code blocks)
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    return json.loads(content)

# ============================================================
# MAIN WORKFLOW
# ============================================================

def select_golden_sample(db) -> dict:
    """Select accounts for the Golden Sample: 50 clean, 50 with laundering."""
    print("\n[1/4] Selecting Golden Sample accounts...")

    # Find accounts that have laundering transactions (using nested sender.account_id)
    laundering_accounts = list(db.transactions.aggregate([
        {"$match": {"is_laundering": True}},
        {"$group": {"_id": "$sender.account_id"}},
        {"$limit": LAUNDERING_ACCOUNTS_SAMPLE * 2}  # Get extra in case some have too few txns
    ]))
    laundering_account_ids = [a["_id"] for a in laundering_accounts]
    print(f"    Found {len(laundering_account_ids)} accounts with laundering transactions")

    # Find accounts with NO laundering transactions (only clean activity)
    clean_accounts = list(db.transactions.aggregate([
        {"$match": {"is_laundering": False, "sender.account_id": {"$nin": laundering_account_ids}}},
        {"$group": {"_id": "$sender.account_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 10}}},  # At least 10 transactions
        {"$limit": CLEAN_ACCOUNTS_SAMPLE * 2}
    ]))
    clean_account_ids = [a["_id"] for a in clean_accounts]
    print(f"    Found {len(clean_account_ids)} clean accounts with 10+ transactions")

    # Sample
    selected_clean = random.sample(clean_account_ids, min(CLEAN_ACCOUNTS_SAMPLE, len(clean_account_ids)))
    selected_laundering = random.sample(laundering_account_ids, min(LAUNDERING_ACCOUNTS_SAMPLE, len(laundering_account_ids)))

    print(f"    Selected {len(selected_clean)} clean accounts for sample")
    print(f"    Selected {len(selected_laundering)} accounts with laundering for sample")

    return {
        "clean": selected_clean,
        "laundering": selected_laundering
    }

def generate_profiles_for_sample(db, openai_client, sample: dict):
    """Generate profiles for all accounts in the sample."""
    print("\n[2/4] Generating profiles from clean transaction behavior...")

    all_accounts = sample["clean"] + sample["laundering"]
    profiles_generated = 0

    for i, account_id in enumerate(all_accounts):
        print(f"\n    Processing account {i+1}/{len(all_accounts)}: {account_id}")

        # Get ONLY clean transactions for this account (using nested sender.account_id)
        clean_txns = list(db.transactions.find({
            "sender.account_id": account_id,
            "is_laundering": False
        }).sort("timestamp", 1).limit(50))  # First 50 clean transactions

        if len(clean_txns) < 5:
            print(f"      Skipping - only {len(clean_txns)} clean transactions")
            continue

        # Analyze behavior
        stats = analyze_transactions(clean_txns)

        # Generate profile
        try:
            profile = generate_profile(openai_client, clean_txns, stats)

            # Add metadata
            profile["_generated_at"] = datetime.utcnow().isoformat()
            profile["_based_on_txn_count"] = len(clean_txns)
            profile["_behavioral_stats"] = stats
            profile["_has_laundering"] = account_id in sample["laundering"]

            # Count laundering transactions for this account
            launder_count = db.transactions.count_documents({
                "sender.account_id": account_id,
                "is_laundering": True
            })
            profile["_laundering_txn_count"] = launder_count

            # Store in MongoDB
            db.accounts.update_one(
                {"account_id": account_id},
                {
                    "$set": {
                        "profile": profile,
                        "profile_generated": True
                    }
                },
                upsert=True
            )

            profiles_generated += 1
            print(f"      Generated: {profile['customer_type']} - {profile['likely_occupation_or_industry']}")
            print(f"      Narrative: {profile['narrative_summary'][:100]}...")

        except Exception as e:
            print(f"      Error generating profile: {e}")
            continue

    return profiles_generated

def verify_profiles(db):
    """Verify generated profiles and show sample."""
    print("\n[3/4] Verifying generated profiles...")

    profiles = list(db.accounts.find({"profile_generated": True}).limit(5))

    print(f"\n    Sample profiles generated:")
    print("    " + "="*60)

    for p in profiles:
        profile = p.get("profile", {})
        print(f"\n    Account: {p['account_id']}")
        print(f"    Type: {profile.get('customer_type')} / {profile.get('subtype')}")
        print(f"    Industry: {profile.get('likely_occupation_or_industry')}")
        print(f"    Income: {profile.get('estimated_monthly_income_or_revenue')}")
        print(f"    Has Laundering: {profile.get('_has_laundering')} ({profile.get('_laundering_txn_count', 0)} txns)")
        print(f"    Narrative: {profile.get('narrative_summary', 'N/A')[:150]}...")
        print("    " + "-"*60)

def print_summary(db, profiles_generated: int):
    """Print final summary."""
    print("\n[4/4] Summary")
    print("="*60)

    total_with_profiles = db.accounts.count_documents({"profile_generated": True})
    clean_with_profiles = db.accounts.count_documents({
        "profile_generated": True,
        "profile._has_laundering": False
    })
    laundering_with_profiles = db.accounts.count_documents({
        "profile_generated": True,
        "profile._has_laundering": True
    })

    print(f"    Profiles generated this run: {profiles_generated}")
    print(f"    Total accounts with profiles: {total_with_profiles}")
    print(f"    - Clean accounts: {clean_with_profiles}")
    print(f"    - Accounts with laundering: {laundering_with_profiles}")
    print()
    print("    Next step: Run the day-by-day simulator to test CNA detection")
    print("="*60)

# ============================================================
# ENTRY POINT
# ============================================================

def main():
    print("="*60)
    print("PROFILE REVERSE-ENGINEERING GENERATOR")
    print("'Sherlock Holmes' Script for CNA Testing")
    print("="*60)

    # Connect
    mongo_client = get_mongo_client()
    db = mongo_client[DATABASE_NAME]
    openai_client = get_openai_client()

    print(f"\nConnected to MongoDB: {DATABASE_NAME}")

    # Step 1: Select Golden Sample
    sample = select_golden_sample(db)

    # Step 2: Generate profiles
    profiles_generated = generate_profiles_for_sample(db, openai_client, sample)

    # Step 3: Verify
    verify_profiles(db)

    # Step 4: Summary
    print_summary(db, profiles_generated)

if __name__ == "__main__":
    main()
