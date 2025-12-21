#!/usr/bin/env python3
"""
Build LPxGP Product Document PDF.

Run from /tmp/pdf-env:
    source /tmp/pdf-env/bin/activate
    python /home/tijn/code/lpxgp/docs/product-doc/build_pdf.py
"""
import asyncio
from pathlib import Path
from datetime import datetime

# Paths
SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
MOCKUPS_DIR = SCRIPT_DIR / "preview"
SCREENSHOTS_DIR = SCRIPT_DIR / "screenshots"
OUTPUT_PDF = SCRIPT_DIR.parent / "LPxGP-Product-Document.pdf"

# Screen definitions with metadata
SCREENS = {
    "public": [
        ("login.html", "Login", "User authentication page"),
        ("accept-invitation.html", "Accept Invitation", "New user onboarding flow"),
        ("forgot-password.html", "Forgot Password", "Password reset request"),
        ("reset-password.html", "Reset Password", "Create new password"),
    ],
    "gp_user": [
        ("dashboard.html", "Dashboard", "Fund overview and recent activity"),
        ("fund-list.html", "Funds", "List of all funds"),
        ("fund-detail.html", "Fund Detail", "Fund profile with thesis and track record"),
        ("fund-create.html", "Create Fund", "New fund creation form"),
        ("lp-search.html", "LP Search", "Search and filter institutional investors"),
        ("lp-detail.html", "LP Detail", "LP profile with mandate and contacts"),
        ("matches.html", "Matches", "AI-ranked LP matches for fund"),
        ("match-detail.html", "Match Analysis", "AI insights and talking points"),
        ("pitch-generator.html", "Pitch Generator", "AI-powered outreach content"),
        ("shortlist.html", "Shortlist", "LPs ready for outreach"),
        ("outreach-hub.html", "Outreach Hub", "Activity tracking and pipeline"),
        ("settings-profile.html", "Settings - Profile", "User profile settings"),
        ("settings-team.html", "Settings - Team", "Team member management"),
    ],
    "admin": [
        ("admin-dashboard.html", "Admin Dashboard", "Platform overview and health"),
        ("admin-companies.html", "Companies", "Manage GP firms on platform"),
        ("admin-company-detail.html", "Company Detail", "Company users and funds"),
        ("admin-users.html", "Users", "All platform users"),
        ("admin-people.html", "People", "LP contacts database"),
        ("admin-lps.html", "LPs", "Institutional investor database"),
        ("admin-lp-detail.html", "Edit LP", "LP data management form"),
        ("admin-data-quality.html", "Data Quality", "Quality monitoring and issues"),
        ("admin-import.html", "Import Wizard", "CSV import tool"),
        ("admin-health.html", "System Health", "Services and integrations status"),
    ],
}


async def take_screenshots():
    """Take screenshots of all HTML mockups using Playwright."""
    from playwright.async_api import async_playwright

    SCREENSHOTS_DIR.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        for category, screens in SCREENS.items():
            for filename, title, desc in screens:
                html_path = MOCKUPS_DIR / filename
                if not html_path.exists():
                    print(f"  Skipping {filename} (not found)")
                    continue

                await page.goto(f"file://{html_path}")
                await page.wait_for_timeout(500)  # Wait for Tailwind to load

                screenshot_path = SCREENSHOTS_DIR / filename.replace(".html", ".png")
                await page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"  Screenshot: {screenshot_path.name}")

        await browser.close()


