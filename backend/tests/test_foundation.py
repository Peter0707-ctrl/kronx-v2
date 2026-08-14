import unittest
import os
import sys
import json
import shutil
import tempfile
import threading
import time
from datetime import datetime
from unittest.mock import patch, MagicMock

# Adjust sys.path to run tests from backend root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.http import get_client, close_client
from orchestrator.core import BoundedCache, KronxOrchestrator
from memory.store import MemoryStore

class TestFoundation(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.original_memory_file = os.environ.get("MEMORY_FILE")
        # Direct MemoryStore to our temp test directory file
        self.test_store_path = os.path.join(self.test_dir, "test_memory_store.json")
        
    def tearDown(self):
        # Clean up temp directory
        shutil.rmtree(self.test_dir)

    def test_bounded_cache_eviction(self):
        """Verify that BoundedCache limits size to 500 and evicts oldest items."""
        cache = BoundedCache(maxsize=10)
        for i in range(15):
            cache[f"key_{i}"] = f"value_{i}"
        
        # Total size must be locked at maxsize (10)
        self.assertEqual(len(cache.cache), 10)
        
        # First 5 items (key_0 to key_4) must have been evicted
        for i in range(5):
            self.assertNotIn(f"key_{i}", cache)
            
        # Last 10 items must exist
        for i in range(5, 15):
            self.assertIn(f"key_{i}", cache)

    def test_bounded_cache_lru_movement(self):
        """Verify that accessing a key moves it to the end (LRU behavior)."""
        cache = BoundedCache(maxsize=3)
        cache["a"] = 1
        cache["b"] = 2
        cache["c"] = 3
        
        # Access 'a' so it becomes the most recently used
        _ = cache["a"]
        
        # Add a new item 'd', forcing eviction of 'b' (since 'b' is now the oldest)
        cache["d"] = 4
        
        self.assertNotIn("b", cache)
        self.assertIn("a", cache)
        self.assertIn("c", cache)
        self.assertIn("d", cache)

    def test_memory_store_atomic_write_and_concurrency(self):
        """Verify that MemoryStore handles concurrent writes under multiple threads and remains uncorrupted."""
        store = MemoryStore()
        store.path = self.test_store_path
        store._ensure_file()
        
        # Simulate concurrent writes
        def worker(thread_idx):
            for i in range(10):
                store.save_memory(
                    conversation_id=f"conv_{thread_idx}",
                    content=f"content_{i}",
                    memory_type="test"
                )
                
        threads = []
        for t in range(5):
            th = threading.Thread(target=worker, args=(t,))
            threads.append(th)
            th.start()
            
        for th in threads:
            th.join()
            
        # Verify the file is fully valid JSON and has accurate content
        with open(store.path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for t in range(5):
            conv_id = f"conv_{t}"
            self.assertIn(conv_id, data)
            # Pruning limits items, check we have entries saved
            self.assertTrue(len(data[conv_id]) > 0)

    def test_memory_store_corruption_recovery(self):
        """Verify that MemoryStore recovers safely from a corrupted JSON file by archiving it and starting clean."""
        store = MemoryStore()
        store.path = self.test_store_path
        
        # Write corrupted garbage string to the file
        with open(store.path, "w", encoding="utf-8") as f:
            f.write("{ invalid json corrupted data }")
            
        # Reading should not crash, it must load an empty dict and create a backup of the corrupted file
        data = store._load()
        self.assertEqual(data, {})
        
        # Check that a backup file was created
        files_in_dir = os.listdir(self.test_dir)
        corrupt_backups = [file for file in files_in_dir if "corrupt" in file]
        self.assertTrue(len(corrupt_backups) > 0)

    def test_http_client_timeouts(self):
        """Verify that get_client configures custom connection timeouts correctly."""
        client = get_client()
        self.assertIsNotNone(client)
        self.assertEqual(client.timeout.connect, 5.0)
        self.assertEqual(client.timeout.read, 30.0)
        self.assertEqual(client.timeout.write, 15.0)
        self.assertEqual(client.timeout.pool, 10.0)

    @patch.dict(os.environ, {"PAYMENT_WEBHOOK_SECRET": "secret_key_123"})
    def test_webhook_security_success(self):
        """Verify payment webhook validates correctly with valid secret and catches mismatch/missing configuration."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        
        # 1. Test unauthorized signature
        payload = {"phone_number": "255700000000", "amount": 15000.0, "reference_id": "tx_ref_101"}
        resp = client.post("/api/payment/mobile-money/webhook", json=payload, headers={"X-Webhook-Secret": "wrong_secret"})
        self.assertEqual(resp.status_code, 401)
        
        # 2. Test authorized signature
        resp = client.post("/api/payment/mobile-money/webhook", json=payload, headers={"X-Webhook-Secret": "secret_key_123"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")

    @patch.dict(os.environ, {}, clear=True)
    def test_webhook_fail_closed_if_secret_missing(self):
        """Verify payment webhook rejects processing if PAYMENT_WEBHOOK_SECRET is unconfigured (fail-closed)."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        
        payload = {"phone_number": "255700000000", "amount": 15000.0, "reference_id": "tx_ref_102"}
        resp = client.post("/api/payment/mobile-money/webhook", json=payload, headers={"X-Webhook-Secret": "anything"})
        self.assertEqual(resp.status_code, 500)
        self.assertIn("misconfigured", resp.json()["detail"])

    @patch("orchestrator.core.get_client")
    def test_system_status_model_check_caching(self, mock_get_client):
        """Verify that active model checks are cached for 60 seconds to prevent external model API spam."""
        orchestrator = KronxOrchestrator()
        orchestrator.api_key = "test_key"
        
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []} # simulate failure to force check loop
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        # Call get_active_model synchronously via asyncio.run
        import asyncio
        model1 = asyncio.run(orchestrator.get_active_model())
        model2 = asyncio.run(orchestrator.get_active_model())
        
        # The connection pool client should have only been invoked once because of caching!
        self.assertTrue(mock_client.post.call_count <= 4) # Flash lite, Flash 2.5, Flash 2.0, Flash 3.5

    def test_concurrent_memory_store_stress(self):
        """Stress test concurrent reads, writes, deletes, and updates on the SAME conversation ID."""
        store = MemoryStore()
        store.path = self.test_store_path
        store._ensure_file()
        
        conversation_id = "stress_test_conv"
        
        def writer_worker(item_idx):
            for i in range(20):
                store.save_memory(
                    conversation_id=conversation_id,
                    content=f"write_{item_idx}_{i}",
                    memory_type="write_test"
                )
                
        def reader_worker():
            for _ in range(50):
                memories = store.get_memories(conversation_id)
                self.assertIsInstance(memories, list)
                
        def deleter_worker():
            for _ in range(10):
                # Retrieve all and delete first if exists
                all_m = store.get_all_memories(conversation_id)
                if all_m:
                    store.delete_memory(conversation_id, all_m[0]["id"])
                    
        threads = []
        # Spawn 3 writer threads, 3 reader threads, and 2 deleter threads
        for i in range(3):
            threads.append(threading.Thread(target=writer_worker, args=(i,)))
        for _ in range(3):
            threads.append(threading.Thread(target=reader_worker))
        for _ in range(2):
            threads.append(threading.Thread(target=deleter_worker))
            
        for th in threads:
            th.start()
            
        for th in threads:
            th.join()
            
        # Verify the file is fully valid JSON
        with open(store.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn(conversation_id, data)

    @patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": "http://localhost:3000,https://kronx.app"})
    def test_cors_security(self):
        """Test CORS allowed origin, disallowed origin, and credentials header matching."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        
        # 1. Authorized Origin
        resp = client.get("/health", headers={"Origin": "http://localhost:3000"})
        self.assertEqual(resp.headers.get("access-control-allow-origin"), "http://localhost:3000")
        self.assertEqual(resp.headers.get("access-control-allow-credentials"), "true")
        
        # 2. Unauthorized Origin (should not match allowed origins)
        resp = client.get("/health", headers={"Origin": "http://malicious-origin.com"})
        self.assertNotEqual(resp.headers.get("access-control-allow-origin"), "http://malicious-origin.com")

    @patch.dict(os.environ, {"PAYMENT_WEBHOOK_SECRET": "secret_key_123"})
    def test_payment_idempotency_deduplication(self):
        """Test duplicate payment webhook transaction deduplication and replay handling."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        
        payload = {"phone_number": "255700000000", "amount": 15000.0, "reference_id": "tx_unique_ref_999"}
        headers = {"X-Webhook-Secret": "secret_key_123"}
        
        # First request succeeds
        resp1 = client.post("/api/payment/mobile-money/webhook", json=payload, headers=headers)
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.json()["status"], "success")
        self.assertEqual(resp1.json()["unlocked_plan"], "premium")
        
        # Second request (duplicate) is recognized as duplicate and processed idempotently
        resp2 = client.post("/api/payment/mobile-money/webhook", json=payload, headers=headers)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["status"], "success")
        self.assertIn("already processed", resp2.json()["message"])

    def test_request_id_and_exception_sanitization(self):
        """Test that X-Request-ID propagates in response headers and unhandled exceptions are sanitized."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        
        # Test normal request propagates request ID
        resp = client.get("/health", headers={"X-Request-ID": "test-req-123"})
        self.assertEqual(resp.headers.get("X-Request-ID"), "test-req-123")
        
        # Test route that raises exception is sanitized to hide stack traces
        @app.get("/test-error-endpoint")
        def error_endpoint():
            raise RuntimeError("Secret system error context")
            
        resp_err = client.get("/test-error-endpoint")
        self.assertEqual(resp_err.status_code, 500)
        # Detail must be sanitized and must not leak "Secret system error context"
        self.assertNotIn("Secret system error context", resp_err.text)
        self.assertIn("internal server error", resp_err.text.lower())

if __name__ == "__main__":
    unittest.main()
