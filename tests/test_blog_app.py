import sqlite3
import tempfile
import unittest

from blog_app import slugify, unique_slug


class BlogUtilitiesTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Hello Matte Green"), "hello-matte-green")

    def test_unique_slug(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            conn = sqlite3.connect(tmp.name)
            conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT NOT NULL UNIQUE)")
            conn.execute("INSERT INTO posts(slug) VALUES (?)", ("first-post",))
            conn.commit()
            self.assertEqual(unique_slug(conn, "First Post"), "first-post-2")


if __name__ == "__main__":
    unittest.main()
