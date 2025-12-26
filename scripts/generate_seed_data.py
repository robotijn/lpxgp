#!/usr/bin/env python3
"""Generate 10,000 LPs and 10,000 GPs for testing.

This script generates realistic test data and saves it to JSON files
in data/seed/ directory. Run once to generate, then use load_seed_data.py
to load into the database.

Usage:
    uv run python scripts/generate_seed_data.py
"""

import json
import random
import uuid
from pathlib import Path

# Output directory
SEED_DIR = Path(__file__).parent.parent / "data" / "seed"
SEED_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# Name Components for Realistic Data
# =============================================================================

LP_PREFIXES = [
    "State", "National", "Public", "Municipal", "Regional", "Federal",
    "University", "College", "School", "Foundation", "Trust", "Heritage",
]

LP_SUFFIXES_PENSION = [
    "Pension Fund", "Retirement System", "Teachers Retirement",
    "Employees Retirement", "Public Employees", "State Retirement",
    "Municipal Retirement", "Police & Fire Retirement",
]

LP_SUFFIXES_ENDOWMENT = [
    "Endowment", "University Endowment", "Foundation Endowment",
    "Educational Foundation", "Scholarship Fund", "Academic Trust",
]

LP_SUFFIXES_FOUNDATION = [
    "Foundation", "Charitable Foundation", "Family Foundation",
    "Community Foundation", "Philanthropic Trust", "Giving Fund",
]

LP_SUFFIXES_FAMILY_OFFICE = [
    "Family Office", "Family Investments", "Family Capital",
    "Private Office", "Wealth Management", "Family Holdings",
]

LP_SUFFIXES_SOVEREIGN = [
    "Investment Authority", "Sovereign Fund", "National Fund",
    "Investment Corporation", "State Investment", "Reserve Fund",
]

LP_SUFFIXES_INSURANCE = [
    "Insurance Company", "Life Insurance", "Mutual Insurance",
    "Insurance Group", "Assurance Company", "Re-Insurance",
]

GP_PREFIXES = [
    "Summit", "Alpine", "Pacific", "Atlantic", "Horizon", "Pinnacle",
    "Apex", "Vertex", "Sequoia", "Redwood", "Oak", "Maple", "Cedar",
    "Granite", "Sterling", "Golden", "Silver", "Platinum", "Diamond",
    "Emerald", "Sapphire", "Ruby", "Onyx", "Cobalt", "Iron", "Steel",
    "Titan", "Atlas", "Apollo", "Mercury", "Jupiter", "Saturn", "Mars",
    "Orion", "Polaris", "Nova", "Stellar", "Cosmic", "Galaxy", "Nebula",
    "Vector", "Matrix", "Quantum", "Fusion", "Catalyst", "Nexus", "Vertex",
    "Vanguard", "Pioneer", "Frontier", "Endeavor", "Aspire", "Elevate",
]

GP_SUFFIXES = [
    "Capital", "Partners", "Ventures", "Equity", "Investments",
    "Capital Partners", "Investment Partners", "Equity Partners",
    "Growth Partners", "Private Equity", "Capital Management",
    "Asset Management", "Investment Management", "Fund Management",
    "Capital Group", "Investment Group", "Holdings", "Advisors",
]

FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "David", "William", "Richard",
    "Joseph", "Thomas", "Charles", "Mary", "Patricia", "Jennifer", "Linda",
    "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Emily",
    "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul",
    "Andrew", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Timothy",
    "Ronald", "Edward", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary",
    "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz",
]

US_STATES = [
    ("New York", "NY"), ("California", "CA"), ("Texas", "TX"),
    ("Florida", "FL"), ("Illinois", "IL"), ("Pennsylvania", "PA"),
    ("Ohio", "OH"), ("Georgia", "GA"), ("North Carolina", "NC"),
    ("Michigan", "MI"), ("New Jersey", "NJ"), ("Virginia", "VA"),
    ("Washington", "WA"), ("Arizona", "AZ"), ("Massachusetts", "MA"),
    ("Tennessee", "TN"), ("Indiana", "IN"), ("Missouri", "MO"),
    ("Maryland", "MD"), ("Wisconsin", "WI"), ("Colorado", "CO"),
    ("Minnesota", "MN"), ("South Carolina", "SC"), ("Alabama", "AL"),
    ("Louisiana", "LA"), ("Kentucky", "KY"), ("Oregon", "OR"),
    ("Oklahoma", "OK"), ("Connecticut", "CT"), ("Utah", "UT"),
]

