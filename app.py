import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config["POSTGRES_DB"] = os.environ.get("POSTGRES_DB", "postgres")
app.config["POSTGRES_USER"] = os.environ.get("POSTGRES_USER", "postgres")
app.config["POSTGRES_PASSWORD"] = os.environ.get("POSTGRES_PASSWORD")
if not app.config["POSTGRES_PASSWORD"]:
  raise ValueError("No POSTGRES_PASSWORD environment variable set!")

app.config["POSTGRES_HOST"] = os.environ.get("POSTGRES_HOST", "localhost")
app.config["POSTGRES_PORT"] = int(os.environ.get("POSTGRES_PORT", 5432))

app.secret_key = os.environ.get("APP_SECRET_KEY")
if not app.secret_key:
  raise ValueError(
      "No APP_SECRET_KEY environment variable set! A secure key is required for"
      " production."
  )

socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def get_db_connection():
  """Establishes a connection to the PostgreSQL database."""
  try:
    conn = psycopg2.connect(
        host=app.config["POSTGRES_HOST"],
        database=app.config["POSTGRES_DB"],
        user=app.config["POSTGRES_USER"],
        password=app.config["POSTGRES_PASSWORD"],
        port=app.config["POSTGRES_PORT"],
    )
    return conn
  except psycopg2.OperationalError as e:
    print(f"FATAL: Database connection failed. Check status. Error: {e}")
    raise RuntimeError("Could not connect to database.")

