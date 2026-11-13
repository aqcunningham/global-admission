"""
Match each school in schools.csv to its IPEDS UNITID using the College Scorecard API.

Input:  schools.csv  (columns: name, state[, aid_group])
Output: unitid_matched.csv     -> best match per school + status (AUTO / CHECK / NOT_FOUND)
        unitid_candidates.csv  -> every candidate the API returned, for manual review

Run from the project root:  python scripts/match_unitids.py
"""

import csv
import os
import re
import time

import requests

API_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
API_KEY = os.environ.get("SCORECARD_API_KEY", "DEMO_KEY")

FIELDS = ",".join([
    "id",                                  # the IPEDS UNITID
    "school.name",
    "school.city",
    "school.state",
    "school.school_url",
    "school.degrees_awarded.predominant",  # 3 = bachelor's
    "school.operating",                    # 1 = currently operating
])

INPUT_FILE = "schools.csv"
MATCHED_FILE = "unitid_matched.csv"
CANDIDATES_FILE = "unitid_candidates.csv"


def normalize(name):
    """Lowercase, drop punctuation and filler words so names compare fairly."""
    name = name.lower().replace("&", "and")
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    stop = {"the", "of", "at", "in", "college", "university"}
    return " ".join(w for w in name.split() if w not in stop)


def search(name, state):
    params = {"api_key": API_KEY, "school.name": name, "fields": FIELDS, "per_page": 20}
    if state:
        params["school.state"] = state
    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("results", [])


def pick_best(query, results):
    """Return (best_result, status). AUTO = confident, CHECK = needs a human look."""
    if not results:
        return None, "NOT_FOUND"

    operating = [r for r in results if r.get("school.operating") in (1, None)]
    results = operating or results

    q = normalize(query)
    exact = [r for r in results if normalize(r["school.name"]) == q]
    if len(exact) == 1:
        return exact[0], "AUTO"
    if len(results) == 1:
        return results[0], "AUTO"

    bachelors = [r for r in results if r.get("school.degrees_awarded.predominant") == 3]
    return (exact or bachelors or results)[0], "CHECK"


def main():
    if API_KEY == "DEMO_KEY":
        print("Warning: SCORECARD_API_KEY not found, using the rate-limited DEMO_KEY.")

    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        schools = list(csv.DictReader(f))

    matched_rows, candidate_rows = [], []

    for row in schools:
        name = row["name"].strip()
        state = (row.get("state") or "").strip() or None
        try:
            results = search(name, state)
        except requests.RequestException as e:
            print(f"ERROR     {name}: {e}")
            results = []

        best, status = pick_best(name, results)
        print(f"{status:9} {name}  ->  {best['school.name'] if best else '-'}")

        matched_rows.append({
            "input_name": name,
            "status": status,
            "unitid": best["id"] if best else "",
            "official_name": best["school.name"] if best else "",
            "city": best.get("school.city", "") if best else "",
            "state": best.get("school.state", "") if best else (state or ""),
            "url": best.get("school.school_url", "") if best else "",
            "aid_group": (row.get("aid_group") or "").strip(),
        })
        for r in results:
            candidate_rows.append({
                "input_name": name,
                "unitid": r["id"],
                "official_name": r["school.name"],
                "city": r.get("school.city", ""),
                "state": r.get("school.state", ""),
                "predominant_degree": r.get("school.degrees_awarded.predominant", ""),
                "url": r.get("school.school_url", ""),
            })

        time.sleep(0.3)

    with open(MATCHED_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(matched_rows[0].keys()))
        writer.writeheader()
        writer.writerows(matched_rows)

    if candidate_rows:
        with open(CANDIDATES_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(candidate_rows[0].keys()))
            writer.writeheader()
            writer.writerows(candidate_rows)

    counts = {s: sum(r["status"] == s for r in matched_rows) for s in ("AUTO", "CHECK", "NOT_FOUND")}
    print(f"\nDone. AUTO: {counts['AUTO']}  CHECK: {counts['CHECK']}  NOT_FOUND: {counts['NOT_FOUND']}")


if __name__ == "__main__":
    main()