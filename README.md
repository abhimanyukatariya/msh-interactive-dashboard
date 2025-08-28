# MSH Interactive Dashboard (Streamlit)

## How to run
1. Open Terminal and go to the unzipped folder:
   ```bash
   cd msh-interactive-dashboard
   ```
2. Create a virtual env (optional but recommended):
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the app:
   ```bash
   streamlit run app.py
   ```
5. Your browser will open at http://localhost:8501

## Data
- The app reads `data/Cohort2_startups.xlsx` (sheet: **Cohort 2 Startups**).
- To update data, replace the file with a newer version keeping the same sheet name.