def create_tables():
  conn = None
  try:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                reset_token TEXT,
                reset_token_expiration TIMESTAMP WITHOUT TIME ZONE
            );
        """)
    cur.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                company VARCHAR(255) NOT NULL,
                location VARCHAR(255) NOT NULL,
                type VARCHAR(50) NOT NULL,
                salary VARCHAR(100),
                description TEXT NOT NULL,
                requirements TEXT NOT NULL,
                application_email VARCHAR(255),
                posted_date TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                phone_number VARCHAR(50),
                poster_id INTEGER,
                FOREIGN KEY (poster_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)
    conn.commit()
    cur.close()
  except Exception as e:
    print(f"Error creating tables: {e}")
    if conn:
      conn.rollback()
  finally:
    if conn:
      conn.close()


with app.app_context():
  create_tables()


def allowed_file(filename):
  ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
  return (
      "." in filename
      and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
  )


@app.route("/login_page")
def login_page():
  return render_template("login.html")


@app.route("/register_page")
def register_page():
  return render_template("register.html")


@app.route("/")
def home():
  if "user_id" not in session:
    return redirect(url_for("login_page"))
  return render_template("index.html")


@app.route("/logout")
def logout():
  session.pop("user_id", None)
  session.pop("full_name", None)
  flash("You have been logged out.", "info")
  return redirect(url_for("login_page"))


@app.route("/browse-jobs")
def browse_jobs_page():
  if "user_id" not in session:
    return redirect(url_for("login_page"))
  current_user_id = session.get("user_id")
  return render_template("browse-jobs.html", current_user_id=current_user_id)


@app.route("/post-job")
def post_job_page():
  if "user_id" not in session:
    return redirect(url_for("login_page"))
  return render_template("post-jobs.html")


@app.route("/resume-builder")
def resume_builder():
  if "user_id" not in session:
    return redirect(url_for("login_page"))
  return render_template("resume-builder.html")


@app.route("/about-us")
def about_us():
  if "user_id" not in session:
    return redirect(url_for("login_page"))
  return render_template("about-us.html")


@app.route("/contact-us")
def contact_us():
  if "user_id" not in session:
    return redirect(url_for("login_page"))
  return render_template("contact.html")


@app.route("/job-details.html")
def job_details_page():
  if "user_id" not in session:
    return redirect(url_for("login_page"))
  return render_template("job-details.html")


@app.route("/apply", methods=["GET"])
def apply_page():
  if "user_id" not in session:
    return redirect(url_for("login_page"))
  job_id = request.args.get("id")
  return render_template("apply.html", job_id=job_id)


@app.route("/api/apply", methods=["POST"])
def submit_application():
  if "user_id" not in session:
    return jsonify({"error": "Unauthorized"}), 401

  if "resume" not in request.files:
    return jsonify({"error": "No resume file uploaded"}), 400

  resume = request.files["resume"]

  if resume.filename == "":
    return jsonify({"error": "No selected resume file"}), 400

  if resume and allowed_file(resume.filename):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    original_filename = secure_filename(resume.filename)
    filename = f"{timestamp}_{original_filename}"
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    resume.save(file_path)

    full_name = request.form.get("fullName")
    email = request.form.get("email")
    phone = request.form.get("phone", "N/A")
    cover_letter = request.form.get("coverLetter", "N/A")
    job_id = request.form.get("jobId")

    job_title = "General Application"
    if job_id:
      try:
        with get_db_connection() as conn:
          with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT title, company FROM jobs WHERE id = %s", (job_id,)
            )
            job_data = cursor.fetchone()
            if job_data:
              job_title = f"{job_data['title']} at {job_data['company']}"
      except Exception:
        pass

    try:
      mail_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
      mail_port = int(os.environ.get("MAIL_PORT", 587))
      mail_username = os.environ.get("MAIL_USERNAME")
      mail_password = os.environ.get("MAIL_PASSWORD")
      recipient_email = mail_username

      if mail_username and mail_password:
        msg = MIMEMultipart()
        msg["From"] = mail_username
        msg["To"] = recipient_email
        msg["Subject"] = f"New Job Application: {job_title} - {full_name}"

        body = f"""
                You have received a new job application!

                Position: {job_title}
                Applicant Name: {full_name}
                Email: {email}
                Phone: {phone}
                
                Cover Letter:
                {cover_letter}
                """
        msg.attach(MIMEText(body, "plain"))

        with open(file_path, "rb") as attachment:
          part = MIMEBase("application", "octet-stream")
          part.set_payload(attachment.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", f"attachment; filename= {original_filename}"
        )
        msg.attach(part)

        with smtplib.SMTP(mail_server, mail_port) as server:
          server.starttls()
          server.login(mail_username, mail_password)
          server.sendmail(mail_username, recipient_email, msg.as_string())
      else:
        print(
            "WARNING: Mail credentials not fully configured. Email skipped."
        )

    except Exception as e:
      print(f"Error sending application email: {e}")

    return (
        jsonify({
            "message": "Application submitted successfully!",
            "filename": filename,
        }),
        200,
    )
  else:
    return (
        jsonify({
            "error": "Invalid file type. Only PDF, DOC, DOCX are allowed"
        }),
        400,
    )


@app.route("/api/post-job", methods=["POST"])
def post_job():
  if "user_id" not in session:
    return (
        jsonify({
            "error": "Unauthorized",
            "message": "Please log in to post a job.",
        }),
        401,
    )

  current_user_id = session["user_id"]

  try:
    with get_db_connection() as conn:
      with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT is_admin FROM users WHERE id = %s", (current_user_id,)
        )
        user_record = cursor.fetchone()

        if not user_record or not user_record.get("is_admin"):
          return (
              jsonify({
                  "error": "Forbidden",
                  "message": (
                      "Only designated administrators are allowed to post jobs."
                  ),
              }),
              403,
          )

    data = request.get_json()
    title = data.get("title")
    company = data.get("company")
    location = data.get("location")
    job_type = data.get("type")
    salary = data.get("salary")
    description = data.get("description")
    requirements = data.get("requirements")
    application_email = data.get("application_email")
    phone_number = data.get("phone_number")

    if not all(
        [title, company, location, job_type, description, requirements]
    ):
      return (
          jsonify({
              "error": (
                  "Missing required fields (Title, Company, Location, Type,"
                  " Description, Requirements)"
              )
          }),
          400,
      )

    if not application_email and not phone_number:
      return (
          jsonify({
              "error": (
                  "You must provide either an application email or a phone"
                  " number for job seekers to apply."
              )
          }),
          400,
      )

    salary = salary if salary else None
    application_email = application_email if application_email else None
    phone_number = phone_number if phone_number else None
    requirements = requirements if requirements else None

    with get_db_connection() as conn:
      with conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO jobs (title, company, location, type, salary, description, 
                        requirements, application_email, phone_number, posted_date, poster_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s) RETURNING id""",
            (
                title,
                company,
                location,
                job_type,
                salary,
                description,
                requirements,
                application_email,
                phone_number,
                current_user_id,
            ),
        )
        new_job_id = cursor.fetchone()[0]
        conn.commit()
    return jsonify({"message": "Job posted successfully!", "job_id": new_job_id}), 201

  except psycopg2.Error as e:
    print(f"Database error posting job: {e}")
    return jsonify({"error": "Database error posting job"}), 500
  except Exception as e:
    print(f"Error posting job: {e}")
    return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/jobs", methods=["GET"])
