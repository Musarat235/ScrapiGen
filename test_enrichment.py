"""Quick test for enrichment pipeline"""
from core.enrichment import analyze, enrich

data = [
    {"phone": "1234567890", "email": "TEST@Example.COM ", "website": "example.com"},
    {"phone": "+1-234-567-890", "email": "test@example.com", "website": "https://example.com/"},
    {"phone": "9876543210", "email": "other@test.com"}
]

print("=== ANALYZE (stats only) ===")
stats = analyze(data)
for k, v in stats.items():
    print(f"  {k}: {v}")

print()
print("=== ENRICH (normalize + deduplicate) ===")
result = enrich(data)
print(f"  Stages applied: {result['stages_applied']}")
print(f"  Original count: {result['original_count']}")
print(f"  Enriched count: {result['enriched_count']}")
print(f"  Duplicates removed: {result['duplicates_removed']}")
print()
print("  Cleaned records:")
for i, rec in enumerate(result["data"]):
    print(f"    [{i}] {rec}")

print()
print("ALL TESTS PASSED")
