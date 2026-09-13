COMPANIES = [
    {"name": "Acme Analytics", "industry": "Software", "sponsors_h1b": True},
    {"name": "Northwind Foods", "industry": "Consumer", "sponsors_h1b": False},
    {"name": "Contoso Cloud", "industry": "Software", "sponsors_h1b": True},
    {"name": "BlueRiver Health", "industry": "Healthcare", "sponsors_h1b": False},
    {"name": "Fabrikam Robotics", "industry": "Manufacturing", "sponsors_h1b": True},
    {"name": "Globex Financial", "industry": "Finance", "sponsors_h1b": True},
    {"name": "Initech Systems", "industry": "Software", "sponsors_h1b": False},
    {"name": "Umbrella Biotech", "industry": "Healthcare", "sponsors_h1b": True},
]


def search_companies(query: str):
    query = query.strip().lower()
    if not query:
        return COMPANIES
    return [c for c in COMPANIES if query in c["name"].lower() or query in c["industry"].lower()]