def get_jobs():
  try:
    with get_db_connection() as conn:
      with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT id, title, company, location, type, salary, description,"
            " requirements, application_email, phone_number, poster_id,"
            " posted_date FROM jobs ORDER BY posted_date DESC"
        )
        jobs = cursor.fetchall()
    return jsonify(jobs)
  except psycopg2.Error as e:
    print(f"Database error during job fetch: {e}")
    return jsonify({"error": "Database error fetching jobs"}), 500
  except Exception as e:
    print(f"An unexpected error occurred during job fetch: {e}")
    return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/search-jobs", methods=["GET"])
def search_jobs():
  query = request.args.get("q")
  if not query:
    return get_jobs()

  try:
    with get_db_connection() as conn:
      with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        sql = """
                    SELECT id, title, company, location, type, salary, description, requirements, application_email, phone_number, poster_id, posted_date FROM jobs
                    WHERE LOWER(title) LIKE %s OR LOWER(company) LIKE %s OR LOWER(location) LIKE %s OR LOWER(description) LIKE %s
                    ORDER BY posted_date DESC
                """
        search_term = f"%{query.lower()}%"
        cursor.execute(
            sql, (search_term, search_term, search_term, search_term)
        )
        jobs = cursor.fetchall()
    return jsonify(jobs), 200
  except psycopg2.Error as e:
    print(f"Database error during search: {e}")
    return jsonify({"error": "Failed to retrieve search results"}), 500
  except Exception as e:
    print(f"An unexpected error occurred during search: {e}")
    return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/login", methods=["POST"])
def login():
  data = request.get_json()
  email = data.get("email")
  password = data.get("password")
  if not email or not password:
    return jsonify({"error": "Email and password are required"}), 400

  try:
    with get_db_connection() as conn:
      with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT id, full_name, password FROM users WHERE email = %s",
            (email,),
        )
        user = cursor.fetchone()

    if user:
      user_id = user["id"]
      full_name = user["full_name"]
      hashed_password = user["password"]

      if check_password_hash(hashed_password, password):
        session["user_id"] = user_id
        session["full_name"] = full_name
        return (
            jsonify({"message": "Login successful!", "full_name": full_name}),
            200,
        )
      else:
        return jsonify({"error": "Invalid credentials"}), 401
    else:
      return jsonify({"error": "User not found"}), 401
  except psycopg2.Error as e:
    print(f"Database error during login: {e}")
    return jsonify({"error": "Database error during login"}), 500
  except Exception as e:
    print(f"An unexpected error occurred during login: {e}")
    return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/register", methods=["POST"])
