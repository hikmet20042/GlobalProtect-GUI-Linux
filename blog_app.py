from __future__ import annotations

import html
import os
import re
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "blog.db"

OWNER_NAME = "Hikmat Mammadli"
DOMAIN = "mammadli.space"
ADMIN_USERNAME = os.environ.get("BLOG_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("BLOG_ADMIN_PASSWORD", "change-me-now")

SESSIONS: dict[str, bool] = {}


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            summary TEXT,
            content TEXT NOT NULL,
            is_published INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def slugify(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    collapsed = re.sub(r"[\s_-]+", "-", normalized)
    return collapsed or "post"


def unique_slug(conn: sqlite3.Connection, title: str, exclude_id: int | None = None) -> str:
    base = slugify(title)
    slug = base
    num = 2
    while True:
        if exclude_id is None:
            exists = conn.execute("SELECT id FROM posts WHERE slug = ?", (slug,)).fetchone()
        else:
            exists = conn.execute("SELECT id FROM posts WHERE slug = ? AND id != ?", (slug, exclude_id)).fetchone()
        if exists is None:
            return slug
        slug = f"{base}-{num}"
        num += 1


def parse_post_data(environ) -> dict[str, str]:
    try:
        size = int(environ.get("CONTENT_LENGTH", "0"))
    except ValueError:
        size = 0
    raw = environ["wsgi.input"].read(size).decode("utf-8") if size > 0 else ""
    parsed = parse_qs(raw)
    return {k: v[0] for k, v in parsed.items()}


def get_session_id(environ) -> str | None:
    cookies = environ.get("HTTP_COOKIE", "")
    for part in cookies.split(";"):
        part = part.strip()
        if part.startswith("session_id="):
            return part.split("=", 1)[1]
    return None


def is_admin(environ) -> bool:
    sid = get_session_id(environ)
    return bool(sid and SESSIONS.get(sid))


def redirect(start_response, location: str, cookie: str | None = None):
    headers = [("Location", location)]
    if cookie:
        headers.append(("Set-Cookie", cookie))
    start_response("302 Found", headers)
    return [b""]


def html_page(title: str, body: str, flash: str = "") -> bytes:
    flash_box = f"<div class='flash'>{flash}</div>" if flash else ""
    content = f"""
<!doctype html>
<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{html.escape(title)}</title>
<link rel='stylesheet' href='/static/style.css'></head>
<body>
<header><div class='wrap'><h1>{OWNER_NAME}</h1><p>{DOMAIN}</p><nav><a href='/'>Home</a><a href='/admin'>Admin</a></nav></div></header>
<main class='wrap'>
{flash_box}
{body}
</main>
</body></html>
"""
    return content.encode("utf-8")


def app(environ, start_response):
    method = environ["REQUEST_METHOD"]
    path = environ.get("PATH_INFO", "/")

    if path == "/static/style.css":
        css = (BASE_DIR / "static" / "style.css").read_text(encoding="utf-8")
        start_response("200 OK", [("Content-Type", "text/css; charset=utf-8")])
        return [css.encode("utf-8")]

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if path == "/":
        posts = conn.execute(
            "SELECT title, slug, summary, content, created_at FROM posts WHERE is_published = 1 ORDER BY created_at DESC"
        ).fetchall()
        cards = "".join(
            f"<article class='card'><h3><a href='/post/{p['slug']}'>{html.escape(p['title'])}</a></h3>"
            f"<p class='meta'>{p['created_at'][:10]}</p><p>{html.escape(p['summary'] or p['content'][:160] + '...')}</p></article>"
            for p in posts
        ) or "<article class='card'><p>No published posts yet.</p></article>"
        body = f"<section><h2>Welcome to my blog</h2><p>Thoughts and updates by {OWNER_NAME}.</p>{cards}</section>"
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        conn.close()
        return [html_page("Blog", body)]

    if path.startswith("/post/"):
        slug = path.removeprefix("/post/")
        post = conn.execute(
            "SELECT title, summary, content, created_at FROM posts WHERE slug = ? AND is_published = 1", (slug,)
        ).fetchone()
        if not post:
            start_response("404 Not Found", [("Content-Type", "text/plain")])
            conn.close()
            return [b"Post not found"]
        body = (
            f"<article class='card'><h2>{html.escape(post['title'])}</h2><p class='meta'>{post['created_at'][:10]}</p>"
            f"<p>{html.escape(post['summary'] or '')}</p><div style='white-space: pre-wrap'>{html.escape(post['content'])}</div></article>"
        )
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        conn.close()
        return [html_page(post["title"], body)]

    if path == "/admin/login":
        if method == "GET":
            body = """
            <section class='card'><h2>Admin Login</h2>
            <form method='post'>
            <label>Username<input name='username' required></label>
            <label>Password<input name='password' type='password' required></label>
            <button type='submit'>Login</button>
            </form></section>
            """
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            conn.close()
            return [html_page("Admin Login", body)]
        data = parse_post_data(environ)
        if data.get("username") == ADMIN_USERNAME and data.get("password") == ADMIN_PASSWORD:
            sid = secrets.token_hex(16)
            SESSIONS[sid] = True
            conn.close()
            return redirect(start_response, "/admin", cookie=f"session_id={sid}; Path=/; HttpOnly")
        start_response("401 Unauthorized", [("Content-Type", "text/html; charset=utf-8")])
        conn.close()
        return [html_page("Admin Login", "<p>Invalid credentials.</p>")]

    if path == "/admin/logout":
        sid = get_session_id(environ)
        if sid:
            SESSIONS.pop(sid, None)
        conn.close()
        return redirect(start_response, "/", cookie="session_id=; Path=/; Max-Age=0")

    if path == "/admin" and not is_admin(environ):
        conn.close()
        return redirect(start_response, "/admin/login")

    if path == "/admin":
        posts = conn.execute("SELECT id, title, summary, is_published, created_at FROM posts ORDER BY created_at DESC").fetchall()
        listing = "".join(
            f"<article class='card'><h3>{html.escape(p['title'])}</h3><p class='meta'>{p['created_at'][:10]} · {'Published' if p['is_published'] else 'Draft'}</p>"
            f"<p>{html.escape(p['summary'] or '')}</p><div class='actions'><a class='btn' href='/admin/post/{p['id']}/edit'>Edit</a>"
            f"<form method='post' action='/admin/post/{p['id']}/delete'><button class='danger' type='submit'>Delete</button></form></div></article>"
            for p in posts
        ) or "<article class='card'><p>No posts created yet.</p></article>"
        body = f"""
        <section class='card'><h2>Create New Post</h2>
        <form method='post' action='/admin/post/new'>
        <label>Title<input name='title' required></label>
        <label>Summary<textarea name='summary' rows='2'></textarea></label>
        <label>Content<textarea name='content' rows='8' required></textarea></label>
        <label><input type='checkbox' name='is_published' checked> Publish now</label>
        <button type='submit'>Create Post</button>
        </form></section>
        <section><h2>Your Posts</h2>{listing}</section>
        """
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        conn.close()
        return [html_page("Admin Panel", body)]

    if path == "/admin/post/new" and method == "POST":
        if not is_admin(environ):
            conn.close()
            return redirect(start_response, "/admin/login")
        data = parse_post_data(environ)
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        if title and content:
            slug = unique_slug(conn, title)
            conn.execute(
                "INSERT INTO posts (title, slug, summary, content, is_published, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    title,
                    slug,
                    data.get("summary", "").strip(),
                    content,
                    1 if data.get("is_published") else 0,
                    datetime.utcnow().isoformat(timespec="seconds"),
                ),
            )
            conn.commit()
        conn.close()
        return redirect(start_response, "/admin")

    if path.startswith("/admin/post/") and path.endswith("/edit"):
        if not is_admin(environ):
            conn.close()
            return redirect(start_response, "/admin/login")
        post_id = int(path.split("/")[3])
        post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if not post:
            start_response("404 Not Found", [("Content-Type", "text/plain")])
            conn.close()
            return [b"Not found"]
        if method == "GET":
            body = f"""
            <section class='card'><h2>Edit Post</h2>
            <form method='post'>
            <label>Title<input name='title' value='{html.escape(post['title'])}' required></label>
            <label>Summary<textarea name='summary' rows='2'>{html.escape(post['summary'] or '')}</textarea></label>
            <label>Content<textarea name='content' rows='10' required>{html.escape(post['content'])}</textarea></label>
            <label><input type='checkbox' name='is_published' {'checked' if post['is_published'] else ''}> Published</label>
            <button type='submit'>Save</button></form></section>
            """
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            conn.close()
            return [html_page("Edit Post", body)]
        data = parse_post_data(environ)
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        if title and content:
            slug = post["slug"] if title == post["title"] else unique_slug(conn, title, exclude_id=post_id)
            conn.execute(
                "UPDATE posts SET title = ?, slug = ?, summary = ?, content = ?, is_published = ? WHERE id = ?",
                (title, slug, data.get("summary", "").strip(), content, 1 if data.get("is_published") else 0, post_id),
            )
            conn.commit()
        conn.close()
        return redirect(start_response, "/admin")

    if path.startswith("/admin/post/") and path.endswith("/delete") and method == "POST":
        if not is_admin(environ):
            conn.close()
            return redirect(start_response, "/admin/login")
        post_id = int(path.split("/")[3])
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()
        return redirect(start_response, "/admin")

    conn.close()
    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"Not Found"]


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "5000"))
    with make_server("0.0.0.0", port, app) as server:
        print(f"Serving on http://127.0.0.1:{port}")
        server.serve_forever()
