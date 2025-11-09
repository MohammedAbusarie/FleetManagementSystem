# Car Module CRUD Manual Test Plan

## Overview
- Scope: End-to-end manual validation of car creation, retrieval (listing/detail), update, and deletion flows in the admin panel.
- Goals: Confirm that business rules, hierarchical validations, mandatory record requirements, multi-file handling, and edge cases behave correctly without regressing existing functionality.
- Out of scope: API/export integrations, background schedulers, and RBAC variations beyond the specified prerequisites.

## Preconditions
- Test user: Admin or user with explicit `cars:create/read/update/delete` permissions.
- Supporting data:
  - At least one sector, administrative unit, department, and division available (dummy records such as `غير محدد` are acceptable).
  - Reference dropdown values (car class, manufacturer, model, activity, contract type, etc.) populated as needed.
  - Sample maintenance categories and regions available; new regions can be created inline via the UI.
- Browser cache cleared for consistent asset loading; disable auto-translation to keep Arabic labels intact.
- Dummy media path `dummy_media/cars` available for image uploads if you want ready-made assets.

## Shared Test Data References
| Field | Value 1 (Primary) | Value 2 (Alternate) |
| --- | --- | --- |
| `fleet_no` | `FLEET-9011` | `FLEET-9012` |
| `plate_no_en` | `ABC-9011` | `ABC-9012` |
| `plate_no_ar` | `أ ب ج ٩٠١١` | `أ ب ج ٩٠١٢` |
| `ownership_type` | `owned` | `leased` |
| `status` | `active` | `under_maintenance` |
| License dates | `start: 2025-01-01`, `end: 2026-01-01` | `start: 2024-05-01`, `end: 2025-05-01` |
| Inspection dates | `start: 2025-02-01`, `end: 2026-02-01` | `start: 2024-06-01`, `end: 2025-06-01` |
| Region tags | `المنطقة المركزية`, `المدينة الجديدة` | — |

> Adjust numbers if conflicts with existing data. Ensure `plate_no_en` remains uppercase and `plate_no_ar` uses Arabic numerals.

## Test Cases

### Creation (C)

**C1 – Happy Path Creation with Minimum Mandatory Data**  
Objective: Verify creation succeeds with required fields, single license/inspection record, and default hierarchy auto-fill.  
Preconditions: Dummy `غير محدد` hierarchy records exist.  
Test Data: Use `fleet_no`/`plate` primary values, `status=active`, one license record, one inspection record, region `المنطقة المركزية`, upload `dummy_media/cars/car/car_1.jpg`.  
Steps:
1. Navigate to car list → click “إضافة سيارة”.
2. Fill required Arabic fields plus English identifiers (ensure uppercase for English plate). Leave optional fields empty.
3. Confirm sector/administrative unit/department auto-populate with dummy defaults; keep them.
4. Add one license and one inspection row with provided dates.
5. Add visited region tag.
6. Upload one JPG image via multi-upload field.
7. Submit.  
Expected:
- Success toast in Arabic.
- Redirect to car list; newly created car appears with correct fleet number.
- Detail view shows uploaded image, license, inspection, and region.

**C2 – Under Maintenance Requires Maintenance Entry**  
Objective: Ensure selecting `status=under_maintenance` enforces maintenance formset validation.  
Preconditions: Existing car from C1 or use alternate data.  
Steps:
1. Begin new car creation with alternate identifiers.
2. Set status to `تحت الصيانة` (under_maintenance) but do not add maintenance entry; fill license/inspection as usual.
3. Submit; expect validation error pointing to maintenance section.
4. Add maintenance record: set description, date, and cost; re-submit.  
Expected:
- Initial submission blocked with validation error (Arabic message).
- After adding maintenance record, creation succeeds and maintenance appears in detail timeline.

**C3 – Unique Identifier Enforcement**  
Objective: Confirm duplicate `fleet_no`/`plate_no_en` are rejected.  
Preconditions: Car from C1 exists.  
Steps:
1. Open create form.
2. Reuse `fleet_no` and `plate_no_en` from existing car; change other fields.
3. Submit.  
Expected:
- Form shows field-level validation messages in Arabic for both duplicates; record is not saved.

**C4 – Hierarchy Consistency Validation**  
Objective: Ensure division must align with chosen administrative unit.  
Test Data: Pick sector A with division tied to a different administrative unit B.  
Steps:
1. Open create form.
2. Select valid sector (not dummy).
3. Select administrative unit belonging to that sector.
4. Manually choose division from another administrative unit via select2 search (if available) or intentionally clear admin unit and pick mismatched division.
5. Submit.  
Expected:
- Validation error stating division does not belong to selected administrative unit.  
- When corrected (select matching division), submission succeeds.

