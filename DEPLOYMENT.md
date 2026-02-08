# Deployment Guide: Railway + Netlify

## Prerequisites Checklist

Before deploying, you need:

### ✅ **Accounts**
- [ ] Railway account (https://railway.app)
- [ ] Netlify account (https://netlify.com)
- [ ] MongoDB Atlas account (free tier)
- [ ] OpenRouter API key (or OpenAI API key)
- [ ] (Optional) Neo4j AuraDB account

### ✅ **Services to Set Up**
1. **MongoDB Atlas** - Free M0 cluster
2. **Neo4j AuraDB** (Optional) - Free tier or disable graph features
3. **API Keys** - OpenRouter or OpenAI

---

## Part 1: Backend Deployment (Railway)

### Step 1: Prepare MongoDB Atlas

1. Go to https://www.mongodb.com/cloud/atlas
2. Create free M0 cluster
3. Create database user
4. Whitelist Railway IPs (or use 0.0.0.0/0 for dev)
5. Get connection string:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/surgical_tutor
   ```

### Step 2: Deploy to Railway

1. **Push code to GitHub** (if not already)
   ```bash
   git add .
   git commit -m "Add deployment configuration"
   git push
   ```

2. **Create Railway Project**
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Select `backend` directory as root

3. **Set Environment Variables**
   
   In Railway dashboard → Variables tab:
   ```env
   PORT=8000
   MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/surgical_tutor
   OPENAI_API_KEY=sk-or-v1-your-openrouter-key
   OPENAI_BASE_URL=https://openrouter.ai/api/v1
   OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct:free
   FAISS_INDEX_PATH=./faiss_index.index
   BIOCLINICALBERT_MODEL=emilyalsentzer/Bio_ClinicalBERT
   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-neo4j-password
   SCISPACY_MODEL=en_core_sci_md
   ```

4. **Configure Build**
   - Railway auto-detects Python
   - Uses `railway.json` configuration
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Add FAISS Index**
   
   **Problem:** `faiss_index.index` (with 598 chunks) is too large for Git
   
   **Solutions:**
   
   **Option A: Upload via Railway Volume**
   ```bash
   # After first deploy, use Railway CLI
   railway login
   railway link
   railway run bash
   # Then upload faiss_index.index manually
   ```
   
   **Option B: Rebuild Index on Startup** (Recommended)
   - Add startup script to check if index exists
   - If not, download from cloud storage (S3/GCS)
   - Or rebuild from source documents
   
   **Option C: Git LFS** (if < 2GB)
   ```bash
   git lfs install
   git lfs track "backend/faiss_index.index"
   git add .gitattributes
   git add backend/faiss_index.index
   git commit -m "Add FAISS index with LFS"
   ```

6. **Generate Domain**
   - Railway auto-generates: `https://your-project.up.railway.app`
   - Note this URL for frontend configuration

7. **Test Deployment**
   ```bash
   curl https://your-project.up.railway.app/health
   # Should return: {"status": "ok"}
   ```

---

## Part 2: Frontend Deployment (Netlify)

### Step 1: Update API Configuration

1. **In your local code:**
   ```bash
   # Update frontend to use Railway backend
   cd frontend
   ```

2. **Update API calls to use config.js**
   
   In each component that calls API (ChatPanel, UploadPanel, etc.):
   ```javascript
   import { API_BASE_URL } from '../config';
   
   // Change from:
   axios.post('http://localhost:8000/query', ...)
   
   // To:
   axios.post(`${API_BASE_URL}/query`, ...)
   ```

### Step 2: Deploy to Netlify

1. **Push Updated Code**
   ```bash
   git add .
   git commit -m "Update API configuration for production"
   git push
   ```

2. **Create Netlify Site**
   - Go to https://app.netlify.com
   - Click "Add new site" → "Import existing project"
   - Connect to GitHub
   - Select your repository
   - **Base directory:** `frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `dist`
   - Click "Deploy"

3. **Set Environment Variable**
   
   In Netlify dashboard → Site settings → Environment variables:
   ```env
   VITE_API_URL=https://your-railway-backend.up.railway.app
   ```

4. **Trigger Redeploy**
   - Go to Deploys tab
   - Click "Trigger deploy" → "Clear cache and deploy site"

5. **Test**
   - Open your Netlify URL: `https://your-site.netlify.app`
   - Should connect to Railway backend

---

## Part 3: Update Backend CORS

After Netlify deployment, restrict CORS to your domain:

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-site.netlify.app",
        "http://localhost:5173",  # Keep for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Expected Deployment Times

- **Railway Backend:** 5-10 minutes (first deploy) + 2-5 minutes (model downloads)
- **Netlify Frontend:** 2-3 minutes
- **Total:** ~15-20 minutes

---

## Known Issues & Solutions

### Issue 1: FAISS Index Missing
**Symptom:** 500 errors on /query endpoint  
**Solution:** Upload faiss_index.index via Railway volume or rebuild on startup

### Issue 2: Long Cold Start
**Symptom:** First request takes 30+ seconds  
**Solution:** BioClinicalBERT downloads on first run (~500MB). Subsequent requests fast.

### Issue 3: Neo4j Auth Errors
**Symptom:** Graph features fail  
**Solution:** Either fix Neo4j AuraDB connection OR disable graph features (system falls back to vector-only)

### Issue 4: MongoDB Connection Fails
**Symptom:** Upload/citation features don't work  
**Solution:** Verify MongoDB Atlas IP whitelist includes Railway IPs or use 0.0.0.0/0

---

## Cost Estimate

- **Railway:** $5/month (Hobby plan) - includes 8GB RAM, 8 vCPU
- **Netlify:** Free (100GB bandwidth/month sufficient for demo)
- **MongoDB Atlas:** Free (M0 cluster - 512MB)
- **Neo4j AuraDB:** Free (limited) or $65/month (professional)
- **OpenRouter API:** ~$0.015 per 1K tokens (very cheap for testing)

**Total:** $5-10/month minimum

---

## Post-Deployment Checklist

- [ ] Backend health check returns 200: `/health`
- [ ] Frontend loads and connects to backend
- [ ] Can upload PDFs successfully
- [ ] Can query and get responses
- [ ] FAISS retrieval working (check response includes context)
- [ ] MongoDB storing citations (check `/citations` endpoint)
- [ ] (Optional) Neo4j graph features working or gracefully disabled

---

## Monitoring

**Railway:**
- Check logs: Railway dashboard → Deployments → View logs
- Monitor CPU/memory usage
- Set up alerts for errors

**Netlify:**
- Check build logs
- Monitor bandwidth usage
- Check function logs (if using serverless)

---

## Need Help?

Common debugging commands:
```bash
# Railway logs
railway logs

# Check Railway environment
railway vars

# Local testing with production env
railway run python app/main.py
```