US_CITIES = {
    "NY": ["New York", "Buffalo", "Rochester", "Albany"],
    "CA": ["Los Angeles", "San Francisco", "San Diego", "San Jose", "Sacramento"],
    "TX": ["Houston", "Dallas", "Austin", "San Antonio", "Fort Worth"],
    "FL": ["Miami", "Tampa", "Orlando", "Jacksonville"],
    "IL": ["Chicago", "Springfield", "Naperville"],
    "PA": ["Philadelphia", "Pittsburgh", "Harrisburg"],
    "MA": ["Boston", "Cambridge", "Worcester"],
    "WA": ["Seattle", "Tacoma", "Spokane"],
    "CO": ["Denver", "Boulder", "Colorado Springs"],
    "GA": ["Atlanta", "Savannah", "Augusta"],
}

INTERNATIONAL_LOCATIONS = [
    ("London", "United Kingdom"), ("Toronto", "Canada"), ("Sydney", "Australia"),
    ("Singapore", "Singapore"), ("Hong Kong", "Hong Kong"), ("Tokyo", "Japan"),
    ("Frankfurt", "Germany"), ("Paris", "France"), ("Zurich", "Switzerland"),
    ("Amsterdam", "Netherlands"), ("Dublin", "Ireland"), ("Stockholm", "Sweden"),
    ("Oslo", "Norway"), ("Copenhagen", "Denmark"), ("Milan", "Italy"),
    ("Madrid", "Spain"), ("Seoul", "South Korea"), ("Shanghai", "China"),
    ("Beijing", "China"), ("Mumbai", "India"), ("Dubai", "UAE"),
    ("Abu Dhabi", "UAE"), ("Riyadh", "Saudi Arabia"), ("Tel Aviv", "Israel"),
    ("Sao Paulo", "Brazil"), ("Mexico City", "Mexico"), ("Buenos Aires", "Argentina"),
]

STRATEGIES = ["buyout", "growth", "venture", "real_estate", "infrastructure", "credit", "secondaries"]
GEOGRAPHIES = ["North America", "Europe", "Asia Pacific", "Global", "Latin America", "Middle East", "Africa"]
SECTORS = ["Technology", "Healthcare", "Financial Services", "Consumer", "Industrial", "Energy", "Media"]

LP_TYPES = ["pension", "endowment", "foundation", "family_office", "sovereign_wealth", "insurance", "fund_of_funds"]


def generate_lp_name(lp_type: str, index: int) -> str:
    """Generate a realistic LP name based on type."""
    if lp_type == "pension":
        if random.random() < 0.3:
            state, abbr = random.choice(US_STATES)
            return f"{state} {random.choice(LP_SUFFIXES_PENSION)}"
        else:
            return f"{random.choice(LP_PREFIXES)} {random.choice(LP_SUFFIXES_PENSION)}"
    elif lp_type == "endowment":
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        return f"{first} {last} {random.choice(LP_SUFFIXES_ENDOWMENT)}"
    elif lp_type == "foundation":
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        return f"{last} {random.choice(LP_SUFFIXES_FOUNDATION)}"
    elif lp_type == "family_office":
        last = random.choice(LAST_NAMES)
        return f"{last} {random.choice(LP_SUFFIXES_FAMILY_OFFICE)}"
    elif lp_type == "sovereign_wealth":
        return f"{random.choice(['National', 'State', 'Royal', 'Government'])} {random.choice(LP_SUFFIXES_SOVEREIGN)}"
    elif lp_type == "insurance":
        prefix = random.choice(["First", "United", "American", "National", "Guardian", "Metropolitan"])
        return f"{prefix} {random.choice(LP_SUFFIXES_INSURANCE)}"
    elif lp_type == "fund_of_funds":
        return f"{random.choice(GP_PREFIXES)} {random.choice(['Fund of Funds', 'Multi-Manager Fund', 'PE Fund of Funds', 'Private Markets Fund'])}"
    else:
        return f"{random.choice(LP_PREFIXES)} {random.choice(['Investment Fund', 'Capital Fund', 'Partners Fund'])}"