**C5 – File Upload Validation (Invalid Type & Large Image)**  
Objective: Validate non-image files are rejected and large valid images upload successfully.  
Steps:
1. Start create form (you can cancel later).
2. Attempt to upload a `.pdf` or `.txt` file for car image.  
3. Submit form (even with incomplete fields) to trigger validation.  
4. Replace with a large JPG (≥8 MB) from local test assets; ensure upload completes.  
Expected:
- PDF/TXT rejected with Django/Arabic error message before save.  
- Large JPG accepted; preview/thumbnail appears after upload.

**C6 – Dynamic Region Tag Creation**  
Objective: Confirm ad-hoc region tags persist.  
Steps:
1. Create car and in visited regions input, type new region `منطقة الساحل الغربي` and press Enter.
2. Submit with other required fields.  
Expected:
- Car detail shows the new region.
- Subsequent car creation shows the new region as selectable (autocomplete).

### Retrieval (R)

**R1 – List View Search & Pagination**  
Objective: Ensure search filters results without breaking pagination.  
Steps:
1. Visit car list; note initial count.  
2. Use search dropdown `رقم الأسطول`, enter `FLEET-9011`, search.  
3. Clear search; navigate to next page, confirm navigation works and summary matches.  
Expected:
- Search displays only matching car(s).  
- Pagination controls remain responsive and preserve filters.

**R2 – Sorting**  
Objective: Validate sort toggles between ascending/descending.  
Steps:
1. On car list, click column header for creation date (or use sort dropdown if present).  
2. Toggle twice, confirm order reverses each time.  
Expected:
- Rows reorder correctly with visual indicator (arrow or active state).

**R3 – Detail View Completeness**  
Objective: Confirm detail page renders full data set.  
Steps:
1. Open car created in C1.  
2. Verify sections: core info, hierarchy, license history, inspection history, maintenance, images, regions.  
3. Download each image using provided links to ensure they are retrievable.  
Expected:
- All data accurate; image download works; dates formatted correctly in Arabic locale.

### Update (U)

**U1 – Edit Core Fields**  
Objective: Ensure standard updates persist.  
Steps:
1. Open car from C1 → click edit.  
2. Change status to `متوقف مؤقتًا` (if available), update driver, location description, and contract type.  
3. Submit.  
Expected:
- Success toast; list reflects updated status; audit log entry created (verify via `logs/django.log` if accessible).

**U2 – License & Inspection Record Maintenance**  
Objective: Validate inline formsets allow add/edit/delete while enforcing minimum one record.  
Steps:
1. Edit car.  
2. Add new license record with future dates, mark old record for deletion (check delete checkbox).  
3. Repeat for inspection.  
4. Submit.  
Expected:
- Form saves; detail view shows only the new records; no validation error for minimum count.

**U3 – Image Management**  
Objective: Confirm new uploads append and deletions remove files from storage.  
Steps:
1. Edit car; upload two additional images.  
2. Submit; verify detail shows all images.  
3. Re-open edit; mark one existing image for deletion using UI control (sets `images_to_delete`).  
4. Submit; verify deleted image no longer appears, other images intact.  
5. Optionally check filesystem `media/cars` for removed file.  
Expected:
- Added images saved; deleted image removed from UI and filesystem; timestamps updated.

**U4 – Status Switch to Under Maintenance Without Record**  
Objective: Confirm update enforces maintenance record when switching status.  
Steps:
1. Edit car with no maintenance records.  
2. Change status to `تحت الصيانة`, leave maintenance formset empty.  
3. Submit; expect validation error.  
4. Add maintenance record, resubmit.  
Expected:
- Update blocked until maintenance entry provided; on success, maintenance timeline updated.

### Deletion (D)

**D1 – Confirm Delete Workflow**  
Objective: Ensure delete confirmation and cascade behave as expected.  
Steps:
1. From list view, select car created in C2 (keep original from C1 for reuse).  
2. Click delete → confirm dialog.  
3. Submit.  
Expected:
- Success toast; car removed from list; associated images and inline records removed from database/storage.

**D2 – Permission Enforcement (Optional)**  
Objective: Validate users without delete permission are blocked.  
Preconditions: Secondary user lacking `cars:delete`.  
Steps:
1. Log in as restricted user.  
2. Navigate to car detail; ensure delete action hidden/disabled.  
3. Attempt direct access to delete URL; expect 403 or redirect with message.  
Expected:
- UI hides delete option; direct access denied with Arabic error message.

### Cross-Cutting Checks
- Verify toast/alert messages remain fully in Arabic per UI requirements.
- Observe logging: after create/update/delete, confirm entries in audit logs if accessible.
- After each major operation, refresh list to ensure caching (if enabled) does not show stale data.

## Post-Test Actions
- Record actual outcomes in `docs/test_results_cars_crud.md` with pass/fail notes.
- Re-seed or remove test data to keep environment clean (delete any temporary regions or revert status as needed).