def generate_pdf():
    """Generate PDF document with WeasyPrint."""
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration

    font_config = FontConfiguration()

    # Build HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>LPxGP Product Document</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        @page {{
            size: A4;
            margin: 2cm 2.5cm;
            @top-right {{
                content: "LPxGP Product Document";
                font-size: 9pt;
                color: #64748b;
            }}
            @bottom-center {{
                content: counter(page);
                font-size: 9pt;
                color: #64748b;
            }}
        }}

        @page :first {{
            @top-right {{ content: none; }}
            @bottom-center {{ content: none; }}
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #1e293b;
        }}

        /* Cover Page */
        .cover {{
            page-break-after: always;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            background: linear-gradient(135deg, #102a43 0%, #243b53 100%);
            color: white;
            margin: -2cm -2.5cm;
            padding: 3cm;
        }}

        .cover h1 {{
            font-size: 48pt;
            font-weight: 700;
            margin-bottom: 0.5em;
            letter-spacing: -0.02em;
        }}

        .cover .subtitle {{
            font-size: 18pt;
            font-weight: 400;
            opacity: 0.9;
            margin-bottom: 2em;
        }}

        .cover .date {{
            font-size: 12pt;
            opacity: 0.7;
        }}

        /* Headings */
        h1 {{
            font-size: 24pt;
            font-weight: 700;
            color: #102a43;
            margin-bottom: 0.5em;
            page-break-after: avoid;
        }}

        h2 {{
            font-size: 18pt;
            font-weight: 600;
            color: #243b53;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            page-break-after: avoid;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 0.3em;
        }}

        h3 {{
            font-size: 14pt;
            font-weight: 600;
            color: #334e68;
            margin-top: 1.2em;
            margin-bottom: 0.4em;
            page-break-after: avoid;
        }}

        p {{
            margin-bottom: 1em;
        }}

        ul, ol {{
            margin-left: 1.5em;
            margin-bottom: 1em;
        }}

        li {{
            margin-bottom: 0.3em;
        }}

        /* Table of Contents */
        .toc {{
            page-break-after: always;
        }}

        .toc h1 {{
            margin-bottom: 1em;
        }}

        .toc-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.4em 0;
            border-bottom: 1px dotted #cbd5e1;
        }}

        .toc-section {{
            font-weight: 600;
            color: #102a43;
            margin-top: 1em;
        }}

        /* Section styling */
        .section {{
            page-break-before: always;
        }}

        .section:first-of-type {{
            page-break-before: avoid;
        }}

        /* Screen mockup */
        .screen {{
            page-break-inside: avoid;
            margin-bottom: 2em;
            page-break-before: always;
        }}

        .screen-header {{
            background: #f1f5f9;
            padding: 1em;
            border-radius: 8px 8px 0 0;
            border: 1px solid #e2e8f0;
            border-bottom: none;
        }}

        .screen-title {{
            font-size: 14pt;
            font-weight: 600;
            color: #102a43;
            margin: 0;
        }}

        .screen-desc {{
            font-size: 10pt;
            color: #64748b;
            margin-top: 0.3em;
        }}

        .screen-image {{
            border: 1px solid #e2e8f0;
            border-radius: 0 0 8px 8px;
            overflow: hidden;
        }}

        .screen-image img {{
            width: 100%;
            display: block;
        }}

        /* Info boxes */
        .info-box {{
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 8px;
            padding: 1em;
            margin: 1em 0;
        }}

        .highlight-box {{
            background: #fef3c7;
            border: 1px solid #fcd34d;
            border-radius: 8px;
            padding: 1em;
            margin: 1em 0;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
            font-size: 10pt;
        }}

        th, td {{
            padding: 0.6em 0.8em;
            text-align: left;
            border: 1px solid #e2e8f0;
        }}

        th {{
            background: #f1f5f9;
            font-weight: 600;
            color: #102a43;
        }}

        /* Category headers */
        .category-header {{
            background: #102a43;
            color: white;
            padding: 1em 1.5em;
            border-radius: 8px;
            margin: 2em 0 1em 0;
            page-break-after: avoid;
        }}

        .category-header h2 {{
            color: white;
            border: none;
            margin: 0;
            padding: 0;
        }}

        .category-count {{
            font-size: 10pt;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <!-- Cover Page -->
    <div class="cover">
        <h1>LPxGP</h1>
        <div class="subtitle">GP-LP Intelligence Platform<br>Product Document</div>
        <div class="date">Generated: {datetime.now().strftime("%B %d, %Y")}</div>
    </div>

    <!-- Table of Contents -->
    <div class="toc">
        <h1>Table of Contents</h1>

        <div class="toc-section">1. Executive Summary</div>
        <div class="toc-item"><span>Overview</span></div>
        <div class="toc-item"><span>Problem Statement</span></div>
        <div class="toc-item"><span>Solution</span></div>

        <div class="toc-section">2. User Personas</div>
        <div class="toc-item"><span>GP Fund Manager (Company Admin)</span></div>
        <div class="toc-item"><span>GP Associate (Company Member)</span></div>
        <div class="toc-item"><span>Super Admin (LPxGP Team)</span></div>

        <div class="toc-section">3. User Journeys</div>
        <div class="toc-item"><span>Platform Onboarding (Super Admin)</span></div>
        <div class="toc-item"><span>New User Onboarding (GP Admin)</span></div>
        <div class="toc-item"><span>Fund Creation</span></div>
        <div class="toc-item"><span>LP Research</span></div>
        <div class="toc-item"><span>AI Matching</span></div>
        <div class="toc-item"><span>Pitch Generation</span></div>

        <div class="toc-section">4. Screen Mockups</div>
        <div class="toc-item"><span>Public Screens (4)</span></div>
        <div class="toc-item"><span>GP User Screens (13)</span></div>
        <div class="toc-item"><span>Super Admin Screens (10)</span></div>

        <div class="toc-section">5. Technical Architecture</div>
        <div class="toc-item"><span>System Overview</span></div>
        <div class="toc-item"><span>Technology Stack</span></div>

        <div class="toc-section">6. Milestones</div>
        <div class="toc-item"><span>M0 - M5 Roadmap</span></div>
    </div>

    <!-- Executive Summary -->
    <div class="section">
        <h1>1. Executive Summary</h1>

        <h2>Overview</h2>
        <p>LPxGP is an AI-powered intelligence platform that helps investment fund managers (General Partners, or GPs)
        find and engage the right institutional investors (Limited Partners, or LPs) for their funds.</p>

        <div class="info-box">
            <strong>Domain:</strong> lpxgp.com<br>
            <strong>Target Users:</strong> Private equity, venture capital, and growth equity fund managers
        </div>

        <h2>Problem Statement</h2>
        <p>Fund managers face significant challenges in the fundraising process:</p>
        <ul>
            <li><strong>Information Overload:</strong> Thousands of institutional investors with varying mandates, preferences, and allocation strategies</li>
            <li><strong>Manual Research:</strong> Hours spent researching LP mandates, recent commitments, and contact information</li>
            <li><strong>Poor Targeting:</strong> Wasted meetings with misaligned investors who don't invest in the fund's strategy or size</li>
            <li><strong>Generic Outreach:</strong> One-size-fits-all pitch materials that don't resonate with specific LP priorities</li>
        </ul>

        <h2>Solution</h2>
        <p>LPxGP provides an intelligent matching and outreach platform:</p>

        <table>
            <tr>
                <th>Feature</th>
                <th>Benefit</th>
            </tr>
            <tr>
                <td>LP Database</td>
                <td>5,000+ institutional investors with mandates, AUM, and contacts</td>
            </tr>
            <tr>
                <td>AI Matching</td>
                <td>Semantic search matches fund thesis to LP mandates</td>
            </tr>
            <tr>
                <td>Match Scoring</td>
                <td>Ranked list of LPs by fit score with explanation</td>
            </tr>
            <tr>
                <td>Pitch Generation</td>
                <td>AI-generated personalized outreach for each LP</td>
            </tr>
            <tr>
                <td>Outreach Tracking</td>
                <td>Pipeline management for fundraising campaigns</td>
            </tr>
        </table>

        <div class="highlight-box">
            <strong>Key Value Proposition:</strong> Reduce time-to-first-close by helping GPs focus on the highest-probability LP targets with personalized, relevant outreach.
        </div>
    </div>

    <!-- User Personas -->
    <div class="section">
        <h1>2. User Personas</h1>

        <h2>GP Fund Manager (Company Admin)</h2>
        <p><strong>Role:</strong> Managing Partner or Partner at a PE/VC firm</p>
        <p><strong>Goals:</strong></p>
        <ul>
            <li>Raise capital for new funds efficiently</li>
            <li>Build relationships with institutional investors</li>
            <li>Track fundraising pipeline across the team</li>
        </ul>
        <p><strong>Platform Access:</strong> Full access including fund creation, team management, and all LP features</p>

        <h2>GP Associate (Company Member)</h2>
        <p><strong>Role:</strong> Associate or VP supporting fundraising efforts</p>
        <p><strong>Goals:</strong></p>
        <ul>
            <li>Research and identify potential LP targets</li>
            <li>Prepare meeting materials and pitches</li>
            <li>Support partners with data and analysis</li>
        </ul>
        <p><strong>Platform Access:</strong> LP search, matching, and pitch generation (read-only for fund settings)</p>

        <h2>Super Admin (LPxGP Team)</h2>
        <p><strong>Role:</strong> LPxGP platform administrator</p>
        <p><strong>Goals:</strong></p>
        <ul>
            <li>Onboard new GP firms to the platform</li>
            <li>Maintain and improve LP database quality</li>
            <li>Monitor platform health and usage</li>
        </ul>
        <p><strong>Platform Access:</strong> Full administrative access across all companies</p>
    </div>

    <!-- User Journeys -->
    <div class="section">
        <h1>3. User Journeys</h1>
        <p>This section describes the key user experience flows through the LPxGP platform, connecting screens with user goals and tested behaviors.</p>

        <h2>Journey 1: Platform Onboarding (Super Admin)</h2>
        <p><strong>Actor:</strong> Sarah, LPxGP Super Admin</p>
        <p><strong>Goal:</strong> Onboard a new GP firm to the platform</p>
        <div class="info-box">
            <strong>Screen Flow:</strong> Admin Dashboard → Companies → Create Company → Company Detail → Invite Admin
        </div>
        <p><strong>Story:</strong> Sarah receives a request from Acme Capital to join LPxGP. She reviews platform health on the Admin Dashboard, navigates to Companies, creates the new company profile, and invites John (Partner) as the company admin via email invitation.</p>
        <p><strong>Tested Behaviors:</strong> F-AUTH-04 (Company creation, user invitation), duplicate company name rejection, invalid email format rejection.</p>

        <h2>Journey 2: New User Onboarding (GP Admin)</h2>
        <p><strong>Actor:</strong> John, Partner at Acme Capital</p>
        <p><strong>Goal:</strong> Accept invitation and set up account</p>
        <div class="info-box">
            <strong>Screen Flow:</strong> Email Invitation → Accept Invitation → Login → Dashboard
        </div>
        <p><strong>Story:</strong> John receives an invitation email, clicks the link to accept, creates a secure password, and lands on his empty dashboard ready to create his first fund.</p>
        <p><strong>Tested Behaviors:</strong> F-AUTH-05 (Invitation acceptance), F-AUTH-01 (Login), expired invitation rejection, weak password rejection, account lockout after 5 failed attempts.</p>

        <h2>Journey 3: Fund Creation</h2>
        <p><strong>Actor:</strong> John, Partner at Acme Capital</p>
        <p><strong>Goal:</strong> Create fund profile for Growth Fund III</p>
        <div class="info-box">
            <strong>Screen Flow:</strong> Dashboard → Create Fund → Upload Deck → AI Extraction → Fund Detail
        </div>
        <p><strong>Story:</strong> John clicks "+ New Fund" on his dashboard, uploads a pitch deck PDF. The AI extracts fund information (strategy, size, thesis) with confidence scores. John reviews and confirms each field, especially low-confidence items, then views his completed fund profile.</p>
        <p><strong>Tested Behaviors:</strong> F-GP-01 (Fund creation), F-GP-02 (Deck upload), F-GP-03 (AI extraction), corrupt file rejection, API timeout graceful handling, missing required fields blocked.</p>

        <h2>Journey 4: LP Research</h2>
        <p><strong>Actor:</strong> Maria, Associate at Acme Capital</p>
        <p><strong>Goal:</strong> Find LPs matching Growth Fund III criteria</p>
        <div class="info-box">
            <strong>Screen Flow:</strong> Dashboard → LP Search → Apply Filters → LP Detail → Add to Shortlist
        </div>
        <p><strong>Story:</strong> Maria navigates to Search, applies filters (Strategy: Growth Equity, Check Size > $10M, Geography: North America), reviews 45 matching LPs with relevance scores, clicks on CalPERS to view full profile with mandate and contacts, then adds CalPERS to the shortlist.</p>
        <p><strong>Tested Behaviors:</strong> F-LP-02 (Filters), F-LP-03 (Semantic search), F-UI-03 (HTMX updates), performance < 500ms, empty query handling, special characters handling.</p>

        <h2>Journey 5: AI Matching</h2>
        <p><strong>Actor:</strong> Maria, Associate at Acme Capital</p>
        <p><strong>Goal:</strong> Get AI-ranked LP matches for Growth Fund III</p>
        <div class="info-box">
            <strong>Screen Flow:</strong> Fund Detail → Matches → Match Detail → Review Insights
        </div>
        <p><strong>Story:</strong> Maria clicks "View Matches" for Growth Fund III, sees 45 LPs ranked by fit score (0-100). She clicks on CalPERS (score: 87) to see the breakdown: strategy alignment, size fit, geographic overlap, and semantic similarity. The AI provides talking points and identifies potential concerns.</p>
        <p><strong>Tested Behaviors:</strong> F-MATCH-01 (Hard filters), F-MATCH-02 (Soft scoring), F-MATCH-03 (Semantic matching), F-MATCH-04 (Explanations), no matches handling, API timeout fallback.</p>

        <h2>Journey 6: Pitch Generation</h2>
        <p><strong>Actor:</strong> Maria, Associate at Acme Capital</p>
        <p><strong>Goal:</strong> Create personalized outreach for CalPERS</p>
        <div class="info-box">
            <strong>Screen Flow:</strong> Match Detail → Pitch Generator → Generate → Review & Edit → Copy to Clipboard
        </div>
        <p><strong>Story:</strong> Maria clicks "Generate Pitch" from the match detail page, selects "Outreach Email" as the output type. The AI generates a personalized email referencing CalPERS's recent allocations. Maria edits the subject line and call-to-action, then copies to clipboard for use in her email client.</p>
        <p><strong>Tested Behaviors:</strong> F-PITCH-01 (Executive summary), F-PITCH-02 (Email draft), F-HITL-01 (No auto-send), API rate limiting handled, missing LP data graceful degradation, clipboard permission issues handled.</p>

        <div class="highlight-box">
            <strong>Human-in-the-Loop Design:</strong> All AI-generated content requires human review before use. There is no auto-send functionality - users must copy to clipboard and paste into their email client. This ensures quality control and compliance with professional communication standards.
        </div>
    </div>

    <!-- Screen Mockups -->
    <div class="section">
        <h1>4. Screen Mockups</h1>
        <p>The following pages show all 27 screens in the LPxGP platform, organized by user type. Each screen includes context about its role in the user journeys above.</p>
"""

    # Add screen mockups by category
    category_names = {
        "public": ("Public Screens", "Authentication and onboarding flows"),
        "gp_user": ("GP User Screens", "Core platform functionality for fund managers"),
        "admin": ("Super Admin Screens", "Platform administration and data management"),
    }

    for category, screens in SCREENS.items():
        cat_name, cat_desc = category_names[category]
        html_content += f"""
        <div class="category-header">
            <h2>{cat_name}</h2>
            <div class="category-count">{len(screens)} screens - {cat_desc}</div>
        </div>
"""
        for filename, title, desc in screens:
            screenshot_path = SCREENSHOTS_DIR / filename.replace(".html", ".png")
            if screenshot_path.exists():
                html_content += f"""
        <div class="screen">
            <div class="screen-header">
                <div class="screen-title">{title}</div>
                <div class="screen-desc">{desc}</div>
            </div>
            <div class="screen-image">
                <img src="file://{screenshot_path}" alt="{title}">
            </div>
        </div>
"""

    # Add Technical Architecture section
    html_content += """
    </div>

    <!-- Technical Architecture -->
    <div class="section">
        <h1>5. Technical Architecture</h1>

        <h2>System Overview</h2>
        <p>LPxGP is built as a modern web application with the following architecture:</p>

        <div class="info-box">
            <pre style="font-family: monospace; font-size: 9pt; white-space: pre;">
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Browser       │────▶│   Railway       │────▶│   Supabase      │
│   (HTMX)        │◀────│   (FastAPI)     │◀────│   (PostgreSQL)  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │OpenRouter│ │ Voyage   │ │ Supabase │
             │(LLMs)    │ │ AI       │ │ Auth     │
             └──────────┘ └──────────┘ └──────────┘
            </pre>
        </div>

        <h2>Technology Stack</h2>
        <table>
            <tr>
                <th>Layer</th>
                <th>Technology</th>
                <th>Purpose</th>
            </tr>
            <tr>
                <td>Backend</td>
                <td>Python + FastAPI</td>
                <td>API server and business logic</td>
            </tr>
            <tr>
                <td>Frontend</td>
                <td>Jinja2 + HTMX + Tailwind</td>
                <td>Server-rendered UI with dynamic updates</td>
            </tr>
            <tr>
                <td>Database</td>
                <td>Supabase (PostgreSQL)</td>
                <td>Data storage with pgvector for embeddings</td>
            </tr>
            <tr>
                <td>Auth</td>
                <td>Supabase Auth</td>
                <td>Invite-only authentication with RLS</td>
            </tr>
            <tr>
                <td>LLM</td>
                <td>OpenRouter (Claude)</td>
                <td>Pitch generation and analysis</td>
            </tr>
            <tr>
                <td>Embeddings</td>
                <td>Voyage AI</td>
                <td>Semantic search for LP matching</td>
            </tr>
            <tr>
                <td>Hosting</td>
                <td>Railway</td>
                <td>Auto-deploy from GitHub</td>
            </tr>
        </table>

        <h2>Security Model</h2>
        <ul>
            <li><strong>Invite-Only Access:</strong> Users can only join via company admin invitation</li>
            <li><strong>Row-Level Security:</strong> Database policies ensure users only see their company's data</li>
            <li><strong>Role-Based Access:</strong> Company Admins vs Members vs Super Admins</li>
            <li><strong>Human-in-the-Loop:</strong> All AI-generated content requires review before use</li>
        </ul>
    </div>

    <!-- Milestones -->
    <div class="section">
        <h1>6. Milestones</h1>

        <p>LPxGP is developed in six milestones, each delivering independently demoable functionality:</p>

        <table>
            <tr>
                <th>Milestone</th>
                <th>Focus</th>
                <th>Key Deliverables</th>
            </tr>
            <tr>
                <td><strong>M0</strong></td>
                <td>Foundation</td>
                <td>Project setup, data model, LP import pipeline</td>
            </tr>
            <tr>
                <td><strong>M1</strong></td>
                <td>Auth + Search</td>
                <td>Supabase Auth, basic LP search, Railway deployment</td>
            </tr>
            <tr>
                <td><strong>M2</strong></td>
                <td>Semantic Search</td>
                <td>Voyage AI embeddings, pgvector similarity search</td>
            </tr>
            <tr>
                <td><strong>M3</strong></td>
                <td>Matching</td>
                <td>Fund profiles, LP matching algorithm, score explanations</td>
            </tr>
            <tr>
                <td><strong>M4</strong></td>
                <td>Pitch Generation</td>
                <td>OpenRouter integration, AI summaries, email drafts</td>
            </tr>
            <tr>
                <td><strong>M5</strong></td>
                <td>Production</td>
                <td>Admin panel, data quality, monitoring, polish</td>
            </tr>
        </table>

        <div class="highlight-box">
            <strong>Current Status:</strong> Ready for Milestone 0 implementation
        </div>
    </div>

</body>
</html>
"""

    # Generate PDF
    print("Generating PDF...")
    html = HTML(string=html_content, base_url=str(SCRIPT_DIR))
    html.write_pdf(str(OUTPUT_PDF), font_config=font_config)
    print(f"PDF saved to: {OUTPUT_PDF}")


async def main():
    print("LPxGP Product Document Generator")
    print("=" * 40)

    print("\n1. Taking screenshots...")
    await take_screenshots()

    print("\n2. Generating PDF...")
    generate_pdf()

    print("\n" + "=" * 40)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
