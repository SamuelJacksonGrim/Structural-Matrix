import os
import sys

# Make ``src`` importable without an editable install (keeps CI/web sessions simple).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
