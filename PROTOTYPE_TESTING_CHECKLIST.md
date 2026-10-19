# xG Insight - Prototype Testing Checklist

Tester: Michael
Branch: test/michael-integration

## Automated Tests Completed
- PASS: Django backend tests (2/2)
- PASS: Analytics preprocessing tests (9/9)
- Total: 11/11 passed

## Prototype Integration Tests
- [ ] TC-01: Upload a valid CSV file
- [ ] TC-02: Verify required shot data fields
- [ ] TC-03: Verify x/y coordinates range from 0 to 100
- [ ] TC-04: Verify shots are saved in MongoDB
- [ ] TC-05: Verify xG values appear correctly
- [ ] TC-06: Verify blank xG values are handled
- [ ] TC-07: Verify shots appear on the shot map
- [ ] TC-08: Verify match summary displays correctly
- [ ] TC-09: Test the complete CSV-to-summary workflow

## Current Status
Automated tests passed.
Full prototype integration testing is pending.
