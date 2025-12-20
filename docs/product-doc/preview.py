#!/usr/bin/env python3
"""
Preview HTML templates by rendering them to static files.
Run: uv run docs/product-doc/preview.py
"""
import sys
from pathlib import Path

# Try to import Jinja2
try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("Installing jinja2...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "jinja2", "-q"])
    from jinja2 import Environment, FileSystemLoader

# Paths
SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
OUTPUT_DIR = SCRIPT_DIR / "preview"

# Ensure output dir exists
OUTPUT_DIR.mkdir(exist_ok=True)

# Setup Jinja2 with multiple template directories
env = Environment(loader=FileSystemLoader([
    str(TEMPLATES_DIR),
    str(TEMPLATES_DIR / "screens"),
]))

# Screens to render
SCREENS = [
    # Public screens
    "login.html",
    "accept-invitation.html",
    "forgot-password.html",
    "reset-password.html",
    # GP User screens
    "dashboard.html",
    "fund-list.html",
    "fund-detail.html",
    "fund-create.html",
    "lp-search.html",
    "lp-detail.html",
    "matches.html",
    "match-detail.html",
    "pitch-generator.html",
    "shortlist.html",
    "outreach-hub.html",
    "settings-profile.html",
    "settings-team.html",
    # Super Admin screens
    "admin-dashboard.html",
    "admin-companies.html",
    "admin-company-detail.html",
    "admin-users.html",
    "admin-people.html",
    "admin-lps.html",
    "admin-lp-detail.html",
    "admin-data-quality.html",
    "admin-import.html",
    "admin-health.html",
]

def render_all():
    """Render all screen templates to static HTML files."""
    for screen in SCREENS:
        template = env.get_template(screen)
        html = template.render()

        # Output filename
        output_name = screen
        output_path = OUTPUT_DIR / output_name

        output_path.write_text(html)
        print(f"Rendered: {output_path}")

    # Create index page
    create_index()

    print(f"\nPreview files in: {OUTPUT_DIR}")
    print(f"Open in browser: file://{OUTPUT_DIR}/index.html")


def create_index():
    """Create an index page linking to all mockups."""
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LPxGP - Screen Mockups</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    </style>
</head>
<body class="bg-slate-900 min-h-screen">
    <div class="max-w-5xl mx-auto px-6 py-12">
        <div class="text-center mb-12">
            <h1 class="text-4xl font-bold text-white mb-4">LPxGP</h1>
            <p class="text-xl text-slate-400">GP-LP Intelligence Platform</p>
            <p class="text-slate-500 mt-2">Screen Mockups & Design Preview</p>
            <p class="text-slate-600 mt-4 text-sm">27 screens | Conservative financial design</p>
        </div>

        <div class="grid gap-6">
            <!-- Public Screens -->
            <div class="bg-slate-800 rounded-lg p-6">
                <h2 class="text-lg font-semibold text-white mb-4">Public Screens (4)</h2>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <a href="login.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Login</div>
                        <div class="text-sm text-slate-400">User authentication</div>
                    </a>
                    <a href="accept-invitation.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Accept Invitation</div>
                        <div class="text-sm text-slate-400">New user onboarding</div>
                    </a>
                    <a href="forgot-password.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Forgot Password</div>
                        <div class="text-sm text-slate-400">Request reset link</div>
                    </a>
                    <a href="reset-password.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Reset Password</div>
                        <div class="text-sm text-slate-400">Create new password</div>
                    </a>
                </div>
            </div>

            <!-- GP User Screens -->
            <div class="bg-slate-800 rounded-lg p-6">
                <h2 class="text-lg font-semibold text-white mb-4">GP User Screens (13)</h2>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <a href="dashboard.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Dashboard</div>
                        <div class="text-sm text-slate-400">Fund overview & activity</div>
                    </a>
                    <a href="fund-list.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Fund List</div>
                        <div class="text-sm text-slate-400">All funds overview</div>
                    </a>
                    <a href="fund-detail.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Fund Detail</div>
                        <div class="text-sm text-slate-400">Fund profile & stats</div>
                    </a>
                    <a href="fund-create.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Create Fund</div>
                        <div class="text-sm text-slate-400">New fund form</div>
                    </a>
                    <a href="lp-search.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">LP Search</div>
                        <div class="text-sm text-slate-400">Search & filter LPs</div>
                    </a>
                    <a href="lp-detail.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">LP Detail</div>
                        <div class="text-sm text-slate-400">LP profile & contacts</div>
                    </a>
                    <a href="matches.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Matches</div>
                        <div class="text-sm text-slate-400">AI-ranked LP matches</div>
                    </a>
                    <a href="match-detail.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Match Analysis</div>
                        <div class="text-sm text-slate-400">AI insights & talking points</div>
                    </a>
                    <a href="pitch-generator.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Pitch Generator</div>
                        <div class="text-sm text-slate-400">AI-powered outreach</div>
                    </a>
                    <a href="shortlist.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Shortlist</div>
                        <div class="text-sm text-slate-400">LPs for outreach</div>
                    </a>
                    <a href="outreach-hub.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Outreach Hub</div>
                        <div class="text-sm text-slate-400">Activity & pipeline</div>
                    </a>
                    <a href="settings-profile.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Settings - Profile</div>
                        <div class="text-sm text-slate-400">User profile settings</div>
                    </a>
                    <a href="settings-team.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Settings - Team</div>
                        <div class="text-sm text-slate-400">Team management</div>
                    </a>
                </div>
            </div>

            <!-- Admin Screens -->
            <div class="bg-slate-800 rounded-lg p-6">
                <h2 class="text-lg font-semibold text-white mb-4">Super Admin Screens (10)</h2>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <a href="admin-dashboard.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Admin Dashboard</div>
                        <div class="text-sm text-slate-400">Platform overview</div>
                    </a>
                    <a href="admin-companies.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Companies</div>
                        <div class="text-sm text-slate-400">Manage GP firms</div>
                    </a>
                    <a href="admin-company-detail.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Company Detail</div>
                        <div class="text-sm text-slate-400">Company management</div>
                    </a>
                    <a href="admin-users.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Users</div>
                        <div class="text-sm text-slate-400">All platform users</div>
                    </a>
                    <a href="admin-people.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">People</div>
                        <div class="text-sm text-slate-400">LP contacts database</div>
                    </a>
                    <a href="admin-lps.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">LPs</div>
                        <div class="text-sm text-slate-400">LP database</div>
                    </a>
                    <a href="admin-lp-detail.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Edit LP</div>
                        <div class="text-sm text-slate-400">LP data management</div>
                    </a>
                    <a href="admin-data-quality.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Data Quality</div>
                        <div class="text-sm text-slate-400">Quality monitoring</div>
                    </a>
                    <a href="admin-import.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">Import Wizard</div>
                        <div class="text-sm text-slate-400">CSV import tool</div>
                    </a>
                    <a href="admin-health.html" class="block bg-slate-700 hover:bg-slate-600 rounded-lg p-4 transition">
                        <div class="text-white font-medium">System Health</div>
                        <div class="text-sm text-slate-400">Services & integrations</div>
                    </a>
                </div>
            </div>
        </div>

        <div class="text-center mt-12 text-slate-500 text-sm">
            <p>Conservative financial design | Built with Tailwind CSS</p>
            <p class="mt-2">&copy; 2024 LPxGP</p>
        </div>
    </div>
</body>
</html>'''

    index_path = OUTPUT_DIR / "index.html"
    index_path.write_text(index_html)
    print(f"Created index: {index_path}")

if __name__ == "__main__":
    render_all()
