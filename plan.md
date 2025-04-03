# Refined Plan: npm-like Web Page for LitePolis Repositories with Jekyll

**Tech Stack:**

*   **Static Site Generator:** Jekyll (Ruby-based)
*   **Data Fetching & Processing:** Python (for scripts to interact with GitHub and PyPI APIs)
*   **Frontend:** HTML, CSS, JavaScript (Jekyll templates, potentially minimal JavaScript for interactivity)
*   **Styling:** Plain CSS or a lightweight framework like Tailwind CSS (optional, for easier styling)
*   **Automation:** GitHub Actions (for daily data fetching and site generation)
*   **Hosting:** GitHub Pages

**Workflow Breakdown (Jekyll Specific):**

```mermaid
graph LR
    A[Start: Daily GitHub Actions Schedule] --> B{Fetch GitHub Repositories (GitHub API) - Python Script};
    B --> C{Filter 'LitePolis-' Repositories - Python Script};
    C --> D{For Each Repo: - Python Script};
    D --> E{Check PyPI (PyPI API) - Python Script};
    E -- Package Found --> F{Get PyPI Install Command - Python Script};
    E -- Package Not Found --> G{Installation Command: N/A - Python Script};
    F --> H{Fetch README (GitHub API) - Python Script};
    G --> H;
    H --> I{Fetch License (GitHub API) - Python Script};
    I --> J{Generate Data Files (YAML/JSON) - Python Script};
    J --> K{Jekyll Build Static Site (Jekyll)};
    K --> L{Commit & Push to GitHub Pages branch (gh-pages)};
    L --> M[End: GitHub Pages Updated];
```

**Detailed Steps:**

1.  **Set up Jekyll Project:**
    *   Create a new Jekyll project in your repository. Jekyll has a standard directory structure.
    *   We'll need a `_config.yml` file for Jekyll configuration.
    *   Layouts will be in `_layouts/` (e.g., `default.html`).
    *   Pages will be in the root directory (e.g., `index.html`).
    *   Data files (repository data) will be in `_data/` (e.g., `repositories.yml` or `repositories.json`).
    *   Assets (CSS, JavaScript) can be in `assets/`.

2.  **Python Data Fetching Script (`fetch_data.py`):**
    *   This script will be placed in a `scripts/` directory.
    *   It will use the `requests` library in Python to:
        *   Query the GitHub API to find repositories starting with `LitePolis-`.
        *   For each repository:
            *   Check PyPI for a package with the same name (or a derived name).
            *   Fetch the README content.
            *   Fetch the license information.
            *   Collect relevant data (name, URL, description, install command, README, license).
    *   The script will output the collected data into a YAML or JSON file in the `_data/` directory of the Jekyll project (e.g., `_data/repositories.yml`).

3.  **Jekyll Templates:**
    *   **`_layouts/default.html`:** Basic HTML structure for the website.
    *   **`index.html`:** Homepage template. This will:
        *   Loop through the data in `_data/repositories.yml`.
        *   For each repository, display:
            *   Repository Name (linked to GitHub URL)
            *   Installation command (if available)
            *   README preview (truncated, with a link to full README or GitHub repo)
            *   License (linked to license file on GitHub if available)

4.  **GitHub Actions Workflow (`.github/workflows/update-repos.yml`):**
    ```yaml
    name: Update LitePolis Repositories Website

    on:
      schedule:
        - cron: '0 0 * * *' # Run daily at midnight
      workflow_dispatch: # Allow manual triggering

    jobs:
      update_website:
        runs-on: ubuntu-latest
        steps:
          - name: Checkout Repository
            uses: actions/checkout@v3

          - name: Set up Python
            uses: actions/setup-python@v4
            with:
              python-version: '3.x'

          - name: Install Python dependencies
            run: pip install requests pyyaml

          - name: Run Data Fetching Script
            run: python scripts/fetch_data.py

          - name: Set up Ruby and Jekyll
            uses: actions/setup-ruby@v1
            with:
              ruby-version: '3.2' # or your preferred Ruby version

          - name: Build Jekyll Site
            run: bundle install # Install Jekyll dependencies (if Gemfile exists)
            working-directory: . # Assuming Jekyll project is in the root
            shell: bash
          - name: Build Jekyll Site
            run: bundle exec jekyll build -d _site
            working-directory: . # Assuming Jekyll project is in the root
            shell: bash

          - name: Deploy to GitHub Pages
            uses: peaceiris/actions-gh-pages@v3
            with:
              github_token: ${{ secrets.GITHUB_TOKEN }}
              publish_dir: ./_site # Jekyll output directory
    ```

5.  **GitHub Pages Configuration:**
    *   In your repository settings, enable GitHub Pages and set the source to be the `gh-pages` branch (or `main` branch if you prefer to deploy from there and configure Jekyll accordingly).