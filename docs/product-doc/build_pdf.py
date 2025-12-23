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
MOCKUPS_DIR = SCRIPT_DIR.parent / "mockups"
SCREENSHOTS_DIR = SCRIPT_DIR / "screenshots"
OUTPUT_PDF = SCRIPT_DIR.parent / "LPxGP-Product-Document.pdf"

# Screen definitions with comprehensive metadata
# Format: (filename, title, short_desc, full_explanation)
SCREENS = {
    "public": [
        ("login.html", "Login", "User authentication",
         """The Login screen is the entry point for all authenticated users. Users enter their email and password to access the platform. The design emphasizes security and trust with a clean, professional interface. Failed login attempts are tracked and accounts are locked after 5 consecutive failures to prevent brute-force attacks. A "Forgot Password" link provides account recovery options."""),

        ("accept-invitation.html", "Accept Invitation", "New user onboarding",
         """This screen appears when a user clicks an invitation link from their email. Since LPxGP is invite-only, this is the only way to create an account. Users set their password and confirm their details. The invitation token is validated server-side to ensure security. Expired or already-used tokens show appropriate error messages."""),

        ("forgot-password.html", "Forgot Password", "Request reset link",
         """Users who cannot remember their password can request a reset link. They enter their email address and receive a secure, time-limited reset link. The form includes rate limiting to prevent abuse. For security, the same success message is shown whether or not the email exists in the system."""),

        ("reset-password.html", "Reset Password", "Create new password",
         """After clicking the reset link from their email, users land on this screen to set a new password. Password strength requirements are enforced (minimum 8 characters, mix of letters and numbers). The reset token is validated and expires after use to ensure security."""),
    ],
    "gp_user": [
        ("dashboard.html", "Dashboard", "Fund overview and activity",
         """The Dashboard is the command center for fund managers. It provides an at-a-glance view of all funds, recent matching activity, and quick access to key features. Users see fund cards showing name, status (Raising/Investing/Harvesting), target size, and match statistics. Recent activity includes new matches, shortlist additions, and outreach updates. The "+ New Fund" button provides quick access to fund creation."""),

        ("fund-list.html", "Funds", "List of all funds",
         """The Funds screen shows all funds belonging to the user's company. Each fund card displays key metrics: fund name, status, target size, number of LP matches, and last activity date. Users can filter by status or search by name. Clicking a fund card navigates to the Fund Detail view. Company admins can see all company funds; members see funds they're assigned to."""),

        ("fund-detail.html", "Fund Detail", "Fund profile with thesis and track record",
         """The Fund Detail screen is the comprehensive profile for a single fund. It displays the fund thesis, investment strategy, geographic focus, target size, and track record of notable exits. A sidebar shows matching statistics and quick actions (View Matches, Generate Pitch). Company admins can edit fund details; members have read-only access. This is the primary context for LP matching and outreach activities."""),

        ("fund-create.html", "Create Fund", "New fund creation form",
         """The Create Fund screen enables users to set up a new fund profile. Users can either manually enter fund details or upload a pitch deck (PDF/PPTX) for AI-assisted extraction. When a deck is uploaded, the system uses Claude to extract fund name, strategy, thesis, target size, and other details. Extracted fields show confidence scores, allowing users to review and correct low-confidence items before saving."""),

        ("lp-search.html", "LP Search", "Search and filter institutional investors",
         """LP Search is the primary research tool for finding potential investors. Users can search by keyword or use natural language queries like "technology growth equity investors in North America." Advanced filters allow narrowing by LP type (pension, endowment, family office), AUM range, typical check size, geographic focus, and strategy preferences. Results show relevance scores and key LP attributes. Users can add promising LPs to their shortlist or view full profiles."""),

        ("lp-detail.html", "LP Detail", "LP profile with mandate and contacts",
         """The LP Detail screen provides comprehensive information about an institutional investor. It displays the LP's investment mandate, AUM, allocation targets, geographic preferences, and recent fund commitments. The Contacts section shows key personnel with titles and roles. Users can add the LP to their shortlist, generate a personalized pitch, or view matching scores against their funds. This screen is essential for research before outreach."""),

        ("matches.html", "Matches", "AI-ranked LP matches for fund",
         """The Matches screen shows AI-generated LP recommendations for a specific fund. LPs are ranked by a fit score (0-100) calculated from strategy alignment, size fit, geographic overlap, and semantic similarity between fund thesis and LP mandate. Each match card shows the score, LP name, type, AUM, and key alignment indicators (checkmarks for strong fits, warnings for concerns). Users can filter by score range, sort by different criteria, and bulk-add matches to their shortlist."""),

        ("match-detail.html", "Match Analysis", "AI insights and talking points",
         """The Match Detail screen explains why a specific LP is recommended for a fund. It breaks down the match score into components: strategy alignment, size compatibility, geographic fit, and semantic similarity. The AI generates talking points highlighting what to emphasize in outreach and identifies potential concerns to address proactively. Recent LP activity (if available) helps users time their outreach. A "Generate Pitch" button launches personalized content creation."""),

        ("pitch-generator.html", "Pitch Generator", "AI-powered outreach content",
         """The Pitch Generator uses Claude to create personalized outreach content for specific LP-fund combinations. Users select the output type: Executive Summary (1-page overview), Outreach Email (introduction message), or Talking Points (meeting preparation). The AI references the LP's mandate, recent activity, and the fund's thesis to create relevant, personalized content. All generated content is editable before copying to clipboard. There is no auto-send - this ensures human review of all outreach."""),

        ("shortlist.html", "Shortlist", "LPs ready for outreach",
         """The Shortlist is a curated collection of LPs the user has identified for potential outreach. It serves as a working list for fundraising campaigns. Users can organize LPs, add notes, track outreach status, and generate pitches in bulk. The shortlist persists across sessions and can be shared with team members. Quick actions allow moving LPs through the pipeline: Not Started → Contacted → Meeting Scheduled → In Diligence → Committed."""),

        ("outreach-hub.html", "Outreach Hub", "Activity tracking and pipeline",
         """The Outreach Hub provides a kanban-style view of the fundraising pipeline. LPs are organized by status: Identified, Contacted, Meeting Scheduled, In Diligence, and Committed. Users can drag-and-drop LPs between stages, log activities (calls, emails, meetings), and track commitment amounts. Summary metrics show pipeline progress and conversion rates. This screen helps teams coordinate outreach and measure fundraising progress."""),

        ("settings-profile.html", "Settings - Profile", "User profile settings",
         """The Profile Settings screen allows users to manage their personal information: name, email, title, and notification preferences. Users can change their password and manage two-factor authentication. The screen also shows account activity and login history for security awareness. All changes require current password confirmation for security."""),

        ("settings-team.html", "Settings - Team", "Team member management",
         """The Team Settings screen is available to Company Admins and allows them to manage team access. Admins can invite new team members by email, assign roles (Admin or Member), and deactivate accounts. The member list shows names, emails, roles, and last activity. Admins can also manage fund assignments, controlling which team members can access which funds."""),
    ],
    "admin": [
        ("admin-dashboard.html", "Admin Dashboard", "Platform overview and health",
         """The Admin Dashboard provides Super Admins with a bird's-eye view of the entire LPxGP platform. Key metrics include total companies, users, funds, and LPs in the database. System health indicators show API status, database performance, and external service connectivity. Recent activity logs show new company signups, user invitations, and data imports. Quick actions provide access to common admin tasks."""),

        ("admin-companies.html", "Companies", "Manage GP firms on platform",
         """The Companies screen lists all GP firms registered on LPxGP. Admins can view company details, user counts, fund counts, and subscription status. Search and filter options help find specific companies. Actions include creating new companies, viewing company details, and managing billing. This is the primary customer management interface for platform administrators."""),

        ("admin-company-detail.html", "Company Detail", "Company users and funds",
         """The Company Detail screen shows comprehensive information about a single GP firm. It displays company profile, subscription tier, billing status, and usage metrics. Lists of users and funds associated with the company are shown with quick access to details. Admins can edit company information, manage subscriptions, and impersonate users for support purposes (with audit logging)."""),

        ("admin-users.html", "Users", "All platform users",
         """The Users screen provides a global view of all registered users across all companies. Admins can search by name, email, or company. User cards show name, company, role, last login, and account status. Actions include resetting passwords, deactivating accounts, and viewing activity logs. This helps with user support and security monitoring."""),

        ("admin-people.html", "People", "LP contacts database",
         """The People screen manages the global database of LP contacts (individuals who work at institutional investors). Unlike LPs (organizations), People tracks individuals with their employment history. Admins can search contacts, view profiles, and track career movements between organizations. This data enriches LP profiles with specific relationship targets for outreach."""),

        ("admin-lps.html", "LPs", "Institutional investor database",
         """The LPs screen is the master database of institutional investors. Admins can browse, search, filter, and edit LP records. Each LP entry shows name, type, AUM, location, and data quality score. Bulk actions allow updating multiple records. The Import Wizard button provides access to CSV import for adding new LPs. Data quality indicators highlight records needing attention."""),

        ("admin-lp-detail.html", "Edit LP", "LP data management form",
         """The Edit LP screen allows admins to maintain LP data quality. All fields are editable: name, type, location, AUM, allocation targets, investment mandate, and geographic preferences. The investment mandate text field is particularly important as it's used for semantic matching. Data source and quality score help track provenance. Changes are logged for audit purposes."""),

        ("admin-data-quality.html", "Data Quality", "Quality monitoring and issues",
         """The Data Quality screen helps admins maintain high-quality LP data. It shows data completeness metrics, identifies records with missing fields, flags potential duplicates, and highlights stale data. Quality scores are calculated based on field completeness, recency, and source reliability. Admins can drill down into specific issues and take corrective actions."""),

        ("admin-import.html", "Import Wizard", "CSV import tool",
         """The Import Wizard guides admins through bulk LP data import. It's a multi-step process: upload CSV, map columns to fields, preview changes, and execute import. The system validates data, detects duplicates, and shows potential issues before committing. Import jobs can be paused, resumed, or rolled back. Progress is tracked with detailed logging for troubleshooting."""),

        ("admin-health.html", "System Health", "Services and integrations status",
         """The System Health screen monitors platform infrastructure and external services. It shows status for the database, API server, authentication service, OpenRouter (LLM), Voyage AI (embeddings), and email delivery. Response times and error rates are tracked. Alerts notify admins of issues. This is the first place to check when users report problems."""),
    ],
    "states": [
        ("dashboard-empty.html", "Empty Dashboard", "First-time user experience",
         """The Empty Dashboard appears when a user has no funds yet. Instead of empty space, it provides a welcoming onboarding experience. A prominent call-to-action encourages users to create their first fund. Brief feature descriptions explain what they'll be able to do: find matching LPs, generate pitches, and track outreach. This reduces friction for new users and increases activation rates."""),

        ("loading-matches.html", "Loading Matches", "Match generation progress",
         """The Loading Matches screen appears during AI match generation, which can take 30+ seconds for large LP databases. It shows a progress bar, current step (applying filters, computing similarity scores), and estimated time remaining. A cancel button allows users to abort if needed. This transparent feedback prevents users from thinking the system is frozen and reduces support requests."""),

        ("error-api.html", "API Error", "Error state handling",
         """The API Error screen provides graceful error handling when something goes wrong. Instead of cryptic error messages, it shows a friendly explanation and clear next steps. A "Try Again" button attempts to retry the operation. Error details are available for technical users and support. Contact information helps users get assistance if the problem persists."""),
    ],
    "lp_user": [
        ("lp-dashboard.html", "LP Dashboard", "Fund overview for institutional investors",
         """The LP Dashboard is the command center for institutional investors using LPxGP. It provides an at-a-glance view of matching funds, allocation availability, and recent activity. LPs see statistics including new fund matches, funds reviewed, and current allocation capacity. The top matches table shows funds ranked by compatibility score with quick actions to mark interest or pass. This bidirectional matching enables LPs to proactively discover funds rather than waiting for GP outreach."""),

        ("lp-fund-matches.html", "Fund Matches", "Ranked funds matching LP mandate",
         """The Fund Matches screen shows all funds ranked by compatibility with the LP's investment mandate. LPs can filter by strategy, fund size, and geography. Each fund card displays the GP firm, strategy tags, target size, fund number, closing timeline, and match score. Quick actions allow LPs to mark interest, pass, or view detailed analysis. The scoring algorithm considers strategy alignment, size fit, track record, geographic overlap, and ESG requirements."""),

        ("lp-fund-match-detail.html", "Fund Match Detail", "Detailed fund analysis for LPs",
         """The Fund Match Detail screen explains why a specific fund is recommended for the LP. It provides a narrative explanation of alignment factors, a detailed score breakdown across multiple dimensions (strategy, size, track record, geography, ESG), the fund's investment thesis, historical performance data, and key considerations or concerns. LPs can mark interest, request a meeting, or request the fund deck. Private notes allow LPs to track their evaluation."""),

        ("lp-preferences.html", "LP Preferences", "Matching preferences and alerts",
         """The LP Preferences screen allows institutional investors to configure their matching criteria. LPs can set strategy preferences, geographic focus, fund size range, check size range, track record requirements, and ESG requirements. Current allocation availability helps the system prioritize actively deploying LPs. Notification preferences control alerts for new high-score matches, fund updates, closing reminders, and weekly digests."""),

        ("lp-profile.html", "LP Profile", "Organization profile management",
         """The LP Profile screen displays the LP's organization information and investment mandate. Organization details (name, type, AUM, headquarters) are managed by LPxGP administrators to ensure data quality. The investment mandate section shows the LP's strategies, geographic focus, check size, and track record requirements. User profile settings allow LPs to manage their personal information and security settings including password and two-factor authentication."""),
    ],
}


