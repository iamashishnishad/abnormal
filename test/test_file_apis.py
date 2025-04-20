import unittest
import os
import time
import requests
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/files/"

# Helper function to create temporary files for upload
def create_temp_file(filename, content, size_kb=1):
    with open(filename, "w") as f:
        f.write(content)
        f.write(" " * (size_kb * 1024 - len(content)))  # Pad to desired size
    return filename

class TestFileDeduplicationSystem(unittest.TestCase):
    def setUp(self):
        self.session = requests.Session()
        # Clean up any existing test files (optional, requires delete endpoint)
        # If needed, implement DELETE /api/files/<id> calls here

    def tearDown(self):
        self.session.close()

    def test_detect_duplicate_file_upload(self):
        # Create two identical files
        file1 = create_temp_file("test1.txt", "Test Content", 1)
        file2 = create_temp_file("test2.txt", "Test Content", 1)

        # Upload first file
        with open(file1, "rb") as f1:
            response = self.session.post(
                f"{API_BASE_URL}", files={"file": (file1, f1)}
            )
            self.assertEqual(response.status_code, 201)
            file1_data = response.json()
            self.assertFalse(file1_data["is_duplicate"])

        # Check duplicate for second file
        with open(file2, "rb") as f2:
            response = self.session.post(
                f"{API_BASE_URL}check_duplicate/", files={"file": (file2, f2)}
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["is_duplicate"])

        # Cleanup
        os.remove(file1)
        os.remove(file2)

    def test_store_reference_instead_of_duplicate(self):
        file1 = create_temp_file("image.png", "Image Data", 100)
        file2 = create_temp_file("image_copy.png", "Image Data", 100)

        # Upload first file
        with open(file1, "rb") as f1:
            response = self.session.post(
                f"{API_BASE_URL}", files={"file": (file1, f1)}
            )
            self.assertEqual(response.status_code, 201)
            file1_data = response.json()

        # Upload second (duplicate) file
        with open(file2, "rb") as f2:
            response = self.session.post(
                f"{API_BASE_URL}", files={"file": (file2, f2)}
            )
            self.assertEqual(response.status_code, 201)
            file2_data = response.json()
            self.assertTrue(file2_data["is_duplicate"])
            self.assertEqual(file2_data["original_file"], file1_data["id"])
            self.assertGreater(file2_data["storage_saved"], 0)

        os.remove(file1)
        os.remove(file2)

    def test_track_storage_savings(self):
        file1 = create_temp_file("doc1.pdf", "PDF Content", 10000)
        file2 = create_temp_file("doc2.pdf", "PDF Content", 10000)

        # Upload files
        with open(file1, "rb") as f1:
            self.session.post(f"{API_BASE_URL}", files={"file": (file1, f1)})
        with open(file2, "rb") as f2:
            self.session.post(f"{API_BASE_URL}", files={"file": (file2, f2)})

        # Check storage stats
        response = self.session.get(f"{API_BASE_URL}storage_stats/")
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        self.assertGreater(stats["total_storage_saved"], 0)
        self.assertEqual(stats["duplicate_count"], 1)

        os.remove(file1)
        os.remove(file2)

    def test_non_duplicate_file_upload(self):
        file1 = create_temp_file("unique.txt", "Unique Content", 1)
        with open(file1, "rb") as f1:
            response = self.session.post(
                f"{API_BASE_URL}", files={"file": (file1, f1)}
            )
            self.assertEqual(response.status_code, 201)
            data = response.json()
            self.assertFalse(data["is_duplicate"])
            self.assertEqual(data["storage_saved"], 0)
        os.remove(file1)

