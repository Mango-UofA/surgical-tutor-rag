# Pre-Deployment Checklist

**Status as of Feb 8, 2026**

---

## ✅ **COMPLETED** (Ready to Deploy)

### Configuration Files
- [x] `backend/railway.json` - Railway build configuration
- [x] `backend/Procfile` - Server start command
- [x] `backend/.railwayignore` - Exclude unnecessary files
- [x] `frontend/netlify.toml` - Netlify build configuration
- [x] `frontend/src/config.js` - API URL configuration
- [x] `frontend/.env.example` - Environment variable template
- [x] `DEPLOYMENT.md` - Complete deployment guide

### Code Status
- [x] Backend FastAPI application functional
- [x] Frontend React/Vite application functional
- [x] CORS middleware configured
- [x] Health check endpoint exists (`/health`)
- [x] Environment variable support via `.env`
- [x] Graceful fallback for optional features (graph, multimodal)

---

## ⚠️ **REQUIRES ACTION BEFORE DEPLOYMENT**

### Critical (Must Fix)
1. **[ ] Upload FAISS Index to Railway**
   - File: `backend/faiss_index.index` (598 chunks)
   - Size: Check with `ls -lh faiss_index.index`
   - Options: Git LFS, Railway volume, or cloud storage (S3/GCS)
   - **Without this:** Query endpoint will fail

2. **[ ] Set Up MongoDB Atlas**
   - Create free M0 cluster
   - Get connection string
   - Add to Railway environment variables
   - **Without this:** Upload/citations won't work

3. **[ ] Get OpenRouter API Key**
   - Sign up at https://openrouter.ai
   - Add to Railway environment variables
   - **Without this:** Answer generation will fail

4. **[ ] Update Frontend API Calls**
   - Replace hardcoded `http://localhost:8000` with `${API_BASE_URL}`
   - Files to check:
     - `frontend/src/components/ChatPanel.jsx`
     - `frontend/src/components/UploadPanel.jsx`
     - `frontend/src/components/QuizPanel.jsx`
     - `frontend/src/components/ImageUploadPanel.jsx`
     - `frontend/src/components/VisualQAPanel.jsx`

### Optional (Can Skip Initially)
5. **[ ] Neo4j AuraDB Setup** (or disable graph features)
   - Create free instance at https://neo4j.com/cloud/aura
   - Update connection credentials
   - OR accept graph features will be disabled

6. **[ ] Git LFS for FAISS Index**
   ```bash
   git lfs install
   git lfs track "backend/faiss_index.index"
   git add .gitattributes
   ```

---

## 🔧 **RECOMMENDED IMPROVEMENTS**

### Before First Deploy
- [ ] Add Python version specification: Create `runtime.txt` with `python-3.12`
- [ ] Pin exact dependency versions in `requirements.txt`
- [ ] Add `.gitignore` for `backend/.env` if not already ignored
- [ ] Test locally with production-like environment variables

### After First Deploy
- [ ] Set up Railway persistent volume for FAISS index
- [ ] Configure custom domain (if needed)
- [ ] Set up monitoring/alerts
- [ ] Add rate limiting to API endpoints
- [ ] Enable HTTPS only (Railway does this by default)

---

## 📝 **DEPLOYMENT STEPS SUMMARY**

1. **MongoDB Atlas** → Get connection string
2. **OpenRouter** → Get API key  
3. **Railway** → Deploy backend + add env vars + upload FAISS index
4. **Netlify** → Deploy frontend + add VITE_API_URL
5. **Test** → Verify all endpoints working

**Estimated Time:** 30-45 minutes

---

## ❌ **BLOCKERS**

### Hard Blockers (Cannot deploy without)
1. FAISS index file (`faiss_index.index`) - Need upload strategy
2. MongoDB connection string - Need Atlas setup
3. OpenRouter API key - Need account

### Soft Blockers (Will degrade functionality)
1. Neo4j credentials - Graph features disabled without
2. Model download time - First request slow (~30s) but not a blocker

---

## 🎯 **NEXT STEPS**

**To deploy TODAY:**
1. Fix Critical items #1-4 above (~30 minutes)
2. Follow `DEPLOYMENT.md` guide
3. Test deployment

**Can deploy WITHOUT:**
- Neo4j (graph features will be disabled)
- Multimodal features (already optional)
- Quiz generation (if MongoDB is set up)

---

## 📊 **Current Status: 70% Ready**

**What works:** ✅  
- Code is deployable
- Configuration files created
- Documentation complete

**What's missing:** ⚠️  
- External services setup (MongoDB, API keys)
- FAISS index upload strategy
- Frontend API URL updates

**Estimated work remaining:** 1-2 hours
