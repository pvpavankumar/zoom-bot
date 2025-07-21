
import asyncio
import time
import sys
import os
from datetime import datetime

print("0000000000000")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
print("completed p1")


class StartupValidator:

    def __init__(self):
        print("1111111111111")
        self.results = []
        self.start_time = None
        print("completed p2")

    async def run_all_validations(self):
        print("2222222222222")

        print("🧪 STARTUP VALIDATION CHECKS")
        print("=" * 50)
        print("completed p3")

        self.start_time = time.time()
        print("3333333333333")

        validations = [
            ("Python Environment", self._validate_python_environment),
            ("Project Structure", self._validate_project_structure),
            ("Configuration", self._validate_configuration),
            ("Dependencies", self._validate_dependencies),
            ("Redis Connection", self._validate_redis),
            ("Audio System", self._validate_audio_system),
        ]

        for name, validator in validations:
            print(f"🔍 Validating {name}...")

            try:
                await validator()
                self.results.append({"name": name, "status": "PASSED", "error": None})
                print(f"✅ {name} validation passed")
            except Exception as e:
                self.results.append({"name": name, "status": "FAILED", "error": str(e)})
                print(f"❌ {name} validation failed: {e}")

        self._generate_summary()

        passed = len([r for r in self.results if r["status"] == "PASSED"])
        total = len(self.results)

        return passed == total

    async def _validate_python_environment(self):

        if sys.version_info < (3, 10):
            raise RuntimeError(f"Python 3.10+ required, got {sys.version}")

        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("⚠️ Not running in virtual environment")

    async def _validate_project_structure(self):

        required_dirs = ['src', 'tests', 'scripts']
        required_files = ['requirements.txt', 'README.md', '.env.example']

        project_root = os.path.join(os.path.dirname(__file__), '..')

        for dir_name in required_dirs:
            dir_path = os.path.join(project_root, dir_name)
            if not os.path.isdir(dir_path):
                raise FileNotFoundError(f"Required directory missing: {dir_name}")

        for file_name in required_files:
            file_path = os.path.join(project_root, file_name)
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"Required file missing: {file_name}")

    async def _validate_configuration(self):

        try:
            from src.core.config import settings

            required_settings = ['environment', 'host', 'port']

            for setting in required_settings:
                if not hasattr(settings, setting):
                    raise AttributeError(f"Missing configuration: {setting}")

        except Exception as e:
            raise RuntimeError(f"Configuration validation failed: {e}")

    async def _validate_dependencies(self):

        print(f"   📦 Checking Python package availability...")

        project_root = os.path.join(os.path.dirname(__file__), '..')
        requirements_path = os.path.join(project_root, 'requirements.txt')

        if not os.path.exists(requirements_path):
            raise FileNotFoundError("requirements.txt not found")

        try:
            import pkg_resources
            installed = [pkg.project_name for pkg in pkg_resources.working_set]
            print(f"   ✅ Found {len(installed)} installed packages")
        except:
            print(f"   ⚠️ Could not enumerate installed packages")

        critical_modules = ['fastapi', 'uvicorn', 'redis']
        available_count = 0

        for module in critical_modules:
            try:
                import importlib.util
                spec = importlib.util.find_spec(module)
                if spec is not None:
                    available_count += 1
            except:
                pass

        print(f"   ✅ Core modules available: {available_count}/{len(critical_modules)}")

        if available_count == 0:
            raise ImportError("No critical dependencies found - run 'pip install -r requirements.txt'")

    async def _validate_redis(self):

        try:
            import redis
            from src.core.config import settings

            client = redis.from_url(settings.redis_url)

            result = client.ping()
            if not result:
                raise ConnectionError("Redis ping failed")

        except Exception as e:
            print(f"⚠️ Redis connection issue: {e}")
            print("💡 Start Redis server for full functionality")

    async def _validate_audio_system(self):

        try:
            import sounddevice as sd

            devices = sd.query_devices()
            if not devices:
                raise RuntimeError("No audio devices detected")

            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            if not input_devices:
                print("⚠️ No input audio devices detected")

        except Exception as e:
            print(f"⚠️ Audio system issue: {e}")
            print("💡 Audio processing may be limited")

    def _generate_summary(self):

        total_time = time.time() - self.start_time
        passed = len([r for r in self.results if r["status"] == "PASSED"])
        failed = len([r for r in self.results if r["status"] == "FAILED"])
        total = len(self.results)

        print()
        print("📊 VALIDATION SUMMARY")
        print("-" * 30)
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {failed}/{total}")
        print(f"⏱️ Time: {total_time:.2f}s")

        if failed > 0:
            print()
            print("❌ FAILED VALIDATIONS:")
            for result in self.results:
                if result["status"] == "FAILED":
                    print(f"   • {result['name']}: {result['error']}")

        print()

        if failed == 0:
            print("🎉 ALL VALIDATIONS PASSED! Bot ready for startup.")
        else:
            print("⚠️ Some validations failed. Bot may have limited functionality.")


async def run_startup_tests():

    validator = StartupValidator()
    return await validator.run_all_validations()


if __name__ == "__main__":
    print("🧪 Zoom Interview Bot - Startup Validation")
    print()

    result = asyncio.run(run_startup_tests())

    if result:
        print("✅ Validation completed successfully")
        sys.exit(0)
    else:
        print("❌ Some validations failed")
        sys.exit(1)
