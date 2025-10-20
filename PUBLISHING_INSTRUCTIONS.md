# Publishing NexPyLib to PyPI

## ✅ Pre-Publishing Checklist

- [x] Version updated to 0.1.0
- [x] All 611 tests passing
- [x] Documentation complete
- [x] Package built successfully
- [x] Twine validation passed

---

## 🧪 Option 1: Test with TestPyPI (RECOMMENDED)

### Step 1: Create TestPyPI Account (if you don't have one)
1. Go to: https://test.pypi.org/account/register/
2. Verify your email address

### Step 2: Create API Token for TestPyPI
1. Go to: https://test.pypi.org/manage/account/token/
2. Click "Add API token"
3. Set scope to "Entire account" (or specific to nexpylib if it exists)
4. Copy the token (starts with `pypi-...`)
5. Save it securely - you won't see it again!

### Step 3: Upload to TestPyPI
```bash
cd "/Users/benedikt/Documents/8 Programmierung/Python libraries/nexpylib"
source .venv/bin/activate
twine upload --repository testpypi dist/*
```

When prompted:
- **Username:** `__token__`
- **Password:** Your TestPyPI API token (paste it)

### Step 4: Test Installation from TestPyPI
```bash
# Create a test environment
python3 -m venv test_env
source test_env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple nexpylib

# Test it
python3 -c "import nexpy; print(nexpy.__version__)"
```

**If this works, proceed to PyPI!**

---

## 🚀 Option 2: Publish to PyPI (Production)

### Step 1: Create PyPI Account (if you don't have one)
1. Go to: https://pypi.org/account/register/
2. Verify your email address
3. **Enable 2FA (Two-Factor Authentication)** - Required for uploading!

### Step 2: Create API Token for PyPI
1. Go to: https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Set scope to "Entire account" (you can narrow it after first upload)
4. Copy the token (starts with `pypi-...`)
5. **Save it securely** - you won't see it again!

### Step 3: Upload to PyPI
```bash
cd "/Users/benedikt/Documents/8 Programmierung/Python libraries/nexpylib"
source .venv/bin/activate
twine upload dist/*
```

When prompted:
- **Username:** `__token__`
- **Password:** Your PyPI API token (paste it)

### Step 4: Verify Upload
1. Visit: https://pypi.org/project/nexpylib/
2. Check that version 0.1.0 appears correctly
3. Verify README renders properly

### Step 5: Install and Test
```bash
# In a fresh environment
pip install nexpylib

# Test it
python3 -c "import nexpy; print(nexpy.__version__)"
```

---

## 📝 After Publishing

1. **Create a Git Tag:**
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

2. **Create GitHub Release:**
   - Go to your GitHub repository
   - Click "Releases" → "Create a new release"
   - Select tag `v0.1.0`
   - Title: `v0.1.0 - First Public Release`
   - Description: Copy content from `RELEASE_NOTES_v0.1.0.md`
   - Attach the wheel and tarball from `dist/`

3. **Update README Badge (optional):**
   ```markdown
   [![PyPI version](https://badge.fury.io/py/nexpylib.svg)](https://badge.fury.io/py/nexpylib)
   ```

4. **Announce on Social Media/Communities** (if desired)

---

## 🔒 Security Tips

1. **Never commit your API tokens to Git!**
2. **Store tokens securely** (password manager, keyring)
3. **Use project-scoped tokens** after first upload
4. **Revoke and regenerate tokens periodically**

---

## 🐛 Troubleshooting

### Error: "403 Forbidden"
- Check that your API token is correct
- Ensure username is `__token__` (with underscores)
- Verify your account has upload permissions

### Error: "400 Bad Request - File already exists"
- You cannot re-upload the same version
- Increment the version number in `pyproject.toml` and `_version.py`
- Rebuild: `python -m build`
- Upload again

### Error: "Invalid distribution"
- Run: `twine check dist/*`
- Fix any validation errors
- Rebuild: `rm -rf dist/ && python -m build`

### Package page looks wrong
- Check `README.md` renders correctly on GitHub
- Ensure `pyproject.toml` metadata is complete
- Wait a few minutes for PyPI to process

---

## 📚 Resources

- **PyPI:** https://pypi.org/
- **TestPyPI:** https://test.pypi.org/
- **Python Packaging Guide:** https://packaging.python.org/
- **Twine Documentation:** https://twine.readthedocs.io/

---

**Good luck with your first PyPI release! 🎉**

