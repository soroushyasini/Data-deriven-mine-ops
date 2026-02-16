
## 📐 Data Validation Rules (Automated Alerts)

| Check | Rule | Alert Level |
|---|---|---|
| **K (ore input) grade** | If Au > 5 ppm | 🟡 Flag as high-grade (verify, not error) |
| **K (ore input) grade** | If Au > 20 ppm | 🔴 Verify immediately (possible label error or bonanza) |
| **T (tailings) loss** | If Au > 0.2 ppm | 🔴 Gold loss too high — check leach process |
| **RC (return water)** | If Au > 0.05 ppm | 🔴 Circuit leak — investigate |
| **CR (carbon)** | If Au < 200 ppm | 🟡 Carbon may be exhausted |
| **Tonnage per truck** | If < 15,000 or > 32,000 kg | 🟡 Unusual load — verify |
| **Missing receipt number** | If null | 🟡 Data entry issue |
| **Driver name** | If not in canonical list | 🟡 Possible typo |
| **Sample code format** | If doesn't match regex `^[A-Z]*\d{7,8}[A-Z]*\d*$` | 🔴 Invalid label |