def register():
  data = request.get_json()
  full_name = data.get("fullName")
  email = data.get("email")
  password = data.get("password")

  if not full_name or not email or not password:
    return jsonify({"error": "All fields are required"}), 400

  try:
    with get_db_connection() as conn:
      with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
          return jsonify({"error": "Email already registered"}), 409

        cursor.execute("SELECT COUNT(*) AS count FROM users")
        user_count = cursor.fetchone()["count"]
        is_admin_flag = True if user_count == 0 else False

        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (full_name, email, password, is_admin) VALUES"
            " (%s, %s, %s, %s)",
            (full_name, email, hashed_password, is_admin_flag),
        )
        conn.commit()
    return jsonify({"message": "Registration successful!"}), 201
  except psycopg2.Error as e:
    print(f"Database error during registration: {e}")
    return jsonify({"error": "Database error during registration"}), 500
  except Exception as e:
    print(f"An unexpected error occurred during registration: {e}")
    return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
  if "user_id" not in session:
    return jsonify({"error": "Unauthorized. Please log in."}), 401

  current_user_id = session["user_id"]
  try:
    with get_db_connection() as conn:
      with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT poster_id FROM jobs WHERE id = %s", (job_id,))
        job_data = cursor.fetchone()

        if not job_data:
          return jsonify({"error": "Job not found."}), 404

        poster_id_from_db = job_data["poster_id"]

        if (
            poster_id_from_db is not None
            and poster_id_from_db != current_user_id
        ):
          return (
              jsonify({
                  "error": (
                      "Forbidden. You are not authorized to delete this job."
                  )
              }),
              403,
          )

        cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
        conn.commit()

        if cursor.rowcount == 0:
          return jsonify({"error": "Job not found or already deleted."}), 404

      return jsonify({"message": "Job deleted successfully!"}), 200

  except psycopg2.Error as e:
    print(f"Database error during job deletion: {e}")
    return jsonify({"error": "Database error during job deletion"}), 500
  except Exception as e:
    print(f"An unexpected error occurred during job deletion: {e}")
    return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/jobs/<int:job_id>", methods=["PUT"])
def edit_job(job_id):
  if "user_id" not in session:
    return jsonify({"error": "Unauthorized. Please log in."}), 401

  current_user_id = session["user_id"]
  data = request.get_json()

  title = data.get("title")
  company = data.get("company")
  location = data.get("location")
  job_type = data.get("type")
  salary = data.get("salary")
  description = data.get("description")
  requirements = data.get("requirements")
  application_email = data.get("application_email")
  phone_number = data.get("phone_number")

  if not all(
      [title, company, location, job_type, description, requirements]
  ):
    return (
        jsonify({
            "error": (
                "Missing required fields (title, company, location, type,"
                " description, requirements)"
            )
        }),
        400,
    )

  if not application_email and not phone_number:
    return (
        jsonify({
            "error": "Either application email or phone number is required"
        }),
        400,
    )

  salary = salary if salary else None
  application_email = application_email if application_email else None
  phone_number = phone_number if phone_number else None
  requirements = requirements if requirements else None

  try:
    with get_db_connection() as conn:
      with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT poster_id FROM jobs WHERE id = %s", (job_id,))
        job_data = cursor.fetchone()

        if not job_data:
          return jsonify({"error": "Job not found."}), 404

        poster_id_from_db = job_data["poster_id"]

        if (
            poster_id_from_db is not None
            and poster_id_from_db != current_user_id
        ):
          return (
              jsonify({
                  "error": "Forbidden. You are not authorized to edit this job."
              }),
              403,
          )

        sql = """
                    UPDATE jobs
                    SET title = %s, company = %s, location = %s, type = %s, salary = %s,
                        description = %s, requirements = %s, application_email = %s, phone_number = %s
                    WHERE id = %s
                """
        cursor.execute(
            sql,
            (
                title,
                company,
                location,
                job_type,
                salary,
                description,
                requirements,
                application_email,
                phone_number,
                job_id,
            ),
        )
        conn.commit()

        if cursor.rowcount == 0:
          return jsonify({"error": "Job not found or no changes made."}), 404

      return jsonify({"message": "Job updated successfully!"}), 200

  except psycopg2.Error as e:
    print(f"Database error during job update: {e}")
    return jsonify({"error": "Database error during job update"}), 500
  except Exception as e:
    print(f"An unexpected error occurred during job update: {e}")
    return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/edit-job/<int:job_id>")
