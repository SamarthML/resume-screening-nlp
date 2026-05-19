import re

_semantic_model = None


def extract_text_from_pdf(file):
    """Extract text from a PDF. If regular text extraction returns empty,
    fallback to OCR (scanned PDFs) using `pdf2image` + `pytesseract`.
    Note: OCR requires poppler and tesseract to be installed on the system.
    """
    import pdfplumber

    file.seek(0)
    pages = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)

    text = "\n".join(pages).strip()
    if text:
        return text

    # Fallback to OCR for scanned PDFs
    try:
        return ocr_pdf(file)
    except Exception:
        return ""


def clean_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[\r\n]+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_semantic_model():
    global _semantic_model
    if _semantic_model is None:
        from sentence_transformers import SentenceTransformer
        _semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _semantic_model


def calculate_match_score(resume_text, jd_text):
    resume_clean = clean_text(resume_text)
    jd_clean = clean_text(jd_text)

    if not resume_clean or not jd_clean:
        return 0.0

    from sklearn.metrics.pairwise import cosine_similarity

    model = get_semantic_model()
    embeddings = model.encode([resume_clean, jd_clean], convert_to_numpy=True)
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return round(float(score) * 100, 2)

def extract_skills(text):
    tech_skills = [
        "python", "sql", "machine learning", "deep learning",
        "nlp", "tensorflow", "pytorch", "aws", "docker",
        "pandas", "numpy"
    ]

    tools = [
        "excel", "power bi", "tableau", "powerpoint", "dashboard",
        "reporting", "automation"
    ]

    soft_skills = [
        "communication", "teamwork", "kpi", "finance", "uat"
    ]

    all_skills = tech_skills + tools + soft_skills

    found = []
    found_tech = []
    found_tools = []
    found_soft = []

    text_l = text.lower()
    for skill in tech_skills:
        if skill in text_l:
            found.append(skill)
            found_tech.append(skill)

    for skill in tools:
        if skill in text_l:
            found.append(skill)
            found_tools.append(skill)

    for skill in soft_skills:
        if skill in text_l:
            found.append(skill)
            found_soft.append(skill)

    # Keep backward-compatible return (flat list)
    return found


def categorize_skills(text):
    """Return categorized skills found in text as dict with keys: tech, tools, soft."""
    tech_skills = [
        "python", "sql", "machine learning", "deep learning",
        "nlp", "tensorflow", "pytorch", "aws", "docker",
        "pandas", "numpy"
    ]

    tools = [
        "excel", "power bi", "tableau", "powerpoint", "dashboard",
        "reporting", "automation"
    ]

    soft_skills = [
        "communication", "teamwork", "kpi", "finance", "uat"
    ]

    text_l = text.lower()
    return {
        'tech': [s for s in tech_skills if s in text_l],
        'tools': [s for s in tools if s in text_l],
        'soft': [s for s in soft_skills if s in text_l]
    }


def _fuzzy_contains(skill, text, threshold=80):
    """Return True if `skill` appears in `text` via exact or fuzzy match."""
    text_l = text.lower()
    if skill in text_l:
        return True
    try:
        # import here to keep startup light
        from rapidfuzz import fuzz
        score = fuzz.partial_ratio(skill, text_l)
        return score >= threshold
    except Exception:
        return False


def extract_skills(text, threshold=80):
    """Find skills in text using fuzzy matching. Backward-compatible with previous signature."""
    tech_skills = [
        "python", "sql", "machine learning", "deep learning",
        "nlp", "tensorflow", "pytorch", "aws", "docker",
        "pandas", "numpy"
    ]

    tools = [
        "excel", "power bi", "tableau", "powerpoint", "dashboard",
        "reporting", "automation"
    ]

    soft_skills = [
        "communication", "teamwork", "kpi", "finance", "uat"
    ]

    found = []
    text_l = text.lower()
    for s in tech_skills + tools + soft_skills:
        if _fuzzy_contains(s, text_l, threshold=threshold):
            found.append(s)

    return found


def ocr_pdf(file):
    """Perform OCR on PDF and return extracted text.
    Requires `pdf2image` and `pytesseract` and system binaries poppler & tesseract.
    """
    from pdf2image import convert_from_bytes
    import pytesseract

    file.seek(0)
    data = file.read()
    images = convert_from_bytes(data)
    texts = []
    for img in images:
        texts.append(pytesseract.image_to_string(img))
    return "\n".join(texts).strip()


def recommend_missing_skills(jd_text, resume_text, top_n=3):
    """Return top N missing skills the candidate should learn to improve match.
    Simple heuristic: take JD skills not present in resume and return up to top_n.
    """
    jd_sk = extract_skills(jd_text)
    res_sk = extract_skills(resume_text)
    missing = [s for s in jd_sk if s not in res_sk]
    # preserve order from JD skills, return up to top_n
    return missing[:top_n]