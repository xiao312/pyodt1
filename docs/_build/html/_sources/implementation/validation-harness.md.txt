# Validation harness

The main comparison tool is:

- `scripts/compare_one_step.py`

## Current comparisons

### Fixed accepted-eddy path
- `BsKd`
- `BProb`
- `BEddy`

### Sampled eddy path
- `BSeeds`
- `BLenProb`
- `BLength`
- sampled `L3`, `L`, `M`
- final RNG state

## Usage

```bash
python scripts/compare_one_step.py
```
