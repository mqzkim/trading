# Deferred Items -- Phase 05

## Pre-existing Issues

1. **test_screener.py::TestDuckDBSignalStoreRepository::test_save_persists_signal**
   - DuckDB `scores` table does not exist (test fixture references non-existent table)
   - Error: `CatalogException: Table with name scores does not exist!`
   - Discovered during: 05-01 verification
   - Impact: 1 test in test_screener.py fails; does not affect other tests
