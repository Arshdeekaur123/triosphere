import json
import os
from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import PyPDF2

app = Flask(__name__)

model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))
df = pickle.load(open("data.pkl", "rb"))

# RESUME TEXT EXTRACT

def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text.lower()

# SKILL EXTRACTION

known_skills = [
    "python", "java", "machine learning", "data analysis",
    "sql", "tensorflow", "pytorch", "html", "css",
    "javascript", "react", "node", "c++"
]

def extract_skills(text):
    found = []
    for skill in known_skills:
        if skill in text:
            found.append(skill)
    return found

def recommend_jobs(user_skills):
    user_text = " ".join(user_skills).lower()
    results = []

    for i, row in df.iterrows():
        print("Checking job:", i) 
        job_name = str(row['job_position_name'])
        job_text = str(row['skills_required'])

        combined = user_text + " " + job_text
        vec = vectorizer.transform([combined])

        score = model.predict(vec)[0]

        results.append((job_name, score, job_text))

    results = sorted(results, key=lambda x: x[1], reverse=True)

    seen = set()
    final = []
    for job, score, job_text in results:
        if job not in seen:
            final.append((job, round(score,2), job_text))
            seen.add(job)
        if len(final) == 3:
            break

    return final


def skill_gap(user_skills, job_text):
    user_set = set([s.lower() for s in user_skills])
    job_set = set(job_text.split())
    return list(job_set - user_set)
# JSON FILE (DATABASE)
DB_FILE = "users.json"

# create file if not exists
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump([], f)
@app.route('/img/<path:filename>')
def serve_img(filename):
    from flask import send_from_directory
    return send_from_directory('static/img', filename)
# read users
def read_users():
    with open(DB_FILE, "r") as f:
        return json.load(f)

# write users
def write_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=4)


# ROUTES (HTML PAGES)
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/predict', methods=['POST'])
def predict():
    try:
        file = request.files['resume']
        if not file or file.filename == "":
            return "No file uploaded"

        pdf = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content

        if text.strip() == "":
            return "Could not read resume. Try another PDF."

        # Extract skills from resume
        user_skills = extract_skills(text)

        jobs = recommend_jobs(user_skills)

        # Mapping of job titles to images
        job_images = {
            "AI Engineer": "ai_engineer.png",
            "Data Engineer": "data_engineer.png",
            "Database Administrator (DBA)": "dba.png",
            "Web Developer": "web_developer.png"
        }

        results = []
        for job, score, job_text in jobs:
            missing = skill_gap(user_skills, job_text)
            image_file = job_images.get(job, "default.png")  # default image if job not in mapping

            results.append({
                "job": job,
                "score": score,
                "job_skills": job_text.split(),
                "matched_skills": list(set(user_skills) & set(job_text.split())),
                "missing": missing,
                "image": image_file
            })

        return render_template('result.html', results=results)

    except Exception as e:
        return f"Error occurred: {str(e)}"
    
@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/upload")
def upload():
    return render_template("upload.html")
@app.route("/explore")
def explore():
    return render_template("explore.html")

@app.route("/opportunities")
def opportunities():
    return render_template("opportunities.html")

@app.route("/roadmap")
def roadmap():
    return render_template("roadmap.html")

@app.route("/roadmap-ai")
def roadmap_ai():
    return render_template("roadmapai.html")

@app.route("/roadmap-ds")
def roadmap_ds():
    return render_template("roadmapdatascience.html")

@app.route("/roadmap-cyber")
def roadmap_cyber():
    return render_template("roadmacyber.html")

@app.route("/webroad")
def webroad():
    return render_template("webroad.html")

# REGISTER API
@app.route("/register-user", methods=["POST"])
def register():
    data = request.json

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    users = read_users()

    # check if user exists
    for user in users:
        if user["email"] == email:
            return jsonify({"message": "User already exists"})

    # hash password
    hashed_password = generate_password_hash(password)

    users.append({
        "username": username,
        "email": email,
        "password": hashed_password
    })

    write_users(users)

    return jsonify({"message": "Registered successfully"})


# LOGIN API
@app.route("/login-user", methods=["POST"])
def login():
    data = request.json

    email = data.get("email")
    password = data.get("password")

    users = read_users()

    for user in users:
        if user["email"] == email:
            if check_password_hash(user["password"], password):
                return jsonify({"message": "Login successful"})
            else:
                return jsonify({"message": "Wrong password"})

    return jsonify({"message": "User not found"})


# RUN SERVER
if __name__ == "__main__":
    app.run(debug=True)