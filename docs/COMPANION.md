# Connect the staffing and charge nurse dashboard

Source repository: [charge-nurse-handoff-dashboard](https://github.com/true2thecore-cloud/charge-nurse-handoff-dashboard). That repository owns staffing assignment calculations, Forms mappings and the charge nurse dashboard. This companion consumes snapshots and adds an **Operations View**.

## Staffing

1. Use the companion's `scripts/ExportStaffing.ts` on the staffing workbook.
2. Supply `localDate` as `YYYY-MM-DD` and choose `next-business-day`, `same-date` or `explicit-date`.
3. In next-business-day mode, Friday advances to Monday. The source tab's B1 date must match. No different tab is silently substituted.
4. Save the returned JSON as a `.staffing.json` file. Import it through the workbench, watcher, or CLI:

```powershell
python -m hospital_ops --config config/site.local.json snapshot staffing data/staffing.json
```

The contract is version 1, `sourceSheet`, `staffingDate`, `capturedUtc`, and `values` containing exactly 46 rows by 12 strings. A1:L46 is retained, including later shifts in K:L. Staffing-date labels and capture times remain visible. The core does not treat the imported date as “today” when it is actually next Monday, and it does not recompute hours or infer role headcounts from free text.

The companion's base business-day rule skips weekends, not holidays. To honor a holiday, use its explicit-date option. This core's `staffing-date --holiday` helper can calculate an explicit target for the flow:

```powershell
python -m hospital_ops staffing-date 2027-01-22 --holiday 2027-01-25
```

This returns `2027-01-26`. The helper does not change the companion script by itself; pass the calculated date into `explicitDate` with mode `explicit-date`.

## Handoff

1. Run the companion's `scripts/ExportHandoff.ts` on the workbook containing the configured Forms response table.
2. Save the result as `.handoff.json`.
3. Import it through the same workflow.

The contract is `{ "version": 1, "headers": ["..."], "rows": [["..."]] }`. The source field names are retained. The HTML view shows up to 30 records in source order and does not claim the last row is the latest response. The existing charge dashboard continues to select and render the latest submission according to its own verified timestamp rules.

Snapshots provide context. They do not automatically become reviewed meeting signals or silently assign staff to new locations.

## Operations back into the shared workbook

Import the core's report JSON with `scripts/ImportOperationsBrief.ts`. It creates or updates only a marked, dedicated Operations View. If an existing sheet has unrelated contents, it stops. Keep the default name or choose a new dedicated sheet.

The first repo does not need to be changed. Create the intake/export and publication steps in your tenant, with one coordinated writer for the combined Excel workbook. A repository link alone does not authenticate or connect files.

## Readiness workbook extension (version 2)

The full readiness workflow adds executive/current views and immutable daily records. Keep the dashboard scripts and export contracts unchanged. Supply relevant snapshot evidence to a reviewer and map the validated fields into version-2 records using [the readiness profile](../config/readiness.example.json). Preserve the assignment date and receipt time; a new snapshot alone is not a confirmed risk. [Readiness quickstart](READINESS-QUICKSTART.md).
