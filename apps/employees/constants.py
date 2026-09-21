"""apps/employees/constants.py - Paystack bank codes and mapping for Ghana"""
import re

GHANA_PAYSTACK_BANKS = [
    {"name": "Absa Bank Ghana Ltd", "code": "030100", "type": "ghipss"},
    {"name": "Access Bank", "code": "280100", "type": "ghipss"},
    {"name": "ADB Bank Limited", "code": "080100", "type": "ghipss"},
    {"name": "Adehyeman Savings and Loans LTD", "code": "300345", "type": "ghipss"},
    {"name": "Affinity Ghana Savings and Loans", "code": "300341", "type": "ghipss"},
    {"name": "ARB Apex Bank", "code": "070101", "type": "ghipss"},
    {"name": "Bank of Africa Ghana", "code": "210100", "type": "ghipss"},
    {"name": "Bank of Ghana", "code": "010100", "type": "ghipss"},
    {"name": "Best Point Savings & Loans", "code": "300335", "type": "ghipss"},
    {"name": "CAL Bank Limited", "code": "140100", "type": "ghipss"},
    {"name": "Consolidated Bank Ghana Limited", "code": "340100", "type": "ghipss"},
    {"name": "Ecobank Ghana Limited", "code": "130100", "type": "ghipss"},
    {"name": "FBNBank Ghana Limited", "code": "200100", "type": "ghipss"},
    {"name": "Fidelity Bank Ghana Limited", "code": "240100", "type": "ghipss"},
    {"name": "First Atlantic Bank Limited", "code": "170100", "type": "ghipss"},
    {"name": "First National Bank Ghana Limited", "code": "330100", "type": "ghipss"},
    {"name": "GCB Bank Limited", "code": "040100", "type": "ghipss"},
    {"name": "Guaranty Trust Bank (Ghana) Limited", "code": "230100", "type": "ghipss"},
    {"name": "National Investment Bank Limited", "code": "050100", "type": "ghipss"},
    {"name": "OmniBSCI Bank", "code": "360100", "type": "ghipss"},
    {"name": "Prudential Bank Limited", "code": "180100", "type": "ghipss"},
    {"name": "Republic Bank (GH) Limited", "code": "110100", "type": "ghipss"},
    {"name": "Services Integrity Savings and Loans", "code": "300361", "type": "ghipss"},
    {"name": "Sinapi ABA Savings And Loans", "code": "240092", "type": "ghipss"},
    {"name": "Société Générale Ghana Limited", "code": "090100", "type": "ghipss"},
    {"name": "Stanbic Bank Ghana Limited", "code": "190100", "type": "ghipss"},
    {"name": "Standard Chartered Bank Ghana Limited", "code": "020100", "type": "ghipss"},
    {"name": "United Bank for Africa Ghana Limited", "code": "060100", "type": "ghipss"},
    {"name": "Universal Merchant Bank Ghana Limited", "code": "100100", "type": "ghipss"},
    {"name": "Zenith Bank Ghana", "code": "120100", "type": "ghipss"},
]

# Aliases and common variations mapped to Paystack bank codes
BANK_ALIASES = {
    'absa': '030100',
    'access': '280100',
    'adb': '080100',
    'agricultural development': '080100',
    'adehyeman': '300345',
    'affinity': '300341',
    'arb apex': '070101',
    'bank of africa': '210100',
    'boa': '210100',
    'bank of ghana': '010100',
    'bog': '010100',
    'best point': '300335',
    'cal': '140100',
    'calbank': '140100',
    'consolidated': '340100',
    'cbg': '340100',
    'ecobank': '130100',
    'fbn': '200100',
    'fbnbank': '200100',
    'fidelity': '240100',
    'first atlantic': '170100',
    'first national': '330100',
    'fnb': '330100',
    'gcb': '040100',
    'ghana commercial bank': '040100',
    'guaranty trust': '230100',
    'gt bank': '230100',
    'gtbank': '230100',
    'nib': '050100',
    'national investment': '050100',
    'omnibsic': '360100',
    'omnibsci': '360100',
    'prudential': '180100',
    'republic': '110100',
    'services integrity': '300361',
    'sinapi aba': '240092',
    'societe generale': '090100',
    'société générale': '090100',
    'sg-ssb': '090100',
    'stanbic': '190100',
    'standard chartered': '020100',
    'stanchart': '020100',
    'uba': '060100',
    'united bank for africa': '060100',
    'umb': '100100',
    'universal merchant': '100100',
    'zenith': '120100',
}

PAYSTACK_MOMO_PROVIDERS = {
    'mtn': 'MTN',
    'vodafone': 'VOD',
    'telecel': 'VOD',
    'airteltigo': 'ATL',
    'airtel': 'ATL',
    'tigo': 'ATL',
}


def normalize_name(name: str) -> str:
    if not name:
        return ''
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
    return ' '.join(cleaned.split())


def resolve_bank_code(bank_name: str) -> str:
    """Resolve a Ghanaian bank name to its Paystack GHIPSS bank code."""
    if not bank_name:
        return ''

    norm = normalize_name(bank_name)

    # 1. Direct alias check
    for alias, code in BANK_ALIASES.items():
        if alias in norm or norm in alias:
            return code

    # 2. Check against official bank names
    for item in GHANA_PAYSTACK_BANKS:
        official_norm = normalize_name(item['name'])
        if norm in official_norm or official_norm in norm:
            return item['code']

    # 3. Check individual significant words
    words = [w for w in norm.split() if w not in ('bank', 'ghana', 'limited', 'ltd', 'the')]
    for word in words:
        if word in BANK_ALIASES:
            return BANK_ALIASES[word]

    return ''