def generate_gp_name(index: int) -> str:
    """Generate a realistic GP name."""
    style = random.choice(["prefix_suffix", "name_partners", "location_capital"])

    if style == "prefix_suffix":
        return f"{random.choice(GP_PREFIXES)} {random.choice(GP_SUFFIXES)}"
    elif style == "name_partners":
        last1 = random.choice(LAST_NAMES)
        last2 = random.choice(LAST_NAMES)
        while last2 == last1:
            last2 = random.choice(LAST_NAMES)
        return f"{last1} & {last2} {random.choice(['Partners', 'Capital', 'Ventures'])}"
    else:
        city = random.choice(list(US_CITIES.values()))[0] if random.random() < 0.7 else random.choice(INTERNATIONAL_LOCATIONS)[0]
        return f"{city} {random.choice(GP_SUFFIXES)}"


def generate_location() -> tuple[str, str]:
    """Generate a random city and country."""
    if random.random() < 0.7:  # 70% US
        state, abbr = random.choice(US_STATES)
        cities = US_CITIES.get(abbr, [state])
        city = random.choice(cities)
        return city, "USA"
    else:
        return random.choice(INTERNATIONAL_LOCATIONS)


def generate_website(name: str) -> str:
    """Generate a plausible website from org name."""
    # Clean name for domain
    domain = name.lower()
    domain = domain.replace(" & ", "")
    domain = domain.replace("'s", "")
    words = domain.split()[:2]  # First two words
    domain = "".join(words)
    domain = "".join(c for c in domain if c.isalnum())
    return f"https://www.{domain}.com"


def generate_lp_data(count: int = 10000) -> list[dict]:
    """Generate LP organizations and profiles."""
    lps = []

    # Distribute LP types realistically
    type_weights = {
        "pension": 0.25,
        "endowment": 0.15,
        "foundation": 0.15,
        "family_office": 0.20,
        "sovereign_wealth": 0.05,
        "insurance": 0.10,
        "fund_of_funds": 0.10,
    }

    for i in range(count):
        # Pick LP type based on weights
        lp_type = random.choices(
            list(type_weights.keys()),
            weights=list(type_weights.values())
        )[0]

        name = generate_lp_name(lp_type, i)
        city, country = generate_location()

        # Generate AUM based on LP type (in billions)
        if lp_type == "sovereign_wealth":
            aum = random.uniform(50, 1500)
        elif lp_type == "pension":
            aum = random.uniform(5, 500)
        elif lp_type == "endowment":
            aum = random.uniform(1, 50)
        elif lp_type == "insurance":
            aum = random.uniform(10, 200)
        elif lp_type == "family_office":
            aum = random.uniform(0.1, 10)
        else:
            aum = random.uniform(0.5, 50)

        # PE allocation varies by type
        if lp_type in ["pension", "endowment"]:
            pe_allocation = random.uniform(5, 20)
        elif lp_type == "family_office":
            pe_allocation = random.uniform(10, 40)
        else:
            pe_allocation = random.uniform(3, 15)

        # Check size based on AUM
        check_min = max(1, aum * 0.001 * random.uniform(0.5, 2))  # 0.05-0.2% of AUM
        check_max = check_min * random.uniform(2, 10)

        # Strategies - pick 1-4
        num_strategies = random.randint(1, 4)
        strategies = random.sample(STRATEGIES, num_strategies)

        # Geographies - pick 1-3
        num_geos = random.randint(1, 3)
        geographies = random.sample(GEOGRAPHIES, num_geos)

        # Sectors - pick 0-4
        num_sectors = random.randint(0, 4)
        sectors = random.sample(SECTORS, num_sectors) if num_sectors > 0 else []

        lp = {
            "id": str(uuid.uuid4()),
            "organization": {
                "name": name,
                "website": generate_website(name),
                "hq_city": city,
                "hq_country": country,
                "description": f"{name} is a {lp_type.replace('_', ' ')} based in {city}, {country}.",
                "is_gp": False,
                "is_lp": True,
            },
            "profile": {
                "lp_type": lp_type,
                "total_aum_bn": round(aum, 2),
                "pe_allocation_pct": round(pe_allocation, 2),
                "strategies": strategies,
                "geographic_preferences": geographies,
                "sector_preferences": sectors,
                "check_size_min_mm": round(check_min, 2),
                "check_size_max_mm": round(check_max, 2),
                "fund_size_min_mm": round(check_min * 5, 2),
                "fund_size_max_mm": round(check_max * 20, 2),
                "min_track_record_years": random.choice([0, 3, 5, 7, 10]),
                "min_fund_number": random.choice([1, 2, 3, 4]),
                "esg_required": random.random() < 0.3,
                "emerging_manager_ok": random.random() < 0.4,
            }
        }
        lps.append(lp)

        if (i + 1) % 1000 == 0:
            print(f"Generated {i + 1} LPs...")

    return lps


