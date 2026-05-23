from utils import calculate_match_score, extract_skills, extract_text_from_pdf
import streamlit as st

st.set_page_config(page_title="Resume Screener", layout="wide", page_icon=":mag_right:")

# --- styling ---
st.markdown(
    """
    <style>
    :root { --bg:#0b1220; --panel:#0f1720; --muted:#94a3b8; --accent:#6366f1; --accent2:#06b6d4; }
    html, body, .stApp {background:var(--bg); color:#e6eef6}
    .app-title {font-size:30px; font-weight:800; color:linear-gradient(90deg,#fff,#c7d2fe);} 
    .stApp > .main > .block-container {padding:28px 48px}
    .card {background:var(--panel); padding:16px; border-radius:12px; box-shadow:0 6px 18px rgba(2,6,23,0.6); border:1px solid rgba(255,255,255,0.02)}
    .skill-chip {display:inline-block; margin:4px 8px 4px 0; padding:6px 10px; border-radius:999px; background:rgba(99,102,241,0.12); color:#c7d2fe; font-size:13px}
    .skill-chip.matched {background:rgba(16,185,129,0.12); color:#86efac}
    .skill-chip.missing {background:rgba(239,68,68,0.06); color:#fca5a5}
    .score-strong {color:#34d399; font-weight:800}
    .score-medium {color:#f59e0b; font-weight:800}
    .score-low {color:#fb7185; font-weight:800}
    .stAlert {background:#123; color:#cfe8ff}
    .big-text {font-size:15px; color:#cbd5e1}
    textarea[aria-label="Paste Job Description"]{min-height:180px}
    .css-1d391kg {background:var(--panel)}
    /* file uploader */
    .stFileUploader>div>div{background:transparent}
    .stButton>button {background: linear-gradient(90deg,var(--accent),var(--accent2)); color:white; border:none}
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns([3,1])
with col1:
    st.markdown('<div class="app-title">Resume Screening System 🤖</div>', unsafe_allow_html=True)
    st.write("Upload your resume and paste the job description to get a match score.")
with col2:
        # Inline SVG logo to avoid external file issues (renders crisply at any size)
        LOGO_SVG = '''
        <svg width="140" height="140" viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="g" x1="0" x2="1">
                    <stop offset="0%" stop-color="#6366f1" />
                    <stop offset="100%" stop-color="#06b6d4" />
                </linearGradient>
            </defs>
            <rect rx="16" width="140" height="140" fill="#0f172a" />
            <g transform="translate(20,18)">
                <circle cx="50" cy="38" r="28" fill="url(#g)" />
                <text x="50" y="44" font-size="18" text-anchor="middle" fill="#fff" font-family="Arial, sans-serif">RS</text>
            </g>
            <text x="70" y="100" font-size="14" fill="#fff" font-family="Arial, sans-serif">Resume</text>
            <text x="70" y="118" font-size="14" fill="#fff" font-family="Arial, sans-serif">Screener</text>
        </svg>
        '''
        st.markdown(LOGO_SVG, unsafe_allow_html=True)

st.info("The first semantic match may take a few seconds while the BERT model loads.")


def show_score(score):
    pct = round(score * 100, 2)
    st.progress(min(int(pct), 100))
    if score > 0.7:
        st.markdown(f"<div class=\"score-strong\">🔥 Strong Match: {pct}%</div>", unsafe_allow_html=True)
    elif score > 0.4:
        st.markdown(f"<div class=\"score-medium\">⚡ Moderate Match: {pct}%</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class=\"score-low\">❌ Low Match: {pct}%</div>", unsafe_allow_html=True)


def explain_result(score, missing_skills):
    if score > 0.7:
        st.write("This candidate is a strong fit for the role.")
    elif score > 0.4:
        st.write("Candidate partially matches but lacks some key skills.")
    else:
        st.write("Candidate is not a strong match for this role.")

    if missing_skills:
        st.write("Missing important skills:", ", ".join(missing_skills))

resume_files = st.file_uploader("Upload Resume (PDF)", type=["pdf"], accept_multiple_files=True)
jd_text = st.text_area("Paste Job Description")

if resume_files:
    # If multiple resumes uploaded, rank them
    if jd_text and jd_text.strip() and len(resume_files) > 1:
        st.info("Ranking multiple resumes using semantic + skill coverage.")
        results = []
        with st.spinner("Computing scores for resumes..."):
            for f in resume_files:
                resume_text = extract_text_from_pdf(f)
                if not resume_text:
                    continue
                semantic_pct = calculate_match_score(resume_text, jd_text)
                semantic = semantic_pct / 100
                resume_skills = extract_skills(resume_text)
                jd_skills = extract_skills(jd_text)
                matched = sorted(set(resume_skills) & set(jd_skills))
                skill_score = len(matched) / len(jd_skills) if jd_skills else 0
                final_score = (semantic + skill_score) / 2
                results.append({
                    'name': getattr(f, 'name', 'resume'),
                    'final_score': final_score,
                    'semantic_pct': semantic_pct,
                    'matched': matched
                })

        results = sorted(results, key=lambda x: x['final_score'], reverse=True)
        st.subheader("Ranked Candidates")
        for r in results:
            score_display = round(r['final_score'] * 100, 2)
            sem = round(r['semantic_pct'], 2)
            st.markdown(f"<div class='card'><strong>{r['name']}</strong> — <span style='color:#0f172a'>{score_display}%</span> (Semantic: {sem}%)</div>", unsafe_allow_html=True)
            if r['matched']:
                chips = " ".join([f"<span class='skill-chip matched'>{s}</span>" for s in r['matched']])
            else:
                chips = "<span class='skill-chip missing'>None detected</span>"
            st.markdown(chips, unsafe_allow_html=True)

    else:
        # single file handling (use the first uploaded file if multiple provided)
        f = resume_files[0] if isinstance(resume_files, (list, tuple)) else resume_files
        resume_text = extract_text_from_pdf(f)

        if not resume_text:
            st.error("Could not extract text from this PDF. Please try another file.")
        else:
            st.success("Resume uploaded and read successfully!")
            st.subheader("Resume Content Preview")
            st.write(resume_text[:500])

            if jd_text and jd_text.strip():
                st.info("Using BERT semantic matching. The first run may take a few seconds while the model downloads and loads.")
                with st.spinner("Computing semantic similarity..."):
                    score = calculate_match_score(resume_text, jd_text)

                st.metric("Semantic Match Score", f"{score}%")

                resume_skills = extract_skills(resume_text)
                jd_skills = extract_skills(jd_text)
                matched = sorted(set(resume_skills) & set(jd_skills))
                missing = sorted(set(jd_skills) - set(resume_skills))

                # categorized view
                from utils import categorize_skills
                res_cat = categorize_skills(resume_text)
                jd_cat = categorize_skills(jd_text)

                st.subheader("Skill Analysis")
                st.markdown("**Technical skills (resume):**")
                tech_display = ", ".join(res_cat['tech']) if res_cat['tech'] else "None detected"
                st.markdown(f"<div class='card'>{tech_display}</div>", unsafe_allow_html=True)
                st.markdown("**Tools (resume):**")
                tools_display = ", ".join(res_cat['tools']) if res_cat['tools'] else "None detected"
                st.markdown(f"<div class='card'>{tools_display}</div>", unsafe_allow_html=True)
                st.markdown("**Soft skills (resume):**")
                soft_display = ", ".join(res_cat['soft']) if res_cat['soft'] else "None detected"
                st.markdown(f"<div class='card'>{soft_display}</div>", unsafe_allow_html=True)

                st.write("---")
                # matched / missing chips
                if matched:
                    matched_chips = " ".join([f"<span class='skill-chip matched'>{s}</span>" for s in matched])
                else:
                    matched_chips = "<span class='skill-chip missing'>None detected</span>"
                if missing:
                    missing_chips = " ".join([f"<span class='skill-chip missing'>{s}</span>" for s in missing])
                else:
                    missing_chips = "<span class='skill-chip matched'>None detected</span>"

                st.markdown("**✅ Matched Skills:**")
                st.markdown(matched_chips, unsafe_allow_html=True)
                st.markdown("**❌ Missing Skills:**")
                st.markdown(missing_chips, unsafe_allow_html=True)

                # Top-3 missing skills recommendation
                from utils import recommend_missing_skills
                rec = recommend_missing_skills(jd_text, resume_text, top_n=3)
                if rec:
                    st.subheader("To improve match")
                    st.write("- Learn: " + ", ".join(rec))

                skill_score = len(matched) / len(jd_skills) if jd_skills else 0
                tfidf_score = score / 100
                final_score = (tfidf_score + skill_score) / 2
                show_score(final_score)
                explain_result(final_score, missing)
            else:
                st.info("Paste a job description to see the match score and skill analysis.")
