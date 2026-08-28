TRADE_ALIASES = {
    "plumber": {"plumber", "plumbing"},
    "plumbing": {"plumber", "plumbing"},
    "electrician": {"electrician", "electrical"},
    "electrical": {"electrician", "electrical"},
    "heating engineer": {
        "heating engineer",
        "heating",
        "hvac",
    },
    "roofer": {"roofer", "roofing"},
    "locksmith": {"locksmith"},
    "carpenter": {"carpenter", "carpentry"},
    "painter": {"painter", "painting"},
    "appliance repair technician": {
        "appliance repair technician",
        "appliance repair",
    },
}


TEST_EXTERNAL_PROVIDERS = [
    # -------------------------
    # PLUMBING
    # -------------------------

    {
        "id": "external-001",
        "name": "Test Plumbing Services",
        "trades": ["plumber", "plumbing"],
        "location": "Colchester",
        "distance_miles": 2.4,
        "rating": 4.9,
        "verified": True,
        "emergency_available": True,
    },
    {
        "id": "external-002",
        "name": "Colchester Premier Plumbing",
        "trades": ["plumber", "plumbing"],
        "location": "Colchester",
        "distance_miles": 3.8,
        "rating": 4.8,
        "verified": True,
        "emergency_available": True,
    },
    {
        "id": "external-003",
        "name": "Essex Plumbing & Heating",
        "trades": ["plumber", "plumbing"],
        "location": "Colchester",
        "distance_miles": 5.1,
        "rating": 4.7,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-004",
        "name": "Rapid Response Plumbing",
        "trades": ["plumber", "plumbing"],
        "location": "Colchester",
        "distance_miles": 6.4,
        "rating": 4.6,
        "verified": True,
        "emergency_available": True,
    },

    # -------------------------
    # ELECTRICAL
    # -------------------------

    {
        "id": "external-005",
        "name": "Test Electrical Services",
        "trades": ["electrician", "electrical"],
        "location": "Colchester",
        "distance_miles": 3.1,
        "rating": 4.8,
        "verified": True,
        "emergency_available": True,
    },
    {
        "id": "external-006",
        "name": "Colchester Electrical Solutions",
        "trades": ["electrician", "electrical"],
        "location": "Colchester",
        "distance_miles": 4.2,
        "rating": 4.7,
        "verified": True,
        "emergency_available": True,
    },
    {
        "id": "external-007",
        "name": "Essex Electrical Experts",
        "trades": ["electrician", "electrical"],
        "location": "Colchester",
        "distance_miles": 5.6,
        "rating": 4.6,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-008",
        "name": "Rapid Electrical Response",
        "trades": ["electrician", "electrical"],
        "location": "Colchester",
        "distance_miles": 7.2,
        "rating": 4.5,
        "verified": True,
        "emergency_available": True,
    },

    # -------------------------
    # HEATING
    # -------------------------

    {
        "id": "external-009",
        "name": "Test Heating & Boiler Services",
        "trades": ["heating engineer", "heating", "hvac"],
        "location": "Colchester",
        "distance_miles": 4.7,
        "rating": 4.7,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-010",
        "name": "Colchester Boiler Experts",
        "trades": ["heating engineer", "heating", "hvac"],
        "location": "Colchester",
        "distance_miles": 3.9,
        "rating": 4.8,
        "verified": True,
        "emergency_available": True,
    },
    {
        "id": "external-011",
        "name": "Essex Heating Solutions",
        "trades": ["heating engineer", "heating", "hvac"],
        "location": "Colchester",
        "distance_miles": 6.1,
        "rating": 4.6,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-012",
        "name": "Rapid Heating Response",
        "trades": ["heating engineer", "heating", "hvac"],
        "location": "Colchester",
        "distance_miles": 7.4,
        "rating": 4.5,
        "verified": True,
        "emergency_available": True,
    },

    # -------------------------
    # ROOFING
    # -------------------------

    {
        "id": "external-013",
        "name": "Test Roofing Services",
        "trades": ["roofer", "roofing"],
        "location": "Colchester",
        "distance_miles": 4.4,
        "rating": 4.8,
        "verified": True,
        "emergency_available": True,
    },
    {
        "id": "external-014",
        "name": "Colchester Roofing Experts",
        "trades": ["roofer", "roofing"],
        "location": "Colchester",
        "distance_miles": 5.3,
        "rating": 4.7,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-015",
        "name": "Essex Roof Care",
        "trades": ["roofer", "roofing"],
        "location": "Colchester",
        "distance_miles": 6.2,
        "rating": 4.6,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-016",
        "name": "Rapid Roof Repairs",
        "trades": ["roofer", "roofing"],
        "location": "Colchester",
        "distance_miles": 7.1,
        "rating": 4.5,
        "verified": True,
        "emergency_available": True,
    },

    # -------------------------
    # LOCKSMITH
    # -------------------------

    {
        "id": "external-017",
        "name": "Test Locksmith Services",
        "trades": ["locksmith"],
        "location": "Colchester",
        "distance_miles": 2.8,
        "rating": 4.9,
        "verified": True,
        "emergency_available": True,
    },
    {
        "id": "external-018",
        "name": "Colchester Lock & Key",
        "trades": ["locksmith"],
        "location": "Colchester",
        "distance_miles": 4.1,
        "rating": 4.8,
        "verified": True,
        "emergency_available": True,
    },
    {
        "id": "external-019",
        "name": "Essex Locksmith Solutions",
        "trades": ["locksmith"],
        "location": "Colchester",
        "distance_miles": 5.5,
        "rating": 4.6,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-020",
        "name": "Rapid Locksmith Response",
        "trades": ["locksmith"],
        "location": "Colchester",
        "distance_miles": 6.7,
        "rating": 4.5,
        "verified": True,
        "emergency_available": True,
    },

    # -------------------------
    # CARPENTRY
    # -------------------------

    {
        "id": "external-021",
        "name": "Test Carpentry Services",
        "trades": ["carpenter", "carpentry"],
        "location": "Colchester",
        "distance_miles": 3.7,
        "rating": 4.8,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-022",
        "name": "Colchester Joinery & Carpentry",
        "trades": ["carpenter", "carpentry"],
        "location": "Colchester",
        "distance_miles": 4.8,
        "rating": 4.7,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-023",
        "name": "Essex Carpenter Solutions",
        "trades": ["carpenter", "carpentry"],
        "location": "Colchester",
        "distance_miles": 6.0,
        "rating": 4.6,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-024",
        "name": "Precision Carpentry",
        "trades": ["carpenter", "carpentry"],
        "location": "Colchester",
        "distance_miles": 7.3,
        "rating": 4.5,
        "verified": True,
        "emergency_available": False,
    },

    # -------------------------
    # PAINTING
    # -------------------------

    {
        "id": "external-025",
        "name": "Test Painting Services",
        "trades": ["painter", "painting"],
        "location": "Colchester",
        "distance_miles": 3.5,
        "rating": 4.8,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-026",
        "name": "Colchester Professional Painters",
        "trades": ["painter", "painting"],
        "location": "Colchester",
        "distance_miles": 4.6,
        "rating": 4.7,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-027",
        "name": "Essex Painting Solutions",
        "trades": ["painter", "painting"],
        "location": "Colchester",
        "distance_miles": 5.9,
        "rating": 4.6,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-028",
        "name": "Premier Property Painters",
        "trades": ["painter", "painting"],
        "location": "Colchester",
        "distance_miles": 7.0,
        "rating": 4.5,
        "verified": True,
        "emergency_available": False,
    },

    # -------------------------
    # APPLIANCE REPAIR
    # -------------------------

    {
        "id": "external-029",
        "name": "Test Appliance Repair Services",
        "trades": [
            "appliance repair technician",
            "appliance repair",
        ],
        "location": "Colchester",
        "distance_miles": 3.6,
        "rating": 4.9,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-030",
        "name": "Colchester Appliance Experts",
        "trades": [
            "appliance repair technician",
            "appliance repair",
        ],
        "location": "Colchester",
        "distance_miles": 4.5,
        "rating": 4.8,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-031",
        "name": "Essex Appliance Solutions",
        "trades": [
            "appliance repair technician",
            "appliance repair",
        ],
        "location": "Colchester",
        "distance_miles": 5.8,
        "rating": 4.7,
        "verified": True,
        "emergency_available": False,
    },
    {
        "id": "external-032",
        "name": "Rapid Appliance Repairs",
        "trades": [
            "appliance repair technician",
            "appliance repair",
        ],
        "location": "Colchester",
        "distance_miles": 6.9,
        "rating": 4.6,
        "verified": True,
        "emergency_available": False,
    },
]


