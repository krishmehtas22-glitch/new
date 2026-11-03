BillSync UI + read-only Tally Masters & Units snapshot (source-only update)

CONTENTS
- Invoice_Desktop.py — modified desktop UI; existing original methods retained.
- tally_master_reader.py — separate read-only Tally XML master/unit snapshot adapter.

INSTALL (with original files backed up)
1. Close BillSync. Back up your current Invoice_Desktop.py.
2. Copy BOTH Python files into the SAME directory as your existing Invoice_Desktop.py.
3. Keep your existing Common_Rules folder exactly as it is. Do not overwrite it.
4. Start the Python source through your normal development setup (or rebuild the .exe).
   The compiled InvoiceReader.exe will NOT change just by copying Python files.
5. Open a company in TallyPrime and enable its HTTP/XML server (default 9000).
6. Click 'Connect to Tally', choose a loaded company.
7. Click 'Import Masters & Units from Tally' to save a JSON snapshot at
   <data root>/.invoice_app/tally_master_snapshots/<company>_<timestamp>.json.

IMPORTANT
- No Tally master is created, replaced, deleted or edited by the new feature.
- BillSync's existing Units.xml -> Masters.xml -> Sales_Vouchers.xml workflow is unchanged.
- No new snapshot is used to populate or affect the existing BillSync master logic.
- Snapshot coverage depends on available Tally XML collections; empty categories
  are flagged for verification and do not prove the company contains no masters.
- The imported data may include sensitive business details. Store it securely.
- This is NOT a full project / executable. The original Common_Rules directory
  and development dependencies are required to run it.
- The ttk widgets have native, slightly softened button styling rather than
  custom-drawn true rounded corners.

CHECKED: Python syntax compilation for both files.
NOT CHECKED: GUI runtime against missing Common_Rules, or a real TallyPrime server.