def generate_gp_data(count: int = 10000) -> list[dict]:
    """Generate GP organizations and profiles."""
    gps = []

    for i in range(count):
        name = generate_gp_name(i)
        city, country = generate_location()

        # Team size
        team_size = random.randint(5, 100)

        # Years investing
        years = random.randint(1, 40)

        # Notable exits (0-5)
        num_exits = random.randint(0, 5)
        exits = []
        for _ in range(num_exits):
            exits.append({
                "company": f"{random.choice(GP_PREFIXES)}Corp",
                "year": random.randint(2010, 2024),
                "multiple": round(random.uniform(1.5, 10), 1),
            })

        gp = {
            "id": str(uuid.uuid4()),
            "organization": {
                "name": name,
                "website": generate_website(name),
                "hq_city": city,
                "hq_country": country,
                "description": f"{name} is a private equity firm based in {city}, {country}.",
                "is_gp": True,
                "is_lp": False,
            },
            "profile": {
                "investment_philosophy": random.choice([
                    "Value-oriented approach focused on operational improvements",
                    "Growth equity investing in market-leading companies",
                    "Partnering with management teams to drive transformation",
                    "Sector-focused strategy with deep domain expertise",
                    "Flexible capital solutions across the capital structure",
                ]),
                "team_size": team_size,
                "years_investing": years,
                "spun_out_from": random.choice([None, None, None, "Goldman Sachs", "KKR", "Blackstone", "TPG", "Bain Capital"]),
                "notable_exits": exits,
                "track_record_summary": {
                    "funds_raised": random.randint(1, 10),
                    "total_aum_bn": round(random.uniform(0.5, 50), 2),
                    "avg_irr": round(random.uniform(10, 35), 1),
                    "avg_moic": round(random.uniform(1.5, 3.5), 2),
                }
            }
        }
        gps.append(gp)

        if (i + 1) % 1000 == 0:
            print(f"Generated {i + 1} GPs...")

    return gps


def main():
    """Generate and save seed data."""
    print("Generating 10,000 LPs...")
    lps = generate_lp_data(10000)

    print("Generating 10,000 GPs...")
    gps = generate_gp_data(10000)

    # Save to JSON files
    lp_file = SEED_DIR / "lps_10k.json"
    gp_file = SEED_DIR / "gps_10k.json"

    print(f"Saving LPs to {lp_file}...")
    with open(lp_file, "w") as f:
        json.dump(lps, f, indent=2)

    print(f"Saving GPs to {gp_file}...")
    with open(gp_file, "w") as f:
        json.dump(gps, f, indent=2)

    print("\nDone! Generated:")
    print(f"  - {len(lps)} LPs -> {lp_file}")
    print(f"  - {len(gps)} GPs -> {gp_file}")
    print("\nTotal file sizes:")
    print(f"  - LPs: {lp_file.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"  - GPs: {gp_file.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
