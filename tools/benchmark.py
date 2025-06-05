#!/usr/bin/env python3
"""
Performance benchmark for pCloud SDK Python v1.0
Tests upload/download speeds and SDK efficiency
"""

import os
import statistics
import tempfile
import time


def safe_print(text: str) -> None:
    """Print text with fallback for systems that don't support Unicode"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fall back to ASCII representation for Windows/other systems
        ascii_text = text.encode('ascii', 'replace').decode('ascii')
        print(ascii_text)


from typing import Any, Dict, List

from pcloud_sdk import PCloudException, PCloudSDK


class PerformanceTracker:
    """Tracker for measuring performance"""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.bytes_transferred = 0
        self.total_bytes = 0
        self.checkpoints = []

    def start(self, total_bytes: int = 0):
        """Start tracking"""
        self.start_time = time.time()
        self.total_bytes = total_bytes
        self.bytes_transferred = 0
        self.checkpoints = []

    def checkpoint(self, bytes_transferred: int):
        """Record a checkpoint"""
        now = time.time()
        if self.start_time:
            elapsed = now - self.start_time
            speed = bytes_transferred / elapsed if elapsed > 0 else 0
            self.checkpoints.append(
                {
                    "time": now,
                    "elapsed": elapsed,
                    "bytes": bytes_transferred,
                    "speed": speed,
                }
            )
        self.bytes_transferred = bytes_transferred

    def finish(self):
        """Finish tracking"""
        self.end_time = time.time()
        return self.get_stats()

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.start_time or not self.end_time:
            return {}

        total_time = self.end_time - self.start_time
        avg_speed = self.bytes_transferred / total_time if total_time > 0 else 0

        # Calculate instantaneous speeds
        instant_speeds = [cp["speed"] for cp in self.checkpoints if cp["speed"] > 0]

        stats = {
            "name": self.name,
            "total_time": total_time,
            "bytes_transferred": self.bytes_transferred,
            "total_bytes": self.total_bytes,
            "avg_speed_bps": avg_speed,
            "avg_speed_mbps": avg_speed / (1024 * 1024),
            "checkpoints_count": len(self.checkpoints),
        }

        if instant_speeds:
            stats.update(
                {
                    "min_speed_mbps": min(instant_speeds) / (1024 * 1024),
                    "max_speed_mbps": max(instant_speeds) / (1024 * 1024),
                    "median_speed_mbps": statistics.median(instant_speeds)
                    / (1024 * 1024),
                }
            )

        return stats


class PCloudBenchmark:
    """Main class for pCloud benchmarks"""

    def __init__(self, email: str, password: str, location_id: int = 2):
        """
        Initialize benchmark

        Args:
            email: pCloud email
            password: pCloud password
            location_id: Server (1=US, 2=EU)
        """
        self.email = email
        self.password = password
        self.location_id = location_id
        self.sdk = None
        self.test_files = []
        self.results = []

    def setup(self) -> bool:
        """Initialize pCloud connection"""
        try:
            safe_print("🔐 Connecting to pCloud...")
            self.sdk = PCloudSDK(token_manager=False)  # Avoid cache for clean tests
            login_info = self.sdk.login(self.email, self.password, self.location_id)

            server_name = "EU" if self.location_id == 2 else "US"
            safe_print(f"✅ Connected: {login_info['email']} ({server_name} server)")
            return True

        except PCloudException as e:
            safe_print(f"❌ Connection error: {e}")
            return False
        except Exception as e:
            safe_print(f"❌ Error: {e}")
            return False

    def create_test_files(self) -> List[Dict[str, Any]]:
        """Create test files of different sizes"""
        file_sizes = [
            (1024, "1KB"),  # 1 KB
            (10 * 1024, "10KB"),  # 10 KB
            (100 * 1024, "100KB"),  # 100 KB
            (1024 * 1024, "1MB"),  # 1 MB
            (5 * 1024 * 1024, "5MB"),  # 5 MB
            (10 * 1024 * 1024, "10MB"),  # 10 MB
        ]

        test_files = []

        print("📝 Creating test files...")

        for size_bytes, size_name in file_sizes:
            # Create file content
            content = os.urandom(size_bytes)  # Random data

            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode="wb", delete=False, suffix=f"_{size_name}.bin"
            ) as f:
                f.write(content)
                temp_path = f.name

            test_file = {
                "path": temp_path,
                "size_bytes": size_bytes,
                "size_name": size_name,
                "filename": f"benchmark_{size_name}.bin",
            }

            test_files.append(test_file)
            self.test_files.append(temp_path)  # For cleanup

            print(f"   ✅ {size_name}: {temp_path}")

        return test_files

    def benchmark_upload(
        self, test_file: Dict[str, Any], runs: int = 3
    ) -> List[Dict[str, Any]]:
        """Benchmark file upload"""
        results = []

        print(f"📤 Upload benchmark {test_file['size_name']} ({runs} runs)...")

        for run in range(runs):
            # Performance tracker with callback
            tracker = PerformanceTracker(
                f"Upload {test_file['size_name']} run {run + 1}"
            )

            def progress_callback(
                bytes_transferred, total_bytes, percentage, speed, **kwargs
            ):
                tracker.checkpoint(bytes_transferred)

            try:
                tracker.start(test_file["size_bytes"])

                upload_result = self.sdk.file.upload(
                    test_file["path"],
                    filename=f"{test_file['filename']}_run{run + 1}",
                    progress_callback=progress_callback,
                )

                stats = tracker.finish()

                if "metadata" in upload_result:
                    file_id = upload_result["metadata"]["fileid"]
                    stats["file_id"] = file_id
                    stats["run"] = run + 1
                    stats["success"] = True

                    results.append(stats)

                    print(
                        f"   Run {run + 1}: {stats['avg_speed_mbps']:.2f} MB/s "
                        f"({stats['total_time']:.2f}s)"
                    )

                    # Delete uploaded file to avoid clutter
                    try:
                        self.sdk.file.delete(file_id)
                    except:
                        pass

            except Exception as e:
                print(f"   ❌ Run {run + 1} failed: {e}")
                stats = tracker.get_stats()
                stats["run"] = run + 1
                stats["success"] = False
                stats["error"] = str(e)
                results.append(stats)

        return results

    def benchmark_download(
        self, test_file: Dict[str, Any], runs: int = 3
    ) -> List[Dict[str, Any]]:
        """Benchmark file download"""
        results = []

        print(f"📥 Download benchmark {test_file['size_name']} ({runs} runs)...")

        # First upload the file to download
        try:
            upload_result = self.sdk.file.upload(
                test_file["path"], filename=f"download_test_{test_file['filename']}"
            )

            if "metadata" not in upload_result:
                print(f"   ❌ Unable to upload file for download test")
                return []

            file_id = upload_result["metadata"]["fileid"]

            # Create temporary download directory
            download_dir = tempfile.mkdtemp()

            for run in range(runs):
                tracker = PerformanceTracker(
                    f"Download {test_file['size_name']} run {run + 1}"
                )

                def progress_callback(
                    bytes_transferred, total_bytes, percentage, speed, **kwargs
                ):
                    tracker.checkpoint(bytes_transferred)

                try:
                    tracker.start(test_file["size_bytes"])

                    success = self.sdk.file.download(
                        file_id, download_dir, progress_callback=progress_callback
                    )

                    stats = tracker.finish()
                    stats["run"] = run + 1
                    stats["success"] = success

                    if success:
                        results.append(stats)
                        print(
                            f"   Run {run + 1}: {stats['avg_speed_mbps']:.2f} MB/s "
                            f"({stats['total_time']:.2f}s)"
                        )
                    else:
                        print(f"   ❌ Run {run + 1} failed")

                except Exception as e:
                    print(f"   ❌ Run {run + 1} failed: {e}")
                    stats = tracker.get_stats()
                    stats["run"] = run + 1
                    stats["success"] = False
                    stats["error"] = str(e)
                    results.append(stats)

            # Cleanup
            try:
                self.sdk.file.delete(file_id)
                import shutil

                shutil.rmtree(download_dir)
            except:
                pass

        except Exception as e:
            print(f"   ❌ Error during download preparation: {e}")

        return results

    def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark"""
        if not self.setup():
            return {}

        print(f"\n🚀 Starting complete benchmark")
        print("=" * 50)

        # Create test files
        test_files = self.create_test_files()

        benchmark_results = {
            "timestamp": time.time(),
            "server": "EU" if self.location_id == 2 else "US",
            "upload_results": {},
            "download_results": {},
            "summary": {},
        }

        # Upload benchmarks
        print(f"\n📤 UPLOAD BENCHMARKS")
        print("-" * 30)

        for test_file in test_files:
            upload_results = self.benchmark_upload(test_file)
            benchmark_results["upload_results"][test_file["size_name"]] = upload_results

        # Download benchmarks
        print(f"\n📥 DOWNLOAD BENCHMARKS")
        print("-" * 30)

        for test_file in test_files:
            download_results = self.benchmark_download(test_file)
            benchmark_results["download_results"][
                test_file["size_name"]
            ] = download_results

        # Calculate summary
        benchmark_results["summary"] = self.calculate_summary(benchmark_results)

        return benchmark_results

    def calculate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate results summary"""
        summary = {"upload": {}, "download": {}}

        # Upload summary
        all_upload_speeds = []
        for size_name, runs in results["upload_results"].items():
            successful_runs = [r for r in runs if r.get("success", False)]
            if successful_runs:
                speeds = [r["avg_speed_mbps"] for r in successful_runs]
                summary["upload"][size_name] = {
                    "avg_speed_mbps": statistics.mean(speeds),
                    "min_speed_mbps": min(speeds),
                    "max_speed_mbps": max(speeds),
                    "successful_runs": len(successful_runs),
                    "total_runs": len(runs),
                }
                all_upload_speeds.extend(speeds)

        if all_upload_speeds:
            summary["upload"]["overall"] = {
                "avg_speed_mbps": statistics.mean(all_upload_speeds),
                "median_speed_mbps": statistics.median(all_upload_speeds),
            }

        # Download summary
        all_download_speeds = []
        for size_name, runs in results["download_results"].items():
            successful_runs = [r for r in runs if r.get("success", False)]
            if successful_runs:
                speeds = [r["avg_speed_mbps"] for r in successful_runs]
                summary["download"][size_name] = {
                    "avg_speed_mbps": statistics.mean(speeds),
                    "min_speed_mbps": min(speeds),
                    "max_speed_mbps": max(speeds),
                    "successful_runs": len(successful_runs),
                    "total_runs": len(runs),
                }
                all_download_speeds.extend(speeds)

        if all_download_speeds:
            summary["download"]["overall"] = {
                "avg_speed_mbps": statistics.mean(all_download_speeds),
                "median_speed_mbps": statistics.median(all_download_speeds),
            }

        return summary

    def display_results(self, results: Dict[str, Any]):
        """Display results in readable format"""
        print(f"\n📊 BENCHMARK RESULTS")
        print("=" * 50)

        server = results.get("server", "Unknown")
        print(f"🌍 Server: {server}")
        print(
            f"📅 Date: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}"
        )

        # Upload results
        print(f"\n📤 UPLOAD SPEEDS:")
        upload_summary = results["summary"].get("upload", {})

        for size_name in ["1KB", "10KB", "100KB", "1MB", "5MB", "10MB"]:
            if size_name in upload_summary:
                stats = upload_summary[size_name]
                print(
                    f"   {size_name:>6}: {stats['avg_speed_mbps']:6.2f} MB/s "
                    f"(min: {stats['min_speed_mbps']:5.2f}, max: {stats['max_speed_mbps']:5.2f}) "
                    f"[{stats['successful_runs']}/{stats['total_runs']} runs]"
                )

        if "overall" in upload_summary:
            overall = upload_summary["overall"]
            print(
                f"   {'OVERALL':>6}: {overall['avg_speed_mbps']:6.2f} MB/s "
                f"(median: {overall['median_speed_mbps']:5.2f})"
            )

        # Download results
        print(f"\n📥 DOWNLOAD SPEEDS:")
        download_summary = results["summary"].get("download", {})

        for size_name in ["1KB", "10KB", "100KB", "1MB", "5MB", "10MB"]:
            if size_name in download_summary:
                stats = download_summary[size_name]
                print(
                    f"   {size_name:>6}: {stats['avg_speed_mbps']:6.2f} MB/s "
                    f"(min: {stats['min_speed_mbps']:5.2f}, max: {stats['max_speed_mbps']:5.2f}) "
                    f"[{stats['successful_runs']}/{stats['total_runs']} runs]"
                )

        if "overall" in download_summary:
            overall = download_summary["overall"]
            print(
                f"   {'OVERALL':>6}: {overall['avg_speed_mbps']:6.2f} MB/s "
                f"(median: {overall['median_speed_mbps']:5.2f})"
            )

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")

        if "overall" in upload_summary and "overall" in download_summary:
            upload_speed = upload_summary["overall"]["avg_speed_mbps"]
            download_speed = download_summary["overall"]["avg_speed_mbps"]

            if upload_speed < 1.0:
                print("   📤 Upload: Low speed (<1MB/s) - check your upload connection")
            elif upload_speed < 5.0:
                print("   📤 Upload: Decent speed (1-5MB/s)")
            else:
                print("   📤 Upload: Excellent speed (>5MB/s)")

            if download_speed < 2.0:
                print("   📥 Download: Low speed (<2MB/s) - check your connection")
            elif download_speed < 10.0:
                print("   📥 Download: Decent speed (2-10MB/s)")
            else:
                print("   📥 Download: Excellent speed (>10MB/s)")

            if server == "US":
                print("   🌍 Tip: Try EU server (location_id=2) if you're in Europe")
            elif server == "EU":
                print("   🌍 Tip: Try US server (location_id=1) if you're in America")

    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.test_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        safe_print("🧹 Temporary files cleaned up")


def main():
    """Main entry point for benchmark"""
    safe_print("🚀 pCloud SDK Python v2.0 - Performance Benchmark")
    print("=" * 60)

    # Ask for credentials
    email = input("pCloud email: ").strip()
    password = input("Password: ").strip()

    if not email or not password:
        safe_print("❌ Email and password required")
        return 1

    # Choose server
    safe_print("🌍 Server to test:")
    print("  1. US (api.pcloud.com)")
    print("  2. EU (eapi.pcloud.com)")

    server_choice = input("Choose (1/2, default=2): ").strip() or "2"
    location_id = 2 if server_choice == "2" else 1

    # Run benchmark
    benchmark = PCloudBenchmark(email, password, location_id)

    try:
        results = benchmark.run_full_benchmark()

        if results:
            benchmark.display_results(results)

            # Offer to save results
            save_choice = input("\n💾 Save results? (y/N): ").lower().strip()
            if save_choice in ["y", "yes"]:
                import json

                filename = f"pcloud_benchmark_{int(time.time())}.json"
                with open(filename, "w") as f:
                    json.dump(results, f, indent=2)
                print(f"📁 Results saved to: {filename}")

            print("\n🎉 Benchmark completed successfully!")
            return 0
        else:
            print("\n❌ Benchmark failed")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️ Benchmark interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error during benchmark: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        benchmark.cleanup()


if __name__ == "__main__":
    import sys

    sys.exit(main())
