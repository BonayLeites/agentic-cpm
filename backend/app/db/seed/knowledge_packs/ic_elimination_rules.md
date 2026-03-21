# Intercompany Elimination Procedure — NikkoGroup

## Matching Process

IC transactions are matched using a three-tier process:

1. **Invoice Number Match**: The primary matching key is the IC invoice number. Both the sending and receiving entity must reference the same invoice number in their GL postings. Matched pairs are auto-eliminated.

2. **Amount Tolerance Match**: For transactions without matching invoice numbers, the system attempts to match by amount within a tolerance band. The tolerance is set at 2% of the transaction value or JPY 1M, whichever is smaller. Transactions matched within tolerance are flagged for controller review but are auto-eliminated.

3. **Entity Pair and Period Match**: Remaining unmatched transactions are grouped by entity pair and period. The Group Controller reviews these manually and determines whether the difference is due to timing (cut-off), FX translation, or a genuine error.

## Cut-off Rules

Transactions must be recorded in the same period by both entities. If the sending entity records in month M and the receiving entity records in month M+1, this constitutes a cut-off timing difference. The receiving entity must either: (a) post an accrual in month M, or (b) re-date the transaction to align with the sender. Cut-off differences exceeding 5 business days require escalation.

## Elimination Journal Entries

IC elimination entries are posted at the group level as consolidation adjustments. They do not affect individual entity trial balances. All elimination entries must balance to zero across the group.