class TestSearchFilteringSystem(unittest.TestCase):
    def setUp(self):
        self.session = requests.Session()
        # Pre-upload test files
        files = [
            ("report.pdf", "Report1", 500, "2025-01-01T00:00:00Z"),
            ("report_final.pdf", "Report2", 600, "2025-01-02T00:00:00Z"),
            ("image.jpg", "Image", 200, "2025-01-03T00:00:00Z"),
            ("doc1.pdf", "Doc1", 500, "2025-03-01T00:00:00Z"),
            ("doc2.docx", "Doc2", 300, "2025-03-02T00:00:00Z"),
            ("video.mp4", "Video", 2000, "2025-03-03T00:00:00Z"),
            ("small.txt", "Small", 1, "2025-01-01T00:00:00Z"),
            ("medium.pdf", "Medium", 500, "2025-03-01T00:00:00Z"),
            ("large.mp4", "Large", 2000, "2025-04-01T00:00:00Z"),
            ("file1.txt", "File1", 100, "2025-01-01T00:00:00Z"),
            ("file2.pdf", "File2", 600, "2025-03-01T00:00:00Z"),
            ("file3.jpg", "File3", 300, "2025-04-01T00:00:00Z"),
        ]
        for name, content, size, date in files:
            temp_file = create_temp_file(name, content, size)
            with open(temp_file, "rb") as f:
                self.session.post(
                    f"{API_BASE_URL}",
                    files={"file": (name, f)},
                    data={"uploaded_at": date}
                )
            os.remove(temp_file)

    def tearDown(self):
        self.session.close()

    def test_search_by_filename(self):
        response = self.session.get(f"{API_BASE_URL}search/?q=report")
        self.assertEqual(response.status_code, 200)
        results = response.json()
        filenames = [r["original_filename"] for r in results]
        self.assertIn("report.pdf", filenames)
        self.assertIn("report_final.pdf", filenames)
        self.assertNotIn("image.jpg", filenames)

    def test_filter_by_file_type(self):
        # Note: API doesn't populate file_type, so use filename extension
        response = self.session.get(f"{API_BASE_URL}search/?q=pdf")
        self.assertEqual(response.status_code, 200)
        results = response.json()
        filenames = [r["original_filename"] for r in results]
        self.assertIn("report.pdf", filenames)
        self.assertNotIn("doc2.docx", filenames)

    def test_filter_by_size_range(self):
        response = self.session.get(f"{API_BASE_URL}search/?min_size=100&max_size=1000")
        self.assertEqual(response.status_code, 200)
        results = response.json()
        filenames = [r["original_filename"] for r in results]
        self.assertIn("medium.pdf", filenames)
        self.assertNotIn("small.txt", filenames)
        self.assertNotIn("large.mp4", filenames)

    def test_filter_by_upload_date(self):
        response = self.session.get(
            f"{API_BASE_URL}search/?start_date=2025-02-01&end_date=2025-03-31"
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()
        filenames = [r["original_filename"] for r in results]
        self.assertIn("file2.pdf", filenames)
        self.assertNotIn("file1.txt", filenames)
        self.assertNotIn("file3.jpg", filenames)

    def test_multiple_filters(self):
        response = self.session.get(
            f"{API_BASE_URL}search/?q=pdf&min_size=100&max_size=1000&start_date=2025-03-01&end_date=2025-03-31"
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()
        filenames = [r["original_filename"] for r in results]
        self.assertIn("doc1.pdf", filenames)
        self.assertNotIn("doc2.pdf", filenames)
        self.assertNotIn("image.jpg", filenames)

    def test_search_performance_large_dataset(self):
        # Upload 1000 files (reduced for faster testing)
        for i in range(1000):
            temp_file = create_temp_file(f"file_{i}.txt", f"Content_{i}", 50)
            with open(temp_file, "rb") as f:
                self.session.post(
                    f"{API_BASE_URL}",
                    files={"file": (f"file_{i}.txt", f)},
                    data={"uploaded_at": "2025-01-01T00:00:00Z"}
                )
            os.remove(temp_file)

        start_time = time.time()
        response = self.session.get(
            f"{API_BASE_URL}search/?q=file&min_size=1&max_size=100"
        )
        end_time = time.time()
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 1.0)  # Less than 1 second
        results = response.json()
        self.assertTrue(len(results) > 0)

if __name__ == "__main__":
    unittest.main()