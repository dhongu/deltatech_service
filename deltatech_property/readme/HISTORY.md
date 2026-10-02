## 19.0.1.0.3 (2026-10-02)

- The building area fields referenced a compute method that did not exist, so they
  always stayed at zero. The area of each room usage (office, kitchen, garage, ...) is now
  the sum of the rooms of that usage; the total cleaned area is administrative +
  industrial + external and the total derating area is internal + external. The
  administrative and industrial cleaned areas and the internal derating area become
  editable inputs (PROPERTY-001).

## 19.0.1.0.2 (2026-09-30)

- Own module icon in the flat style of the other modules.