async def take_screenshots():
    """Take screenshots of all HTML mockups using Playwright."""
    from playwright.async_api import async_playwright

    SCREENSHOTS_DIR.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        # Use 1280x720 viewport for cleaner screenshots that fit on PDF pages
        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        for category, screens in SCREENS.items():
            for item in screens:
                filename = item[0]
                title = item[1]
                html_path = MOCKUPS_DIR / filename
                if not html_path.exists():
                    print(f"  Skipping {filename} (not found)")
                    continue

                await page.goto(f"file://{html_path}")
                await page.wait_for_timeout(500)  # Wait for Tailwind to load

                screenshot_path = SCREENSHOTS_DIR / filename.replace(".html", ".png")
                # Capture viewport only (not full page) for consistent sizing
                await page.screenshot(path=str(screenshot_path), full_page=False)
                print(f"  Screenshot: {screenshot_path.name}")

        await browser.close()


def generate_pdf():
    """Generate PDF document with WeasyPrint."""
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration

    font_config = FontConfiguration()

    # Count total screens
    total_screens = sum(len(screens) for screens in SCREENS.values())

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
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            color: white;
            margin: -2cm -2.5cm;
            padding: 3cm;
            position: relative;
        }}

        .cover::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(ellipse at 30% 20%, rgba(212, 168, 75, 0.15) 0%, transparent 50%),
                        radial-gradient(ellipse at 70% 80%, rgba(212, 168, 75, 0.1) 0%, transparent 40%);
            pointer-events: none;
        }}

        .cover-logo {{
            width: 180px;
            height: auto;
            margin-bottom: 1.5em;
            position: relative;
            z-index: 1;
        }}

        .cover h1 {{
            font-size: 54pt;
            font-weight: 700;
            margin-bottom: 0.3em;
            letter-spacing: -0.02em;
            position: relative;
            z-index: 1;
        }}

        .cover .subtitle {{
            font-size: 20pt;
            font-weight: 500;
            color: #d4a84b;
            margin-bottom: 0.8em;
            position: relative;
            z-index: 1;
        }}

        .cover .tagline {{
            font-size: 14pt;
            font-weight: 400;
            opacity: 0.8;
            margin-bottom: 1.5em;
            max-width: 450px;
            line-height: 1.5;
            position: relative;
            z-index: 1;
        }}

        .cover .slogan {{
            font-size: 24pt;
            font-weight: 600;
            color: #fbbf24;
            margin-bottom: 1.5em;
            letter-spacing: -0.01em;
            position: relative;
            z-index: 1;
        }}

        .cover .stats-row {{
            display: flex;
            justify-content: center;
            gap: 3em;
            margin-bottom: 2em;
            position: relative;
            z-index: 1;
        }}

        .cover .stat {{
            text-align: center;
        }}

        .cover .stat-number {{
            font-size: 28pt;
            font-weight: 700;
            color: #d4a84b;
            display: block;
        }}

        .cover .stat-label {{
            font-size: 10pt;
            opacity: 0.7;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .cover .date {{
            font-size: 11pt;
            opacity: 0.5;
            position: relative;
            z-index: 1;
        }}

        .cover .badge {{
            display: inline-block;
            background: rgba(212, 168, 75, 0.2);
            border: 1px solid rgba(212, 168, 75, 0.4);
            color: #fbbf24;
            padding: 0.5em 1em;
            border-radius: 2em;
            font-size: 10pt;
            font-weight: 500;
            margin-bottom: 1.5em;
            position: relative;
            z-index: 1;
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
            font-size: 16pt;
            font-weight: 600;
            color: #243b53;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            page-break-after: avoid;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 0.3em;
        }}

        h3 {{
            font-size: 13pt;
            font-weight: 600;
            color: #334e68;
            margin-top: 1.2em;
            margin-bottom: 0.4em;
            page-break-after: avoid;
        }}

        h4 {{
            font-size: 11pt;
            font-weight: 600;
            color: #486581;
            margin-top: 1em;
            margin-bottom: 0.3em;
        }}

        p {{
            margin-bottom: 0.8em;
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

        .toc-section {{
            font-weight: 600;
            color: #102a43;
            margin-top: 1.2em;
            font-size: 12pt;
        }}

        .toc-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.3em 0;
            padding-left: 1em;
            font-size: 10pt;
            color: #475569;
        }}

        /* Section styling */
        .section {{
            page-break-before: always;
        }}

        .section:first-of-type {{
            page-break-before: avoid;
        }}

        /* Screen mockup with explanation - each screen on its own page */
        .screen {{
            page-break-before: always;
            page-break-inside: avoid;
        }}

        .screen-header {{
            background: linear-gradient(135deg, #102a43 0%, #1e3a5f 100%);
            color: white;
            padding: 0.8em 1em;
            border-radius: 8px 8px 0 0;
            margin-bottom: 0;
        }}

        .screen-title {{
            font-size: 14pt;
            font-weight: 600;
            margin: 0;
        }}

        .screen-subtitle {{
            font-size: 9pt;
            opacity: 0.8;
            margin-top: 0.2em;
        }}

        .screen-image {{
            /* Clean screenshot display - no borders */
        }}

        .screen-image img {{
            width: 100%;
            display: block;
        }}

        .screen-explanation {{
            background: #f8fafc;
            border-radius: 8px;
            padding: 0.8em 1em;
            margin-top: 0.5em;
            font-size: 9pt;
            line-height: 1.4;
            color: #475569;
        }}

        /* Info boxes */
        .info-box {{
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-left: 4px solid #0ea5e9;
            border-radius: 0 8px 8px 0;
            padding: 1em;
            margin: 1em 0;
        }}

        .highlight-box {{
            background: #fef3c7;
            border: 1px solid #fcd34d;
            border-left: 4px solid #f59e0b;
            border-radius: 0 8px 8px 0;
            padding: 1em;
            margin: 1em 0;
        }}

        .success-box {{
            background: #d1fae5;
            border: 1px solid #6ee7b7;
            border-left: 4px solid #10b981;
            border-radius: 0 8px 8px 0;
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

        tr:nth-child(even) {{
            background: #f8fafc;
        }}

        /* Category headers - each category starts on new page */
        .category-header {{
            background: linear-gradient(135deg, #102a43 0%, #243b53 100%);
            color: white;
            padding: 1.2em 1.5em;
            border-radius: 8px;
            margin: 0 0 1.5em 0;
            page-break-before: always;
            page-break-after: avoid;
        }}

        .category-header h2 {{
            color: white;
            border: none;
            margin: 0;
            padding: 0;
            font-size: 18pt;
        }}

        .category-count {{
            font-size: 11pt;
            opacity: 0.8;
            margin-top: 0.3em;
        }}

        /* Feature grid */
        .feature-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1em;
            margin: 1em 0;
        }}

        .feature-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1em;
        }}

        .feature-card h4 {{
            margin-top: 0;
            color: #102a43;
        }}

        .feature-card p {{
            font-size: 10pt;
            margin-bottom: 0;
            color: #64748b;
        }}

        /* Code/pre styling */
        pre {{
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            font-size: 9pt;
            background: #1e293b;
            color: #e2e8f0;
            padding: 1em;
            border-radius: 8px;
            overflow-x: auto;
            white-space: pre-wrap;
        }}

        code {{
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            font-size: 10pt;
            background: #f1f5f9;
            padding: 0.1em 0.3em;
            border-radius: 3px;
        }}

        /* Glossary */
        .glossary-term {{
            font-weight: 600;
            color: #102a43;
        }}

        .glossary-def {{
            margin-left: 1em;
            margin-bottom: 0.8em;
            color: #475569;
        }}
    </style>
</head>
<body>
    <!-- Cover Page -->
    <div class="cover">
        <img src="file://{MOCKUPS_DIR / 'logo-dark.png'}" alt="LPxGP" class="cover-logo">
        <div class="slogan">Smarter LP Outreach. Better Fundraising.</div>
        <div class="subtitle">The Intelligence Platform for Private Capital</div>
        <div class="tagline">Powered by 36 AI agents working 24/7—researching, debating, and verifying every LP match before it reaches you.</div>
        <div class="stats-row">
            <div class="stat">
                <span class="stat-number">36</span>
                <span class="stat-label">AI Agents</span>
            </div>
            <div class="stat">
                <span class="stat-number">11</span>
                <span class="stat-label">Debate Types</span>
            </div>
            <div class="stat">
                <span class="stat-number">$4T+</span>
                <span class="stat-label">Market Size</span>
            </div>
        </div>
        <div class="badge">Product Requirements Document</div>
        <div class="date">{datetime.now().strftime("%B %Y")}</div>
    </div>

    <!-- Table of Contents -->
    <div class="toc">
        <h1>Table of Contents</h1>

        <div class="toc-section">1. Product Overview</div>
        <div class="toc-item"><span>What LPxGP Does</span></div>
        <div class="toc-item"><span>The Problem We Solve</span></div>
        <div class="toc-item"><span>Key Capabilities</span></div>
        <div class="toc-item"><span>Who Uses LPxGP</span></div>

        <div class="toc-section">2. Feature Specifications</div>
        <div class="toc-item"><span>LP Database & Search</span></div>
        <div class="toc-item"><span>AI-Powered Matching</span></div>
        <div class="toc-item"><span>Pitch Generation</span></div>
        <div class="toc-item"><span>Pipeline Management</span></div>

        <div class="toc-section">3. User Journeys</div>
        <div class="toc-item"><span>Platform Onboarding</span></div>
        <div class="toc-item"><span>Fund Creation</span></div>
        <div class="toc-item"><span>LP Research & Matching</span></div>
        <div class="toc-item"><span>Pitch & Outreach</span></div>

        <div class="toc-section">4. Screen Reference ({total_screens} screens)</div>
        <div class="toc-item"><span>Public Screens (4)</span></div>
        <div class="toc-item"><span>GP User Screens (13)</span></div>
        <div class="toc-item"><span>Super Admin Screens (10)</span></div>
        <div class="toc-item"><span>UI State Screens (3)</span></div>

        <div class="toc-section">5. Data Model</div>
        <div class="toc-item"><span>Entity Overview</span></div>
        <div class="toc-item"><span>Key Relationships</span></div>

        <div class="toc-section">6. Technical Architecture</div>
        <div class="toc-item"><span>System Overview</span></div>
        <div class="toc-item"><span>Technology Stack</span></div>
        <div class="toc-item"><span>Security Model</span></div>

        <div class="toc-section">7. Agentic AI Architecture</div>
        <div class="toc-item"><span>Multi-Agent Debate System</span></div>
        <div class="toc-item"><span>The 36 Specialized AI Agents</span></div>
        <div class="toc-item"><span>LangGraph Orchestration</span></div>
        <div class="toc-item"><span>Continuous Learning</span></div>

        <div class="toc-section">8. Non-Functional Requirements</div>
        <div class="toc-item"><span>Performance</span></div>
        <div class="toc-item"><span>Security</span></div>
        <div class="toc-item"><span>Scalability</span></div>

        <div class="toc-section">9. Success Metrics</div>

        <div class="toc-section">10. Glossary</div>
    </div>

    <!-- Section 1: Product Overview -->
    <div class="section">
        <h1>1. Product Overview</h1>

        <h2>The Opportunity</h2>
        <p>Private equity and venture capital fundraising is a $4+ trillion industry running on spreadsheets, outdated databases, and gut instinct. Fund managers spend 40% of their time on fundraising—most of it on manual research, blind outreach, and wasted meetings with misaligned investors.</p>

        <div class="highlight-box">
            <strong>The Technical Insight:</strong> Traditional matching systems use a single AI model that outputs a score. They're overconfident, can't explain themselves, and hallucinate data. LPxGP uses a fundamentally different architecture: <strong>36 specialized agents that debate each other</strong>, catch each other's mistakes, and only commit when they reach consensus—or escalate to humans when they don't.
        </div>

        <h2>What LPxGP Does</h2>
        <p>LPxGP is an AI-native intelligence platform that helps fund managers find and engage institutional investors. But unlike "AI-powered" tools that slap ChatGPT onto a database, we built a multi-agent architecture from first principles.</p>

        <div class="success-box">
            <strong>In one sentence:</strong> LPxGP's adversarial AI agents debate every match, catch hallucinations before they embarrass users, and produce verified, explainable recommendations—turning fundraising from art into science.
        </div>

        <h3>Platform Capabilities</h3>

        <table>
            <tr>
                <th>Capability</th>
                <th>The AI Approach</th>
                <th>Why It Matters</th>
            </tr>
            <tr>
                <td><strong>LP Database</strong></td>
                <td>5,000+ institutional investors with mandates, AUM, allocation targets, and contacts—enriched by Research Agent debates that validate every data point</td>
                <td>Hours of research in seconds, with verified data</td>
            </tr>
            <tr>
                <td><strong>Semantic Search</strong></td>
                <td>Voyage AI embeddings tuned for finance + LLM re-ranking. Search "growth equity that likes founder-led companies in fintech" and get relevant results</td>
                <td>Find LPs by concept, not just keywords</td>
            </tr>
            <tr>
                <td><strong>Multi-Agent Matching</strong></td>
                <td>Bull Agent argues for, Bear Agent argues against, Synthesizer weighs evidence. Disagreements get cross-feedback loops or human escalation</td>
                <td>Catches overconfidence and edge cases that single models miss</td>
            </tr>
            <tr>
                <td><strong>Explainable Scores</strong></td>
                <td>Full debate transcripts available. See exactly why Bull thinks it's an 85 and Bear thinks it's a 62—and how they resolved it</td>
                <td>Users trust recommendations they can understand</td>
            </tr>
            <tr>
                <td><strong>Verified Pitch Generation</strong></td>
                <td>Pitch Generator creates content, Pitch Critic catches hallucinations and factual errors, Content Synthesizer approves or regenerates</td>
                <td>Personalization at scale without embarrassing mistakes</td>
            </tr>
            <tr>
                <td><strong>Pipeline Tracking</strong></td>
                <td>Every interaction feeds the learning loop. 12-18 month lag to commitment, but we track early signals (response rate, meeting conversion)</td>
                <td>System gets smarter with every match</td>
            </tr>
        </table>

        <h2>The Problem We Solve</h2>
        <p>Fundraising is broken. Here's why:</p>

        <div class="feature-grid">
            <div class="feature-card">
                <h4>Information Overload</h4>
                <p>10,000+ institutional investors globally. Mandates change quarterly. Allocation cycles vary. Manually evaluating fit is impossible at scale.</p>
            </div>
            <div class="feature-card">
                <h4>Wasted Meetings</h4>
                <p>80% of LP meetings go nowhere—wrong strategy, wrong size, wrong timing. Each wasted meeting costs the GP $2,000+ in time and travel.</p>
            </div>
            <div class="feature-card">
                <h4>Generic Outreach</h4>
                <p>"Dear Investor, we're raising a fund..." gets deleted. Personalization requires hours of research per LP. Most GPs can't scale it.</p>
            </div>
            <div class="feature-card">
                <h4>AI Hallucination Risk</h4>
                <p>Standard AI tools make up facts about LPs, invent allocations, and fabricate contacts. One wrong claim destroys credibility permanently.</p>
            </div>
        </div>

        <h2>Who Uses LPxGP</h2>

        <h3>GP Fund Manager (Company Admin)</h3>
        <p><strong>Role:</strong> Managing Partner or Partner at a PE/VC firm responsible for fundraising</p>
        <p><strong>Platform Access:</strong> Full access including fund creation, team management, and all LP features</p>
        <p><strong>Primary Goals:</strong></p>
        <ul>
            <li>Raise capital for new funds efficiently</li>
            <li>Build relationships with the right institutional investors</li>
            <li>Track fundraising pipeline across the entire team</li>
        </ul>

        <h3>GP Associate (Company Member)</h3>
        <p><strong>Role:</strong> Associate or VP supporting fundraising efforts at a PE/VC firm</p>
        <p><strong>Platform Access:</strong> LP search, matching, and pitch generation (read-only for fund settings)</p>
        <p><strong>Primary Goals:</strong></p>
        <ul>
            <li>Research and identify potential LP targets</li>
            <li>Prepare meeting materials and personalized pitches</li>
            <li>Support partners with data and analysis</li>
        </ul>

        <h3>Super Admin (LPxGP Team)</h3>
        <p><strong>Role:</strong> LPxGP platform administrator responsible for operations</p>
        <p><strong>Platform Access:</strong> Full administrative access across all companies</p>
        <p><strong>Primary Goals:</strong></p>
        <ul>
            <li>Onboard new GP firms to the platform</li>
            <li>Maintain and improve LP database quality</li>
            <li>Monitor platform health and support users</li>
        </ul>
    </div>

    <!-- Section 2: Feature Specifications -->
    <div class="section">
        <h1>2. Feature Specifications</h1>

        <h2>LP Database & Search</h2>

        <h3>Database Contents</h3>
        <p>The LP database contains comprehensive information on institutional investors:</p>
        <ul>
            <li><strong>Organization Profile:</strong> Name, type (pension, endowment, family office, etc.), headquarters location, website</li>
            <li><strong>Financial Data:</strong> Total AUM, PE/VC allocation percentage, typical check size range, target returns</li>
            <li><strong>Investment Mandate:</strong> Strategy preferences, geographic focus, sector interests, stage preferences</li>
            <li><strong>Contact Information:</strong> Key personnel with names, titles, and professional profiles</li>
            <li><strong>Activity Data:</strong> Recent fund commitments (when available from public sources)</li>
        </ul>

        <h3>Search Capabilities</h3>
        <table>
            <tr>
                <th>Search Type</th>
                <th>Description</th>
                <th>Example</th>
            </tr>
            <tr>
                <td>Keyword Search</td>
                <td>Traditional text matching on LP names and fields</td>
                <td>"CalPERS" or "technology"</td>
            </tr>
            <tr>
                <td>Semantic Search</td>
                <td>Natural language queries using AI embeddings</td>
                <td>"growth equity investors focused on enterprise software"</td>
            </tr>
            <tr>
                <td>Filtered Search</td>
                <td>Combine filters for precise targeting</td>
                <td>Type: Pension, AUM: >$10B, Geography: North America</td>
            </tr>
        </table>

        <h2>AI-Powered Matching</h2>

        <div class="success-box">
            <strong>Design Principle:</strong> Quality above all else. Cost is not a constraint. Success is measured by actual investment commitments, not just high match scores.
        </div>

        <h3>Quality-First Hybrid Pipeline</h3>
        <p>The matching system uses a 6-stage pipeline that combines hard filters, multiple scoring methods, LLM analysis, and continuous learning:</p>

        <div class="info-box">
            <pre style="font-family: monospace; font-size: 8pt; background: transparent; color: inherit; padding: 0;">
Stage 1: HARD FILTERS (SQL)
  └── Eliminate impossible matches (strategy, geography, size, track record)
  └── Output: ~300-500 candidates from 10,000 LPs

Stage 2: MULTI-SIGNAL SCORING (Python + Embeddings)
  └── Attribute matching, semantic similarity, historical patterns
  └── Output: Ranked list with preliminary scores

Stage 3: LLM DEEP ANALYSIS (Claude via OpenRouter)
  └── Analyze EVERY filtered candidate with LLM for nuanced judgment
  └── Output: LLM-validated scores + detailed reasoning

Stage 4: ENSEMBLE RANKING
  └── Combine all scores, surface disagreements as "worth investigating"
  └── Output: Final ranked matches with multi-perspective validation

Stage 5: EXPLANATION GENERATION
  └── Rich explanations, talking points, concerns, approach strategy
  └── Output: Actionable intelligence for GP outreach

Stage 6: LEARNING LOOP (Continuous)
  └── Track outcomes, retrain models, A/B test changes
            </pre>
        </div>

        <h3>Ensemble Scoring Weights</h3>
        <table>
            <tr>
                <th>Component</th>
                <th>Weight</th>
                <th>Source</th>
                <th>Purpose</th>
            </tr>
            <tr>
                <td>Rule-Based Score</td>
                <td>25%</td>
                <td>SQL + Python</td>
                <td>Hard constraints, business logic</td>
            </tr>
            <tr>
                <td>Semantic Score</td>
                <td>25%</td>
                <td>Voyage AI embeddings</td>
                <td>Thesis/mandate alignment</td>
            </tr>
            <tr>
                <td><strong>LLM Score</strong></td>
                <td><strong>35%</strong></td>
                <td>Claude analysis</td>
                <td>Nuanced judgment, non-obvious fit</td>
            </tr>
            <tr>
                <td>Collaborative Score</td>
                <td>15%</td>
                <td>Historical patterns</td>
                <td>"LPs like this invested in funds like this"</td>
            </tr>
        </table>

        <h3>LLM Scoring (Key Innovation)</h3>
        <p>Unlike systems that only use LLMs for explanations, we use Claude to actually score every match. The LLM analyzes fund profiles and LP mandates to identify:</p>
        <ul>
            <li><strong>Strategy Alignment:</strong> How well does fund strategy match LP mandate?</li>
            <li><strong>Size Fit:</strong> Is fund size in LP's sweet spot or at the edge?</li>
            <li><strong>Track Record:</strong> Does team experience meet LP's requirements?</li>
            <li><strong>Timing:</strong> Is LP likely allocating now based on known patterns?</li>
            <li><strong>Non-Obvious Insights:</strong> Red flags, hidden opportunities, and nuanced factors</li>
        </ul>

        <h3>Bidirectional Matching</h3>
        <p>The system supports matching in both directions:</p>
        <ul>
            <li><strong>GP → LP:</strong> GP creates fund, system finds matching LPs ranked by fit quality</li>
            <li><strong>LP → GP:</strong> LPs can see which funds match their mandate (optional feature)</li>
        </ul>

        <h3>Learning From Slow Feedback</h3>
        <div class="highlight-box">
            <strong>Critical Reality:</strong> Investment sector feedback takes 12-18 months (first meeting → commitment). The system uses proxy metrics for early learning.
        </div>

        <table>
            <tr>
                <th>Tier</th>
                <th>Signal</th>
                <th>Latency</th>
                <th>Use For</th>
            </tr>
            <tr>
                <td>1</td>
                <td>Match shortlisted/dismissed</td>
                <td>Immediate</td>
                <td>Hard filter tuning</td>
            </tr>
            <tr>
                <td>2</td>
                <td>Response received</td>
                <td>Days-Weeks</td>
                <td><strong>Key early predictor</strong></td>
            </tr>
            <tr>
                <td>2</td>
                <td>Meeting scheduled</td>
                <td>Weeks</td>
                <td><strong>Strong quality signal</strong></td>
            </tr>
            <tr>
                <td>3</td>
                <td>Due diligence started</td>
                <td>2-6 months</td>
                <td>Deal progression</td>
            </tr>
            <tr>
                <td>4</td>
                <td>Commitment made</td>
                <td>6-18 months</td>
                <td><strong>Ground truth</strong></td>
            </tr>
        </table>

        <h3>Match Output</h3>
        <p>For each fund, the system generates:</p>
        <ul>
            <li><strong>Ranked LP List:</strong> LPs ordered by fit score (0-100)</li>
            <li><strong>Score Breakdown:</strong> How each component contributed to the score</li>
            <li><strong>Talking Points:</strong> What to emphasize when approaching this LP</li>
            <li><strong>Risk Factors:</strong> Potential concerns to address proactively</li>
        </ul>

        <h2>Pitch Generation</h2>

        <h3>Output Types</h3>
        <table>
            <tr>
                <th>Type</th>
                <th>Length</th>
                <th>Use Case</th>
            </tr>
            <tr>
                <td>Executive Summary</td>
                <td>1 page</td>
                <td>One-pager tailored to LP's interests and mandate</td>
            </tr>
            <tr>
                <td>Outreach Email</td>
                <td>3-5 paragraphs</td>
                <td>Initial introduction referencing LP's recent activity</td>
            </tr>
            <tr>
                <td>Talking Points</td>
                <td>Bullet list</td>
                <td>Meeting preparation with key messages and responses</td>
            </tr>
        </table>

        <div class="highlight-box">
            <strong>Human-in-the-Loop Design:</strong> All AI-generated content requires human review before use. There is no auto-send functionality - users must copy to clipboard and paste into their email client. This ensures quality control and compliance with professional communication standards.
        </div>

        <h2>Pipeline Management</h2>
        <p>The platform tracks LPs through the fundraising pipeline:</p>
        <ul>
            <li><strong>Identified:</strong> LP discovered through search or matching</li>
            <li><strong>Shortlisted:</strong> Selected for potential outreach</li>
            <li><strong>Contacted:</strong> Initial outreach sent</li>
            <li><strong>Meeting Scheduled:</strong> Engagement confirmed</li>
            <li><strong>In Diligence:</strong> Active evaluation underway</li>
            <li><strong>Committed:</strong> Commitment received</li>
        </ul>
    </div>

    <!-- Section 3: User Journeys -->
    <div class="section">
        <h1>3. User Journeys</h1>
        <p>This section describes the key user experience flows through the LPxGP platform.</p>

        <h2>Journey 1: Platform Onboarding</h2>
        <p><strong>Actor:</strong> Sarah, LPxGP Super Admin</p>
        <p><strong>Goal:</strong> Onboard a new GP firm to the platform</p>
        <div class="info-box">
            <strong>Screen Flow:</strong> Admin Dashboard → Companies → Create Company → Company Detail → Invite Admin
        </div>
        <p>Sarah receives a request from Acme Capital to join LPxGP. She reviews platform health on the Admin Dashboard, navigates to Companies, creates the new company profile with billing information, and invites John (Managing Partner) as the company admin via email invitation. John receives a secure link to accept the invitation and set up his account.</p>

        <h2>Journey 2: Fund Creation</h2>
        <p><strong>Actor:</strong> John, Partner at Acme Capital</p>
        <p><strong>Goal:</strong> Create fund profile for Growth Fund III</p>
        <div class="info-box">
            <strong>Screen Flow:</strong> Dashboard → Create Fund → Upload Deck → AI Extraction → Fund Detail
        </div>
        <p>John clicks "+ New Fund" on his dashboard. He can either manually enter fund details or upload a pitch deck PDF. Choosing to upload, the AI extracts fund information (name, strategy, target size, thesis, track record) with confidence scores for each field. John reviews and confirms high-confidence items, manually corrects a low-confidence field, and saves the fund profile. The fund is now ready for LP matching.</p>

        <h2>Journey 3: LP Research & Matching</h2>
        <p><strong>Actor:</strong> Maria, Associate at Acme Capital</p>
        <p><strong>Goal:</strong> Find and evaluate LPs for Growth Fund III</p>
        <div class="info-box">
            <strong>Screen Flow:</strong> Dashboard → LP Search → Apply Filters → LP Detail → Matches → Match Detail → Add to Shortlist
        </div>
        <p>Maria uses two approaches: manual research and AI matching. For manual research, she navigates to LP Search, enters "growth equity technology investors" and applies filters (Check Size > $10M, Geography: North America). She reviews 45 results, clicks on promising LPs to view full profiles with mandates and contacts.</p>
        <p>For AI matching, she goes to Growth Fund III and clicks "View Matches." The system shows 87 LPs ranked by fit score. She clicks on CalPERS (score: 92) to see why it's a strong match: strategy alignment, appropriate size, and high semantic similarity to the fund thesis. The AI provides talking points about CalPERS's recent tech investments and flags a potential concern about their preference for established managers.</p>

        <h2>Journey 4: Pitch & Outreach</h2>
        <p><strong>Actor:</strong> Maria, Associate at Acme Capital</p>
        <p><strong>Goal:</strong> Create personalized outreach for high-priority LPs</p>
        <div class="info-box">
            <strong>Screen Flow:</strong> Match Detail → Pitch Generator → Generate → Edit → Copy → Outreach Hub
        </div>
        <p>From the CalPERS match detail, Maria clicks "Generate Pitch" and selects "Outreach Email." The AI generates a personalized email referencing CalPERS's recent allocations and how Growth Fund III aligns with their mandate. Maria edits the subject line to add a mutual connection reference, adjusts the call-to-action timing, and copies the final email to clipboard. She pastes it into her email client and sends. Back in LPxGP, she moves CalPERS to "Contacted" in the Outreach Hub and logs the activity.</p>
    </div>

    <!-- Section 4: Screen Reference -->
    <div class="section">
        <h1>4. Screen Reference</h1>
        <p>This section documents all {total_screens} screens in the LPxGP platform. Each screen includes a visual mockup and explanation of its purpose, user actions, and role in user journeys.</p>
"""

    # Add screen mockups by category with full explanations
    category_info = {
        "public": ("Public Screens", "Authentication and onboarding flows for all users", 4),
        "gp_user": ("GP User Screens", "Core platform functionality for fund managers and associates", 13),
        "admin": ("Super Admin Screens", "Platform administration and data management", 10),
        "lp_user": ("LP User Screens", "Bidirectional matching - funds ranked for institutional investors", 5),
        "states": ("UI State Screens", "Loading, empty, and error states for better user experience", 3),
    }

    for category, screens in SCREENS.items():
        cat_name, cat_desc, cat_count = category_info[category]
        html_content += f"""
        <div class="category-header">
            <h2>{cat_name}</h2>
            <div class="category-count">{cat_count} screens — {cat_desc}</div>
        </div>
"""
        for item in screens:
            filename, title, short_desc, explanation = item
            screenshot_path = SCREENSHOTS_DIR / filename.replace(".html", ".png")
            if screenshot_path.exists():
                html_content += f"""
        <div class="screen">
            <div class="screen-header">
                <div class="screen-title">{title}</div>
                <div class="screen-subtitle">{short_desc}</div>
            </div>
            <div class="screen-image">
                <img src="file://{screenshot_path}" alt="{title}">
            </div>
            <div class="screen-explanation">
                {explanation}
            </div>
        </div>
"""

    # Add remaining sections
    html_content += """
    </div>

    <!-- Section 5: Data Model -->
    <div class="section">
        <h1>5. Data Model</h1>

        <h2>Entity Overview</h2>
        <p>LPxGP uses a unified relational data model where GPs and LPs are both organizations, and platform users are people with login access:</p>

        <div class="info-box">
            <pre style="font-family: monospace; font-size: 9pt; background: transparent; color: inherit; padding: 0;">
┌─────────────────────────────────────────────────────────┐
│                    ORGANIZATIONS                         │
│              (unified: type='gp' | 'lp')                │
├─────────────────────────────────────────────────────────┤
│  GP organizations ──owns──▶ Funds                       │
│  LP organizations ◀──matched_with── Funds               │
└─────────────────────────────────────────────────────────┘
                           │
                           │ employs
                           ▼
┌─────────────────────────────────────────────────────────┐
│                        PEOPLE                            │
│            (all industry professionals)                  │
├─────────────────────────────────────────────────────────┤
│  primary_org_id ──▶ organizations (current employer)   │
│  auth_user_id ──▶ auth.users (if can login)            │
│  Employment history tracks job changes                  │
└─────────────────────────────────────────────────────────┘
            </pre>
        </div>

        <h2>Key Entities</h2>

        <table>
            <tr>
                <th>Entity</th>
                <th>Description</th>
                <th>Key Fields</th>
            </tr>
            <tr>
                <td><strong>Organizations</strong></td>
                <td>Unified table for both GP firms and LP investors</td>
                <td>type (gp/lp), name, aum, lp_type, mandate_embedding</td>
            </tr>
            <tr>
                <td><strong>People</strong></td>
                <td>All industry professionals (can work at any org)</td>
                <td>name, email, primary_org_id, auth_user_id, role</td>
            </tr>
            <tr>
                <td><strong>Employment</strong></td>
                <td>Career history linking people to organizations</td>
                <td>person_id, org_id, title, start_date, end_date</td>
            </tr>
            <tr>
                <td><strong>Funds</strong></td>
                <td>Investment funds owned by GP organizations</td>
                <td>org_id, name, strategy, target_size, thesis_embedding</td>
            </tr>
            <tr>
                <td><strong>Matches</strong></td>
                <td>Fund-LP compatibility scores</td>
                <td>fund_id, lp_org_id, total_score, score_breakdown</td>
            </tr>
            <tr>
                <td><strong>Pitches</strong></td>
                <td>AI-generated outreach content</td>
                <td>match_id, type, content, created_by</td>
            </tr>
            <tr>
                <td><strong>Outreach Events</strong></td>
                <td>Track journey from match to commitment</td>
                <td>match_id, event_type, event_date, meeting_type</td>
            </tr>
            <tr>
                <td><strong>Match Outcomes</strong></td>
                <td>Final outcomes for model training</td>
                <td>match_id, outcome, commitment_amount, features_at_match_time</td>
            </tr>
            <tr>
                <td><strong>Relationships</strong></td>
                <td>GP-LP relationship intelligence</td>
                <td>gp_org_id, lp_org_id, relationship_type, prior_commitments</td>
            </tr>
            <tr>
                <td><strong>LP Capacity</strong></td>
                <td>Timing intelligence for allocation windows</td>
                <td>lp_org_id, fiscal_year, remaining_capacity, next_allocation_window</td>
            </tr>
        </table>

        <h2>Key Design Decisions</h2>
        <ul>
            <li><strong>Unified Organizations:</strong> GPs and LPs are both organizations with a type discriminator. No separate tables.</li>
            <li><strong>People Work at Organizations:</strong> Clean FK to organizations.id - no polymorphic relationships.</li>
            <li><strong>People Can Move:</strong> Employment history tracks job changes. Someone can move from LP to GP.</li>
            <li><strong>Platform Users = People + Auth:</strong> People with auth_user_id set can log in. No separate users table.</li>
            <li><strong>Full Referential Integrity:</strong> All foreign keys are real database constraints.</li>
        </ul>

        <h2>Vector Embeddings</h2>
        <p>Semantic matching uses 1024-dimensional vector embeddings stored in PostgreSQL with pgvector:</p>
        <ul>
            <li><strong>Fund Thesis Embedding:</strong> Vector representation of fund strategy and thesis text</li>
            <li><strong>LP Mandate Embedding:</strong> Vector representation of LP investment mandate (on organizations table)</li>
            <li><strong>Similarity Calculation:</strong> Cosine similarity between embeddings determines semantic fit</li>
        </ul>
    </div>

    <!-- Section 6: Technical Architecture -->
    <div class="section">
        <h1>6. Technical Architecture</h1>

        <h2>System Overview</h2>
        <p>LPxGP is built as a modern web application with server-rendered UI and AI integrations:</p>

        <div class="info-box">
            <pre style="font-family: monospace; font-size: 9pt; background: transparent; color: inherit; padding: 0;">
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Browser       │────▶│   Railway       │────▶│   Supabase      │
│   (HTMX)        │◀────│   (FastAPI)     │◀────│   (PostgreSQL)  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │OpenRouter│ │ Voyage   │ │ Supabase │
             │ (Claude) │ │ AI       │ │ Auth     │
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
                <td>API server, business logic, async operations</td>
            </tr>
            <tr>
                <td>Frontend</td>
                <td>Jinja2 + HTMX + Tailwind</td>
                <td>Server-rendered UI with dynamic updates, no build step</td>
            </tr>
            <tr>
                <td>Database</td>
                <td>Supabase (PostgreSQL + pgvector)</td>
                <td>Data storage, vector similarity search, row-level security</td>
            </tr>
            <tr>
                <td>Authentication</td>
                <td>Supabase Auth</td>
                <td>Invite-only signup, session management, password reset</td>
            </tr>
            <tr>
                <td>LLM</td>
                <td>OpenRouter (Claude)</td>
                <td>Pitch generation, fund extraction, match explanations</td>
            </tr>
            <tr>
                <td>Embeddings</td>
                <td>Voyage AI</td>
                <td>Finance-optimized vectors for semantic matching</td>
            </tr>
            <tr>
                <td>Hosting</td>
                <td>Railway</td>
                <td>Auto-deploy from GitHub, managed infrastructure</td>
            </tr>
        </table>

        <h2>Security Model</h2>
        <ul>
            <li><strong>Invite-Only Access:</strong> Users can only join via company admin invitation - no self-signup</li>
            <li><strong>Row-Level Security:</strong> Database policies ensure users only see their company's data</li>
            <li><strong>Role-Based Access:</strong> Company Admins vs Members vs Super Admins with different permissions</li>
            <li><strong>Human-in-the-Loop:</strong> All AI-generated content requires human review before external use</li>
            <li><strong>Secure Sessions:</strong> JWT tokens with refresh, automatic expiration, and secure cookie handling</li>
        </ul>
    </div>

    <!-- Section 7: Agentic AI Architecture -->
    <div class="section">
        <h1>7. Agentic AI Architecture</h1>

        <div class="highlight-box">
            <strong>Competitive Moat:</strong> LPxGP's multi-agent debate system represents a fundamentally different approach to AI-powered matching. Rather than using a single model that can hallucinate or miss nuances, we deploy 36 specialized agents that argue, critique, and synthesize—producing higher-quality results with built-in verification and explainability.
        </div>

        <h2>Multi-Agent Debate System</h2>
        <p>Traditional AI matching systems use a single model to score compatibility. This approach is prone to overconfidence, hallucination, and missing edge cases. LPxGP takes a radically different approach: <strong>adversarial multi-agent debates</strong>.</p>

        <h3>The Bull/Bear Pattern</h3>
        <p>For every fund-LP match, we run an internal debate:</p>
        <ul>
            <li><strong>Bull Agent:</strong> Argues FOR the match—finds alignment, hidden opportunities, optimal timing</li>
            <li><strong>Bear Agent:</strong> Argues AGAINST—finds risks, constraint violations, relationship barriers</li>
            <li><strong>Synthesizer:</strong> Weighs both perspectives, resolves disagreements, produces final score</li>
        </ul>

        <div class="info-box">
            <strong>Why This Matters:</strong> When Bull and Bear agents disagree significantly (>30 points), the system flags for human review rather than making a confident wrong decision. This catches edge cases that single-model systems miss.
        </div>

        <h3>Four Debate Types</h3>
        <table>
            <tr>
                <th>Debate</th>
                <th>Purpose</th>
                <th>Agents</th>
                <th>Output</th>
            </tr>
            <tr>
                <td><strong>Constraint Interpretation</strong></td>
                <td>Parse LP investment mandates</td>
                <td>Broad Interpreter, Narrow Interpreter, Synthesizer</td>
                <td>Actionable filter criteria</td>
            </tr>
            <tr>
                <td><strong>Research Enrichment</strong></td>
                <td>Validate external data quality</td>
                <td>Research Generator, Research Critic, Quality Synthesizer</td>
                <td>Verified profile updates</td>
            </tr>
            <tr>
                <td><strong>Match Scoring</strong></td>
                <td>Evaluate fund-LP fit</td>
                <td>Bull Agent, Bear Agent, Match Synthesizer</td>
                <td>Confidence-weighted scores</td>
            </tr>
            <tr>
                <td><strong>Pitch Generation</strong></td>
                <td>Create personalized content</td>
                <td>Pitch Generator, Pitch Critic, Content Synthesizer</td>
                <td>Verified, factual pitches</td>
            </tr>
        </table>

        <h2>The 36 Specialized Agents</h2>
        <p>Each agent has a specific role, versioned prompts, and distinct personality. This specialization produces better results than a generalist model.</p>

        <h3>Constraint Interpretation Agents</h3>
        <table>
            <tr>
                <th>Agent</th>
                <th>Role</th>
                <th>Key Behaviors</th>
            </tr>
            <tr>
                <td><strong>Broad Interpreter</strong></td>
                <td>Find flexibility in LP mandates</td>
                <td>Identifies what's implied but not stated, finds edge cases that could qualify, surfaces hidden opportunities based on historical commitments</td>
            </tr>
            <tr>
                <td><strong>Narrow Interpreter</strong></td>
                <td>Identify constraints and exclusions</td>
                <td>Flags hard exclusions, policy constraints, regulatory barriers. Conservative: better to flag than to miss</td>
            </tr>
            <tr>
                <td><strong>Constraint Synthesizer</strong></td>
                <td>Resolve disagreements, create filters</td>
                <td>Classifies constraints as HARD (absolute) or SOFT (preference), escalates unresolved ambiguities for human review</td>
            </tr>
        </table>

        <h3>Match Scoring Agents</h3>
        <table>
            <tr>
                <th>Agent</th>
                <th>Role</th>
                <th>Key Behaviors</th>
            </tr>
            <tr>
                <td><strong>Bull Agent</strong></td>
                <td>Argue FOR the match</td>
                <td>Finds strategy alignment, timing opportunities, warm intro paths, hidden strengths. Generates talking points for GP outreach</td>
            </tr>
            <tr>
                <td><strong>Bear Agent</strong></td>
                <td>Argue AGAINST the match</td>
                <td>Checks hard constraint violations, identifies relationship barriers, flags track record gaps. Sets hard_exclusion=true for deal-breakers</td>
            </tr>
            <tr>
                <td><strong>Match Synthesizer</strong></td>
                <td>Combine perspectives fairly</td>
                <td>Weights Bull/Bear based on evidence quality, resolves disagreements, escalates when confidence is low</td>
            </tr>
        </table>

        <h3>Pitch Generation Agents</h3>
        <table>
            <tr>
                <th>Agent</th>
                <th>Role</th>
                <th>Key Behaviors</th>
            </tr>
            <tr>
                <td><strong>Pitch Generator</strong></td>
                <td>Create personalized content</td>
                <td>Every sentence LP-specific, references recent activity, addresses known concerns proactively. No generic phrases</td>
            </tr>
            <tr>
                <td><strong>Pitch Critic</strong></td>
                <td>Validate accuracy and tone</td>
                <td>Catches factual errors, hallucinations, generic content, tone mismatches. Quality score 0-100</td>
            </tr>
            <tr>
                <td><strong>Content Synthesizer</strong></td>
                <td>Make publish/regenerate/reject decision</td>
                <td>Approves if score ≥85, regenerates if 50-84, rejects if &lt;50 or unfixable errors. Max 3 iterations</td>
            </tr>
        </table>

        <h2>Sample Agent Prompts</h2>
        <p>Each agent operates from a carefully-crafted prompt that defines its personality, inputs, and structured output format. Here are excerpts from key agents:</p>

        <h3>Bull Agent (v1.1.0) — Excerpt</h3>
        <pre style="font-size: 8pt; line-height: 1.4;">
You are the BULL AGENT analyzing a potential match between a fund and LP.

YOUR MISSION: Argue FOR this match. Find the best reasons why it could succeed.
Be optimistic but grounded in data.

ANALYSIS DIMENSIONS:
- strategy_alignment: How fund strategy maps to LP mandate
- timing_opportunity: Why now is the right time to approach
- relationship_potential: Warm intro paths and barriers
- hidden_strengths: Non-obvious connections and opportunities

OUTPUT REQUIREMENTS:
- Score 0-100 with confidence 0.0-1.0
- Specific talking_points for GP outreach (5 actionable points)
- acknowledged_concerns with mitigations
- Data-backed reasoning citing specific profile fields

CRITICAL: Don't inflate scores. Truth matters more than winning the debate.
        </pre>

        <h3>Bear Agent (v1.1.0) — Excerpt</h3>
        <pre style="font-size: 8pt; line-height: 1.4;">
You are the BEAR AGENT analyzing a potential match between a fund and LP.

YOUR MISSION: Critically examine this match. Find reasons why it might fail.
Be skeptical but fair—not cynical.

ANALYSIS DIMENSIONS:
- hard_constraints_violated: Deal-breakers with evidence
- soft_concerns: Issues that reduce probability of success
- timing_issues: Allocation cycle misalignment
- relationship_barriers: Access difficulties

OUTPUT REQUIREMENTS:
- Score 0-100 with confidence 0.0-1.0
- hard_exclusion flag if this is a definite no
- conditions_for_success: What would need to be true
- acknowledged_positives: Fair credit for genuine alignment

CRITICAL: If you find a hard constraint violation, set hard_exclusion=true.
        </pre>

        <h3>Match Synthesizer (v1.0.0) — Excerpt</h3>
        <pre style="font-size: 8pt; line-height: 1.4;">
You are the MATCH SYNTHESIZER combining Bull and Bear perspectives.

YOUR MISSION: Weigh both perspectives fairly. Resolve disagreements where
possible, escalate where not.

RESOLUTION RULES:
- When agents agree: High confidence, weight equally
- When agents disagree &lt;20 points: Resolve based on evidence quality
- When agents disagree >30 points: Flag for human review
- When Bear sets hard_exclusion=true: Take seriously, escalate if unsure

OUTPUT REQUIREMENTS:
- final_score 0-100 with component breakdown
- resolved_disagreements with reasoning
- unresolved_disagreements escalated to human
- talking_points that incorporate Bear's valid concerns
- approach_strategy for GP outreach

ESCALATION TRIGGERS:
- Disagreement >30 points
- Confidence &lt;0.5
- Hard exclusion with Bull score >70
        </pre>

        <h2>LangGraph Orchestration</h2>
        <p>The debate system is implemented as a LangGraph state machine—a directed graph where nodes are agent executions and edges are conditional transitions.</p>

        <div class="info-box">
            <pre style="font-family: monospace; font-size: 8pt; background: transparent; color: inherit; padding: 0;">
┌──────────────────────────────────────────────────────────────────┐
│                  LANGGRAPH STATE MACHINE                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌─────────┐     ┌─────────┐     ┌────────────┐                 │
│   │  START  │────▶│  DEBATE │────▶│ SYNTHESIZE │                 │
│   └─────────┘     └────┬────┘     └─────┬──────┘                 │
│                        │                 │                        │
│         ┌──────────────┼─────────────────┼──────────────┐        │
│         │              │                 │              │        │
│         ▼              ▼                 ▼              ▼        │
│   ┌──────────┐  ┌───────────┐     ┌──────────┐   ┌─────────┐    │
│   │ COMPLETE │  │ REGENERATE│     │ ESCALATE │   │   END   │    │
│   └──────────┘  └─────┬─────┘     └──────────┘   └─────────┘    │
│                       │                                          │
│                       └──────────▶ back to DEBATE (max 3x)       │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

TRANSITION LOGIC:
• Disagreement ≤20 points → COMPLETE (consensus reached)
• Disagreement >20 but ≤30 → REGENERATE with cross-feedback
• Disagreement >30 points → ESCALATE to human review
• Max 3 iterations → ESCALATE if still disagreeing
            </pre>
        </div>

        <h3>Cross-Feedback Mechanism</h3>
        <p>When agents disagree, the regeneration step provides each agent with the other's critique:</p>
        <ul>
            <li><strong>Bull receives:</strong> Bear's concerns, constraint violations, and risk factors</li>
            <li><strong>Bear receives:</strong> Bull's talking points, alignment arguments, and hidden strengths</li>
        </ul>
        <p>This forces agents to directly address counterarguments rather than talking past each other—often resolving disagreements within 2-3 iterations.</p>

        <h2>Observability with Langfuse</h2>
        <p>Every agent execution is fully traced using Langfuse (open-source, self-hostable for data privacy):</p>

        <div class="feature-grid">
            <div class="feature-card">
                <h4>Full Trace Inspection</h4>
                <p>View every debate as a tree of agent calls with inputs, outputs, token counts, and latency.</p>
            </div>
            <div class="feature-card">
                <h4>Prompt Versioning</h4>
                <p>Semantic versioning (X.Y.Z) for all prompts. A/B test new versions before full rollout.</p>
            </div>
            <div class="feature-card">
                <h4>Quality Metrics</h4>
                <p>Track escalation rates, disagreement patterns, and accuracy over time.</p>
            </div>
            <div class="feature-card">
                <h4>Cost Tracking</h4>
                <p>Per-debate token usage and API costs for margin optimization.</p>
            </div>
        </div>

        <h2>Continuous Learning Loop</h2>
        <p>The agentic system improves over time through outcome tracking:</p>

        <table>
            <tr>
                <th>Signal</th>
                <th>Latency</th>
                <th>How It's Used</th>
            </tr>
            <tr>
                <td>Match shortlisted/dismissed</td>
                <td>Immediate</td>
                <td>Tune hard filters, adjust agent weights</td>
            </tr>
            <tr>
                <td>Response received</td>
                <td>Days-Weeks</td>
                <td>Key early predictor—train on high/low response patterns</td>
            </tr>
            <tr>
                <td>Meeting scheduled</td>
                <td>Weeks</td>
                <td>Strong quality signal—validate match explanations</td>
            </tr>
            <tr>
                <td>Commitment made</td>
                <td>6-18 months</td>
                <td>Ground truth—full model retraining</td>
            </tr>
        </table>

        <div class="success-box">
            <strong>Defensible Moat:</strong> As more matches flow through the system, the agent prompts are refined, disagreement patterns are analyzed, and the learning loop compounds. Competitors starting from scratch face a cold-start problem—they lack the interaction data that makes our agents increasingly accurate.
        </div>

        <h2>Why Multi-Agent vs. Single Model?</h2>

        <table>
            <tr>
                <th>Dimension</th>
                <th>Single Model</th>
                <th>Multi-Agent Debate</th>
            </tr>
            <tr>
                <td><strong>Overconfidence</strong></td>
                <td>Common—no internal check</td>
                <td>Bear agent challenges optimism</td>
            </tr>
            <tr>
                <td><strong>Hallucination</strong></td>
                <td>Can go undetected</td>
                <td>Critic agents flag unsupported claims</td>
            </tr>
            <tr>
                <td><strong>Edge Cases</strong></td>
                <td>Often missed</td>
                <td>Broad/Narrow interpreters catch nuances</td>
            </tr>
            <tr>
                <td><strong>Explainability</strong></td>
                <td>Black box score</td>
                <td>Full debate transcript available</td>
            </tr>
            <tr>
                <td><strong>Human Review</strong></td>
                <td>All or nothing</td>
                <td>Targeted escalation when confidence is low</td>
            </tr>
            <tr>
                <td><strong>Improvement</strong></td>
                <td>Retrain entire model</td>
                <td>Tune individual agent prompts</td>
            </tr>
        </table>

    </div>

    <!-- Section 8: Non-Functional Requirements -->
    <div class="section">
        <h1>8. Non-Functional Requirements</h1>

        <h2>Performance</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Target</th>
                <th>Measurement</th>
            </tr>
            <tr>
                <td>Page Load (LCP)</td>
                <td>&lt; 2 seconds</td>
                <td>Largest Contentful Paint for all pages</td>
            </tr>
            <tr>
                <td>Search Response</td>
                <td>&lt; 500ms</td>
                <td>Time from query to results display</td>
            </tr>
            <tr>
                <td>Semantic Search</td>
                <td>&lt; 2 seconds</td>
                <td>Including embedding generation and vector search</td>
            </tr>
            <tr>
                <td>Match Generation</td>
                <td>&lt; 30 seconds</td>
                <td>For 100 matches against full LP database</td>
            </tr>
            <tr>
                <td>Pitch Generation</td>
                <td>&lt; 10 seconds</td>
                <td>LLM response for single pitch</td>
            </tr>
        </table>

        <h2>Security</h2>
        <ul>
            <li><strong>Authentication:</strong> Secure password hashing, rate-limited login, account lockout after 5 failures</li>
            <li><strong>Authorization:</strong> Row-level security policies, role-based access control</li>
            <li><strong>Data Protection:</strong> Encryption at rest and in transit, no PII in logs</li>
            <li><strong>Input Validation:</strong> Server-side validation, SQL injection prevention, XSS protection</li>
            <li><strong>Audit Logging:</strong> Track who accessed what and when for compliance</li>
        </ul>

        <h2>Scalability</h2>
        <ul>
            <li><strong>Database:</strong> Designed to handle 100,000+ LPs with efficient indexing</li>
            <li><strong>Concurrent Users:</strong> Stateless backend supports horizontal scaling</li>
            <li><strong>API Rate Limiting:</strong> Protect external services from overuse</li>
            <li><strong>Background Jobs:</strong> Long-running tasks processed asynchronously</li>
        </ul>

        <h2>Availability</h2>
        <ul>
            <li><strong>Uptime Target:</strong> 99.9% availability (excludes planned maintenance)</li>
            <li><strong>Disaster Recovery:</strong> Daily database backups with point-in-time recovery</li>
            <li><strong>Graceful Degradation:</strong> Core features work even if AI services are temporarily unavailable</li>
        </ul>
    </div>

    <!-- Section 9: Success Metrics -->
    <div class="section">
        <h1>9. Success Metrics</h1>

        <h2>User Engagement</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Target</th>
                <th>Why It Matters</th>
            </tr>
            <tr>
                <td>Daily Active Users / Monthly Active Users</td>
                <td>&gt; 30%</td>
                <td>Indicates habitual usage, not just occasional visits</td>
            </tr>
            <tr>
                <td>Average Session Length</td>
                <td>&gt; 5 minutes</td>
                <td>Users are doing meaningful work, not just checking in</td>
            </tr>
            <tr>
                <td>Matches Reviewed per Session</td>
                <td>&gt; 10</td>
                <td>Users are actively evaluating AI recommendations</td>
            </tr>
        </table>

        <h2>Feature Adoption</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Target</th>
                <th>Why It Matters</th>
            </tr>
            <tr>
                <td>Fund Created within 7 Days of Signup</td>
                <td>&gt; 60%</td>
                <td>Users are activating and seeing value quickly</td>
            </tr>
            <tr>
                <td>Matches Shortlisted per Fund</td>
                <td>&gt; 20</td>
                <td>AI matching is producing actionable recommendations</td>
            </tr>
            <tr>
                <td>Pitches Generated per User (monthly)</td>
                <td>&gt; 5</td>
                <td>Pitch generation is useful enough to use repeatedly</td>
            </tr>
        </table>

        <h2>Quality Indicators</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Target</th>
                <th>Why It Matters</th>
            </tr>
            <tr>
                <td>Match Feedback: "Useful"</td>
                <td>&gt; 70%</td>
                <td>AI recommendations are relevant and actionable</td>
            </tr>
            <tr>
                <td>Pitch Copied to Clipboard</td>
                <td>&gt; 50%</td>
                <td>Generated content is good enough to use</td>
            </tr>
            <tr>
                <td>LP Contacted from Platform</td>
                <td>&gt; 20%</td>
                <td>Platform enables actual outreach, not just research</td>
            </tr>
        </table>
    </div>

    <!-- Section 10: Glossary -->
    <div class="section">
        <h1>10. Glossary</h1>

        <p class="glossary-term">AUM (Assets Under Management)</p>
        <p class="glossary-def">The total market value of assets that an investment firm manages on behalf of clients. For LPs, this indicates their overall investment capacity.</p>

        <p class="glossary-term">Dry Powder</p>
        <p class="glossary-def">Capital that has been committed to a fund but not yet invested. Indicates available capital for new investments.</p>

        <p class="glossary-term">Embedding</p>
        <p class="glossary-def">A vector (array of numbers) that represents text in a way that captures semantic meaning. Used for similarity matching between fund thesis and LP mandate.</p>

        <p class="glossary-term">Endowment</p>
        <p class="glossary-def">A type of LP, typically a fund established by a university, hospital, or non-profit organization for long-term investment.</p>

        <p class="glossary-term">Family Office</p>
        <p class="glossary-def">A private wealth management firm that handles investments for a wealthy family. Often more flexible than institutional LPs.</p>

        <p class="glossary-term">GP (General Partner)</p>
        <p class="glossary-def">The fund manager who makes investment decisions and manages fund operations. GPs are LPxGP's primary users.</p>

        <p class="glossary-term">Hard Filter</p>
        <p class="glossary-def">A matching criterion that must be satisfied for an LP to be considered. If failed, the LP is excluded regardless of other scores.</p>

        <p class="glossary-term">HTMX</p>
        <p class="glossary-def">A JavaScript library that allows HTML elements to make AJAX requests directly, enabling dynamic updates without full page reloads.</p>

        <p class="glossary-term">LP (Limited Partner)</p>
        <p class="glossary-def">An institutional investor who provides capital to investment funds. LPs include pension funds, endowments, family offices, and sovereign wealth funds.</p>

        <p class="glossary-term">Mandate</p>
        <p class="glossary-def">An LP's investment guidelines, including acceptable strategies, geographic regions, check sizes, and return expectations.</p>

        <p class="glossary-term">Pension Fund</p>
        <p class="glossary-def">A type of LP that manages retirement assets for employees of governments, corporations, or unions. Often large and long-term focused.</p>

        <p class="glossary-term">pgvector</p>
        <p class="glossary-def">A PostgreSQL extension for storing and querying vector embeddings, enabling semantic similarity search in the database.</p>

        <p class="glossary-term">RLS (Row-Level Security)</p>
        <p class="glossary-def">Database security feature that restricts which rows users can access based on their identity. Ensures data isolation between companies.</p>

        <p class="glossary-term">Semantic Search</p>
        <p class="glossary-def">Search that understands meaning rather than just matching keywords. Uses embeddings to find conceptually similar content.</p>

        <p class="glossary-term">Soft Score</p>
        <p class="glossary-def">A matching criterion that contributes to the overall fit score but doesn't exclude the LP if not perfectly matched.</p>

        <p class="glossary-term">Sovereign Wealth Fund</p>
        <p class="glossary-def">A state-owned investment fund that invests global reserves. Among the largest LPs with diverse mandates.</p>

        <p class="glossary-term">Thesis</p>
        <p class="glossary-def">A fund's investment philosophy and strategy, describing what types of companies they invest in and why.</p>

        <p class="glossary-term">Voyage AI</p>
        <p class="glossary-def">An AI company providing embedding models optimized for specific domains like finance and legal.</p>
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
