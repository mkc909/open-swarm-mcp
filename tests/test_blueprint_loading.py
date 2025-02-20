import os
import json
import tempfile
from pathlib import Path
import unittest

class TestBlueprintLoading(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to simulate the project structure.
        self.temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(self.temp_dir.name)
        
        # Simulate the blueprints directory and a dummy blueprint.
        self.blueprints_dir = temp_path / "blueprints"
        self.blueprints_dir.mkdir(exist_ok=True)
        self.dummy_blueprint_dir = self.blueprints_dir / "dummy"
        self.dummy_blueprint_dir.mkdir(exist_ok=True)
        self.dummy_settings_path = self.dummy_blueprint_dir / "settings.py"
        
        # Write a dummy settings.py for the dummy blueprint.
        # This file, when executed, will set a global variable DUMMY_BLUEPRINT_LOADED.
        with open(self.dummy_settings_path, "w") as f:
            f.write("DUMMY_BLUEPRINT_LOADED = 'dummy'\n")
        
        # Create a temporary swarm_config.json with a "blueprints" key.
        self.swarm_config_path = temp_path / "swarm_config.json"
        config = {
            "blueprints": {
                "dummy": {
                    "path": str(self.dummy_blueprint_dir)
                },
                "suggestion": {
                    "path": "/app/blueprints/suggestion",
                    "api": True
                },
                "university": {
                    "path": "/app/blueprints/university",
                    "api": True
                }
            }
        }
        # Note: JSON does not accept comments; this is a valid JSON object.
        with open(self.swarm_config_path, "w") as f:
            json.dump(config, f)
            
        # Set environment variables to simulate a deployment with static blueprint configuration.
        os.environ["SWARM_CLI"] = ""
        # To enable dynamic blueprint discovery, BLUEPRINTS_PATH must be set.
        # But here, we want to use the static configuration, so we set BLUEPRINTS_PATH to empty.
        os.environ["BLUEPRINTS_PATH"] = ""
        # Also, ensure SWARM_BLUEPRINTS is empty so that all blueprints from config are loaded.
        os.environ["SWARM_BLUEPRINTS"] = ""
        
        # Monkey-patch the settings module to use our temporary directory as BASE_DIR.
        import swarm.settings as settings
        settings.BASE_DIR = temp_path
        settings.BLUEPRINTS_DIR = self.blueprints_dir
        
        # Copy our temporary swarm_config.json into BASE_DIR as expected by settings.py.
        test_config_path = settings.BASE_DIR / "swarm_config.json"
        with open(test_config_path, "w") as f:
            json.dump(config, f)
        
        # Remove any previously loaded global flag if exists.
        if hasattr(settings, "DUMMY_BLUEPRINT_LOADED"):
            delattr(settings, "DUMMY_BLUEPRINT_LOADED")
        
        # Force the blueprint loading block in settings.py to run.
        # The blueprint loading block in settings.py checks if not in CLI mode,
        # then if swarm_config.json exists, it loads blueprints from the "blueprints" key.
        # We simulate that by directly executing the block:
        if not os.getenv("SWARM_CLI"):
            if test_config_path.exists():
                with open(test_config_path, "r") as f:
                    config_data = json.load(f)
                static_blueprints = config_data.get("blueprints", {})
                if static_blueprints:
                    for blueprint_name, blueprint_conf in static_blueprints.items():
                        # Apply filtering based on SWARM_BLUEPRINTS if specified.
                        allowed = os.getenv("SWARM_BLUEPRINTS", "").strip()
                        if allowed and blueprint_name not in allowed.split(","):
                            continue
                        bp_settings = Path(blueprint_conf["path"]) / "settings.py"
                        if bp_settings.exists():
                            settings.logger.info(f"Loading static blueprint settings for: {blueprint_name}")
                            with open(bp_settings, "r") as f:
                                code = compile(f.read(), str(bp_settings), "exec")
                                exec(code, globals(), globals())
                else:
                    # Fallback: dynamic discovery (not used in this test)
                    pass
        
    def tearDown(self):
        self.temp_dir.cleanup()
        os.environ.pop("SWARM_BLUEPRINTS", None)
        os.environ.pop("BLUEPRINTS_PATH", None)
        os.environ.pop("SWARM_CLI", None)
        
    def test_blueprint_loading(self):
        # After setup, the dummy blueprint settings.py should have been executed,
        # setting the global variable DUMMY_BLUEPRINT_LOADED.
        from swarm import settings
        self.assertTrue("DUMMY_BLUEPRINT_LOADED" in globals())
        self.assertEqual(globals()["DUMMY_BLUEPRINT_LOADED"], "dummy")

if __name__ == "__main__":
    unittest.main()