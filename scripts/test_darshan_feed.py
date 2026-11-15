"""Tests for darshan_feed.py, on pages shaped like the temple website's
(Next.js: photos inside /_next/image?url=... links, HTML-escaped)."""

import datetime as dt
import unittest

import darshan_feed as f

ENC = "https://harekrishnamandir.org/_next/image?url=https%3A%2F%2Fapi.harekrishnamandir.org%2Fuploads%2F{}&amp;w=2048&amp;q=90"

LISTING = f"""
<a href="/gallery/2026-11-15-darshan-2"><img src="{ENC.format('gallery%2F2026%2F11%2Fcover15.jpg')}"></a>
<a href="/gallery/govardhan-pooja-2026">Govardhan</a>
<a href="/gallery/2026-11-14-darshan">14</a>
<a href="/gallery/2026-10-09-darshan-2026-10-09">9 Oct</a>
<a href="/gallery/2027-01-01-darshan">typo, far future</a>
<script>self.__next_f.push([1,"{{\\"href\\":\\"/gallery/2026-11-13-darshan\\"}}"])</script>
"""

ALBUM = f"""
<head><title>2026-11-15 Darshan | Hare Krishna Mandir</title>
<meta property="og:title" content="2026-11-15 Darshan | Hare Krishna Mandir">
<meta property="og:image" content="https://api.harekrishnamandir.org/uploads/gallery/2026/11/cover15.jpg"></head>
<img src="{ENC.format('logos%2F2026%2F10%2Flogo.png')}">
<img srcset="{ENC.format('gallery%2F2026%2F11%2Fcover15.jpg')} 1x">
<h2>The photographs</h2>
<img src="{ENC.format('gallery%2F2026%2F11%2Fa.jpg')}">
<img src="{ENC.format('gallery%2F2026%2F11%2Fb.JPG')}">
<img src="{ENC.format('legacy%2Fgallery%2Fgallery_img_1.webp')}">
<script>["https:\\/\\/api.harekrishnamandir.org\\/uploads\\/gallery\\/2026\\/11\\/a.jpg"]</script>
<a href="/gallery/2026-11-14-darshan">More from the gallery</a>
"""


class FeedTest(unittest.TestCase):
    today = dt.date(2026, 11, 15)

    def test_albums_with_dates(self):
        got = f.find_albums(LISTING, self.today)
        self.assertEqual(
            got,
            {
                "2026-11-15-darshan-2": dt.date(2026, 11, 15),
                "2026-11-14-darshan": dt.date(2026, 11, 14),
                "2026-10-09-darshan-2026-10-09": dt.date(2026, 10, 9),
                "2026-11-13-darshan": dt.date(2026, 11, 13),
            },
        )

    def test_photos_in_order_once_without_logos(self):
        self.assertEqual(
            f.find_photos(ALBUM),
            [
                "https://api.harekrishnamandir.org/uploads/gallery/2026/11/cover15.jpg",
                "https://api.harekrishnamandir.org/uploads/gallery/2026/11/a.jpg",
                "https://api.harekrishnamandir.org/uploads/gallery/2026/11/b.JPG",
                "https://api.harekrishnamandir.org/uploads/legacy/gallery/gallery_img_1.webp",
            ],
        )

    def test_title(self):
        self.assertEqual(f.title_of(ALBUM, "x"), "2026-11-15 Darshan")
        self.assertEqual(f.title_of("<p>none</p>", "x"), "x")


if __name__ == "__main__":
    unittest.main()