def normalise_trade(trade):
    trade = (trade or "").strip().lower()

    for canonical_trade, aliases in TRADE_ALIASES.items():
        if trade in aliases:
            return canonical_trade

    return trade


def provider_matches_trade(provider, required_trade):
    required_trade = normalise_trade(required_trade)

    provider_trades = {
        normalise_trade(trade)
        for trade in provider.get("trades", [])
    }

    return required_trade in provider_trades


def calculate_provider_score(provider):
    rating_score = provider["rating"] / 5

    distance_score = max(
        0,
        1 - (provider["distance_miles"] / 25)
    )

    verified_score = (
        1.0
        if provider["verified"]
        else 0.5
    )

    return round(
        (
            rating_score * 0.5
            + distance_score * 0.3
            + verified_score * 0.2
        ),
        3,
    )


def search_external_providers(required_trade):
    matching_providers = []

    for provider in TEST_EXTERNAL_PROVIDERS:
        if not provider_matches_trade(
            provider,
            required_trade
        ):
            continue

        provider_result = {
            **provider,
            "match_score": calculate_provider_score(
                provider
            ),
        }

        matching_providers.append(provider_result)

    matching_providers.sort(
        key=lambda provider: provider["match_score"],
        reverse=True
    )

    return matching_providers[:4]