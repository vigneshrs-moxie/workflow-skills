# The text tier

A wireframe written in the reply, for the first round of "is this the right shape?" when a page would be too much. Nothing is built; when the shape is agreed, the same screens become a sketch, lo-fi or hi-fi page.

Use it when the user asks for a quick sketch in chat, wants to iterate on structure in a few exchanges first, or when there's no screen to draw yet (an idea with three possible shapes). Don't use it for a review that others will read, for states, or for anything the user will pick between visually.

## Notation

One block per screen, in flow order, in a fenced code block. Plain characters only.

```
SCREEN 1 · Invoices list                                      /invoices?status=Overdue
──────────────────────────────────────────────────────────────────────────────
[ Acme Billing ]   Dashboard   *Invoices*   Customers   Reports   Settings
──────────────────────────────────────────────────────────────────────────────
Invoices                                   [Actions ▾]  (Download CSV)*  [New invoice]
                                                        ^1
(All) (Draft) (Sent) [Overdue] (Paid)   [ search: palms ]  [ Last 30 days ▾ ]
                                                           ^2
| Number   | Customer           | Issued | Due    | Status  | Amount    |
| INV-1042 | Desert Palms HOA   | Sep 12 | Oct 12 | Overdue |   $480.00 |
| INV-1037 | Palms Dental Group | Sep 8  | Oct 8  | Overdue | $1,250.00 |

1  Download CSV sits next to New invoice, plain, so New invoice stays the main action.
2  The file follows these filters: status, search, date range.
States: No matches (button disabled, "No invoices to download with these filters.") · Viewer (no button)
Goes to: Confirm download (Download CSV)
```

| Thing | Write it as |
|---|---|
| Top nav / tabs | `Item   *Active*   Item` |
| Primary button | `[Label]` |
| Secondary button | `(Label)` |
| New in this feature | a `*` after it: `(Download CSV)*` |
| Removed | `~~Label~~` |
| Input, select | `[ placeholder ]`, `[ value ▾ ]` |
| Checkbox, radio | `[x] Label`, `( ) Label` |
| Table | pipe rows, header first |
| Image or chart | `[ image: what it shows ]` |
| Dialog, sheet, menu | its own screen block, titled `DIALOG · …` |
| Pin | `^n` under the thing, then `n  note` below the screen |
| Empty / loading / error | a `States:` line naming each, with what changes |
| Where it leads | a `Goes to:` line: screen name (the control) |

A design choice is two short blocks side by side in text, `OPTION A · name` and `OPTION B · name`, each with one Good and one Watch line, and which is recommended.

End with **Questions to settle**: `Decide:` and `Assumed:` lines, the same ones the page would carry.

## After the text round

Keep the screen names, pin numbers and wording when you draw the page: they become the section keys, pins and callouts, so what was agreed in text is what's reviewed on the page.