def edit_job_page(job_id):
  if "user_id" not in session:
    return redirect(url_for("login_page"))

  current_user_id = session["user_id"]
  job = None
  try:
    with get_db_connection() as conn:
      with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT id, title, company, location, type, salary, description,"
            " requirements, application_email, phone_number, poster_id FROM"
            " jobs WHERE id = %s",
            (job_id,),
        )
        job = cursor.fetchone()

        if not job:
          flash("Job not found.")
          return redirect(url_for("browse_jobs_page"))

        if job["poster_id"] is not None and job["poster_id"] != current_user_id:
          flash("You are not authorized to edit this job.")
          return redirect(url_for("browse_jobs_page"))

  except psycopg2.Error as e:
    print(f"Database error fetching job for edit: {e}")
    flash("An error occurred while loading the job for editing.")
    return redirect(url_for("browse_jobs_page"))
  except Exception as e:
    print(f"An unexpected error occurred: {e}")
    flash("An unexpected error occurred while loading the job for editing.")
    return redirect(url_for("browse_jobs_page"))

  return render_template("edit-job.html", job=job)


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
  if request.method == "POST":
    contact_value = request.form.get("contact")
    recovery_type = request.form.get("recovery_type")
    user = None

    if not contact_value:
      flash("Please enter your email address.", "danger")
      return render_template("forgot_password.html")

    try:
      with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
          if recovery_type == "password":
            cur.execute(
                "SELECT id, email, full_name FROM users WHERE email = %s",
                (contact_value,),
            )
            user = cur.fetchone()

            if user:
              token = secrets.token_urlsafe(32)
              expiration = datetime.now() + timedelta(hours=1)

              cur.execute(
                  "UPDATE users SET reset_token = %s, reset_token_expiration ="
                  " %s WHERE id = %s",
                  (token, expiration, user["id"]),
              )
              conn.commit()

              flash(f'Password reset link sent to {user["email"]}.', "success")

              reset_url = url_for("reset_password", token=token, _external=True)

              return render_template(
                  "forgot_password.html", reset_url=reset_url
              )
            else:
              flash("Email address not found.", "danger")

          elif recovery_type == "username":
            cur.execute(
                "SELECT full_name FROM users WHERE email = %s", (contact_value,)
            )
            user_name = cur.fetchone()

            if user_name:
              flash(
                  f'The full name (username) associated with that email is:'
                  f' {user_name["full_name"]}',
                  "success",
              )
            else:
              flash("Email address not found.", "danger")

    except Exception as e:
      flash(f"An error occurred: {e}", "danger")

  return render_template("forgot_password.html")


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
  user = None
  try:
    with get_db_connection() as conn:
      with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT id FROM users WHERE reset_token = %s AND"
            " reset_token_expiration > %s",
            (token, datetime.now()),
        )
        user = cur.fetchone()

      if not user:
        flash("Invalid or expired password reset token.", "danger")
        return redirect(url_for("forgot_password"))

      if request.method == "POST":
        new_password = request.form["new_password"]

        if not new_password:
          flash("Password cannot be empty.", "danger")
          return render_template("reset_password.html", token=token)

        hashed_password = generate_password_hash(new_password)

        with conn.cursor() as cur:
          cur.execute(
              "UPDATE users SET password = %s, reset_token = NULL,"
              " reset_token_expiration = NULL WHERE id = %s",
              (hashed_password, user["id"]),
          )
          conn.commit()

        flash(
            "Your password has been successfully reset. Please log in.",
            "success",
        )
        return redirect(url_for("login_page"))

  except Exception as e:
    flash(f"An error occurred: {e}", "danger")

  return render_template("reset_password.html", token=token)


users = {}


@socketio.on("disconnect")
def handle_disconnect():
  username = users.get(request.sid, "A user")
  print(f"Client disconnected: {username} (SID: {request.sid})")
  emit(
      "message",
      {"sender": "System", "text": f"{username} has left the chat."},
      broadcast=True,
  )
  if request.sid in users:
    del users[request.sid]


@socketio.on("join")
def on_join(data):
  username = data
  users[request.sid] = username
  emit(
      "message",
      {"sender": "System", "text": f"{username} has joined the chat."},
      broadcast=True,
  )


@socketio.on("message")
def handle_message(data):
  sender = data.get("sender", "Guest")
  text = data.get("text", "")
  if sender and text:
    print(f"Message from {sender}: {text}")
    emit("message", {"sender": sender, "text": text}, broadcast=True)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8000))
  socketio.run(app, host="0.0.0.0", port=port)