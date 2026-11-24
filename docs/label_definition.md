# Assay label definition

The assay export preserves the `category` sheet's ordinal scores of `0` through `3` and the `binary` sheet's recorded `0` and `1` values. Blanks represent missing observations and stay blank. Each row records the source workbook and which sheets supplied a value. The two scales are retained independently so any later analysis can document how it defined its outcome.

Inventory counts use `binary = 1` only for descriptive reporting. A modeling threshold for `category` remains pending assay-owner confirmation. Clearing on a spot-test plate may reflect several processes, so describe the recorded outcome as spot-test clearing until assay documentation supports a stronger interpretation.

The workbook's unnamed trailing columns and rows with scores but no host ID are listed for review and excluded from the observation table. Preserve the source files for follow-up. Treat assay-derived columns, including historical `virulence_index` and `inhibition_efficiency`, as outcomes and keep them out of feature inputs.
