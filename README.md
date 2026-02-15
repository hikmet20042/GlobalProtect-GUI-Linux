# Matte Green Blog Website

A Python (standard library) blog website with a matte green design and an admin panel to manage content.

Built for **Hikmat Mammadli** on **mammadli.space**.

## Features

- Public homepage with published blog posts.
- Dedicated post details page.
- Admin login and protected dashboard.
- Create, edit, publish/unpublish, and delete posts.
- SQLite storage (no external database required).

## Quick start

```bash
python blog_app.py
```

Open <http://127.0.0.1:5000>.

## Admin panel

- URL: `/admin/login`
- Default username: `admin`
- Default password: `change-me-now`

Use environment variables in production:

```bash
export BLOG_ADMIN_USERNAME='your-admin'
export BLOG_ADMIN_PASSWORD='your-strong-password'
python blog_app.py
```

## Notes

- Blog data is stored in `blog.db`.
- The posts table is auto-created on first launch.
