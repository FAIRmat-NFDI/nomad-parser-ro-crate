# GUI Pluralization Error Fix

## 🐛 **Problem**
The NOMAD GUI was throwing a pluralization error:
```
Error: The word Data management is not in the dictionary, please add it.
```

## 🔍 **Root Cause**
Our RO-Crate parser entry point was configured with:
```python
code_category = 'Data management'
```

The NOMAD GUI's `pluralize()` function in `/nomad/gui/src/utils.js` has a limited dictionary of known words that can be pluralized. When the GUI tries to pluralize "Data management", it fails because:

1. The dictionary only contains single words, not phrases
2. "Data management" (two words) is not in the dictionary
3. The pluralization function throws an error for unknown words

## ✅ **Solution**
Changed the parser configuration to use `None` instead of a problematic category:

### Before:
```python
code_category: str | None = 'Data management'
metadata = {
    'codeCategory': 'Data management',
    # ...
}
```

### After:
```python
code_category: str | None = None
metadata = {
    'codeCategory': None,
    # ...
}
```

## 📋 **Standard Categories Available**
Based on analysis of other parsers in the NOMAD ecosystem:
- `'Atomistic code'` - Electronic structure/DFT codes
- `'MD code'` - Molecular dynamics codes
- `'Workflow manager'` - Workflow management systems
- `None` - Appears in "Miscellaneous" category

## 🎯 **Result**
- ✅ GUI no longer crashes with pluralization error
- ✅ Parser appears in "Miscellaneous" category
- ✅ All functionality preserved
- ✅ Tests updated and passing

## 🔧 **Alternative Solutions**
If we wanted to keep a category, we could have:
1. **Used a single word**: `'Parser'` or `'Metadata'`
2. **Used an existing category**: `'Workflow manager'` (closest match)
3. **Added to GUI dictionary**: Modify `utils.js` to include "management"

We chose the `None` approach for simplicity and to avoid dependency on GUI dictionary changes.