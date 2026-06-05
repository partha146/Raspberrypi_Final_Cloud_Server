from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, abort
import os, time, mimetypes, shutil

app = Flask(__name__)
app.secret_key = "mysecretkey123"

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.txt")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── helpers ──────────────────────────────────────────────

def load_users():
    users = {}
    if not os.path.exists(USERS_FILE):
        return users
    with open(USERS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if ":" in line:
                u, p = line.split(":", 1)
                users[u.strip()] = p.strip()
    return users

def safe_join(rel):
    rel = rel.strip("/") if rel else ""
    if rel:
        full = os.path.realpath(os.path.join(UPLOAD_DIR, rel))
    else:
        full = UPLOAD_DIR
    # on windows realpath may lowercase drive letter, compare carefully
    if not full.lower().startswith(UPLOAD_DIR.lower()):
        abort(403)
    return full

def format_size(b):
    if b < 1024:         return f"{b} B"
    elif b < 1048576:    return f"{b/1024:.1f} KB"
    elif b < 1073741824: return f"{b/1048576:.1f} MB"
    else:                return f"{b/1073741824:.2f} GB"

def file_icon(name, is_dir=False):
    if is_dir: return "📁"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return {
        "pdf":"📄","txt":"📝","doc":"📝","docx":"📝",
        "xls":"📊","xlsx":"📊","csv":"📊",
        "png":"🖼️","jpg":"🖼️","jpeg":"🖼️","gif":"🖼️","webp":"🖼️","svg":"🖼️",
        "mp4":"🎬","mov":"🎬","avi":"🎬","mkv":"🎬","webm":"🎬",
        "mp3":"🎵","wav":"🎵","flac":"🎵","ogg":"🎵",
        "zip":"🗜️","rar":"🗜️","tar":"🗜️","gz":"🗜️",
        "py":"🐍","js":"📜","html":"🌐","css":"🎨","json":"📋","md":"📋",
    }.get(ext, "📄")

def preview_type(name):
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext in ("png","jpg","jpeg","gif","webp","svg"): return "image"
    if ext in ("mp4","mov","webm"):                    return "video"
    if ext in ("mp3","wav","ogg","flac"):              return "audio"
    if ext in ("pdf",):                                return "pdf"
    if ext in ("txt","py","js","html","css","json","md","csv","sh","log","xml"): return "text"
    return "none"

def list_dir(rel):
    abs_path = safe_join(rel)
    if not os.path.isdir(abs_path):
        abort(404)
    items = []
    for name in sorted(os.listdir(abs_path),
                       key=lambda x: (not os.path.isdir(os.path.join(abs_path, x)), x.lower())):
        full      = os.path.join(abs_path, name)
        is_dir    = os.path.isdir(full)
        child_rel = (rel.strip("/") + "/" + name).strip("/") if rel else name
        items.append({
            "name":     name,
            "rel":      child_rel,
            "is_dir":   is_dir,
            "icon":     file_icon(name, is_dir),
            "size":     "" if is_dir else format_size(os.path.getsize(full)),
            "modified": time.strftime("%d %b %Y", time.localtime(os.path.getmtime(full))),
            "ptype":    "" if is_dir else preview_type(name),
        })
    return items

def make_crumbs(rel):
    crumbs = [{"name": "root", "rel": ""}]
    if rel:
        parts = rel.strip("/").split("/")
        for i, p in enumerate(parts):
            crumbs.append({"name": p, "rel": "/".join(parts[:i+1])})
    return crumbs

def logged_in():
    return "user" in session

# ── auth ─────────────────────────────────────────────────

@app.route("/")
def home():
    return redirect(url_for("drive", rel=""))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form["username"].strip()
        p = request.form["password"].strip()
        users = load_users()
        if u in users and users[u] == p:
            session["user"] = u
            return redirect(url_for("drive", rel=""))
        error = "Wrong username or password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ── drive ─────────────────────────────────────────────────

@app.route("/drive/", defaults={"rel": ""})
@app.route("/drive/<path:rel>")
def drive(rel):
    if not logged_in():
        return redirect(url_for("login"))
    items  = list_dir(rel)
    crumbs = make_crumbs(rel)
    return render_template("drive.html", username=session["user"],
                           items=items, crumbs=crumbs, rel=rel)

@app.route("/upload", methods=["POST"])
def upload():
    if not logged_in():
        return redirect(url_for("login"))
    rel  = request.form.get("current_rel", "").strip("/")
    dest = safe_join(rel)
    os.makedirs(dest, exist_ok=True)
    for f in request.files.getlist("files"):
        if f.filename:
            f.save(os.path.join(dest, f.filename))
    return redirect(url_for("drive", rel=rel))

@app.route("/mkdir", methods=["POST"])
def mkdir():
    if not logged_in():
        return redirect(url_for("login"))
    rel  = request.form.get("current_rel", "").strip("/")
    name = request.form.get("folder_name", "").strip()
    if name:
        # build the new folder path safely
        new_rel  = (rel + "/" + name).strip("/") if rel else name
        new_full = os.path.join(UPLOAD_DIR, new_rel)
        os.makedirs(new_full, exist_ok=True)
    return redirect(url_for("drive", rel=rel))

@app.route("/rename", methods=["POST"])
def rename():
    if not logged_in():
        return redirect(url_for("login"))
    rel      = request.form.get("current_rel", "").strip("/")
    old_name = request.form.get("old_name", "").strip()
    new_name = request.form.get("new_name", "").strip()
    if old_name and new_name and old_name != new_name:
        parent   = safe_join(rel)
        old_path = os.path.join(parent, old_name)
        new_path = os.path.join(parent, new_name)
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
    return redirect(url_for("drive", rel=rel))

@app.route("/download/<path:rel>")
def download(rel):
    if not logged_in():
        return redirect(url_for("login"))
    full      = safe_join(rel)
    directory = os.path.dirname(full)
    filename  = os.path.basename(full)
    return send_from_directory(directory, filename, as_attachment=True)

@app.route("/preview/<path:rel>")
def preview(rel):
    if not logged_in():
        return redirect(url_for("login"))
    full      = safe_join(rel)
    filename  = os.path.basename(full)
    ptype     = preview_type(filename)
    directory = os.path.dirname(full)
    if ptype == "text":
        try:
            with open(full, "r", errors="replace") as f:
                content = f.read(80000)
        except:
            content = "[Could not read file]"
        return render_template("preview.html", username=session["user"],
                               filename=filename, content=content, rel=rel)
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return send_from_directory(directory, filename, mimetype=mime)

@app.route("/delete/<path:rel>", methods=["POST"])
def delete(rel):
    if not logged_in():
        return redirect(url_for("login"))
    full   = safe_join(rel)
    parent = "/".join(rel.strip("/").split("/")[:-1])
    if os.path.isfile(full):
        os.remove(full)
    elif os.path.isdir(full):
        shutil.rmtree(full)
    return redirect(url_for("drive", rel=parent))

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
