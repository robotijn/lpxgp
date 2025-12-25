"""Browser tests for LP and Company CRUD pages.

These pages are accessible by admin, FA, and GP roles.
LP users should be redirected to dashboard.
"""

import pytest


@pytest.mark.browser
def test_lp_list_loads_for_gp_user(gp_page, browser_base_url):
    """LP list page should load for GP users."""
    gp_page.goto(f"{browser_base_url}/admin/lps")
    gp_page.wait_for_selector("h1:has-text('LP Database')")

    # Should show stats cards
    assert gp_page.locator("text=Total LPs").count() > 0

    # Should show table
    assert gp_page.locator("table").count() > 0


@pytest.mark.browser
def test_lp_list_shows_mock_data(gp_page, browser_base_url):
    """LP list should show mock LP data."""
    gp_page.goto(f"{browser_base_url}/admin/lps")
    gp_page.wait_for_selector("h1:has-text('LP Database')")

    # Should show CalPERS in the table
    assert gp_page.locator("text=CalPERS").count() > 0


@pytest.mark.browser
def test_lp_detail_loads(gp_page, browser_base_url):
    """LP detail page should load for mock LP."""
    gp_page.goto(f"{browser_base_url}/admin/lps/lp-001")
    gp_page.wait_for_selector("h1:has-text('Edit LP: CalPERS')")

    # Should show form sections
    assert gp_page.locator("text=Basic Information").count() > 0
    assert gp_page.locator("text=Financial Information").count() > 0
    assert gp_page.locator("text=Investment Mandate").count() > 0


@pytest.mark.browser
def test_lp_new_page_loads(gp_page, browser_base_url):
    """New LP page should load."""
    gp_page.goto(f"{browser_base_url}/admin/lps/new")
    gp_page.wait_for_selector("h1:has-text('Add New LP')")

    # Should show empty form
    assert gp_page.locator("input[name='name']").count() > 0
    assert gp_page.locator("select[name='lp_type']").count() > 0


@pytest.mark.browser
def test_companies_list_loads_for_gp_user(gp_page, browser_base_url):
    """Companies list page should load for GP users."""
    gp_page.goto(f"{browser_base_url}/admin/companies")
    gp_page.wait_for_selector("h1:has-text('Companies')")

    # Should show table
    assert gp_page.locator("table").count() > 0


@pytest.mark.browser
def test_companies_list_shows_data(gp_page, browser_base_url):
    """Companies list should show company data (real or mock)."""
    gp_page.goto(f"{browser_base_url}/admin/companies")
    gp_page.wait_for_selector("h1:has-text('Companies')")

    # Should show at least one company row in the table (either mock or database data)
    # Check for table rows with company data
    table_rows = gp_page.locator("table tbody tr")
    assert table_rows.count() > 0


@pytest.mark.browser
def test_company_detail_loads(gp_page, browser_base_url):
    """Company detail page should load for mock company."""
    gp_page.goto(f"{browser_base_url}/admin/companies/org-001")
    gp_page.wait_for_selector("h1:has-text('Acme Capital')")

    # Should show stats
    assert gp_page.locator("text=Users").count() > 0
    assert gp_page.locator("text=Funds").count() > 0

    # Should show users section
    assert gp_page.locator("text=John Partner").count() > 0


@pytest.mark.browser
def test_lp_list_redirects_lp_user_to_dashboard(lp_page, browser_base_url):
    """LP users should be redirected to dashboard when accessing LP list."""
    lp_page.goto(f"{browser_base_url}/admin/lps")

    # Should redirect to dashboard
    lp_page.wait_for_url(f"{browser_base_url}/dashboard")


@pytest.mark.browser
def test_companies_redirects_lp_user_to_dashboard(lp_page, browser_base_url):
    """LP users should be redirected to dashboard when accessing companies."""
    lp_page.goto(f"{browser_base_url}/admin/companies")

    # Should redirect to dashboard
    lp_page.wait_for_url(f"{browser_base_url}/dashboard")


@pytest.mark.browser
def test_lp_list_loads_for_admin_user(admin_page, browser_base_url):
    """LP list page should load for admin users."""
    admin_page.goto(f"{browser_base_url}/admin/lps")
    admin_page.wait_for_selector("h1:has-text('LP Database')")

    # Should show stats cards
    assert admin_page.locator("text=Total LPs").count() > 0
