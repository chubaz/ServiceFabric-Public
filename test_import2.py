import sys
import importlib.util
import importlib.machinery
from pathlib import Path

catalog_path = Path("6_service_catalog").resolve()
item = catalog_path / "lazio-flask"
init_file = item / "__init__.py"

# Make sure the parent package is in sys.modules
parent_pkg = "dynamic_catalog"
if parent_pkg not in sys.modules:
    spec = importlib.machinery.ModuleSpec(parent_pkg, None, is_package=True)
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(catalog_path)]
    sys.modules[parent_pkg] = module

# Now load the service as a package
service_name = item.name.replace("-", "_")  # Hyphens can cause problems?
module_name = f"{parent_pkg}.{service_name}"

spec = importlib.util.spec_from_file_location(
    module_name, 
    str(init_file), 
    submodule_search_locations=[str(item)]
)
module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = module
spec.loader.exec_module(module)

print("Blueprint loaded:", getattr(module, 'bp'))
