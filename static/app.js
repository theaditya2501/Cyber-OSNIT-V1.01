function startInvestigation() {

    let username = document.getElementById("username").value;
    let email = document.getElementById("email").value;
    let phone = document.getElementById("phone").value;

    fetch("/run_osint", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, phone })
    })
    .then(res => res.json())
    .then(data => {

        document.getElementById("results").style.display = "block";

        /* ===== SUMMARY BAR ===== */
        let platformFound = Object.values(data.username_results).filter(p => p.found).length;

        document.getElementById("riskBox").innerText =
            data.risk.score + " (" + data.risk.level + ")";

        document.getElementById("confidenceBox").innerText =
            data.identity_confidence.confidence_score + "% (" + data.identity_confidence.level + ")";

        document.getElementById("platformCount").innerText = platformFound;

        document.getElementById("exposureBox").innerText =
            data.email_results.valid || data.phone_results.valid ? "MEDIUM" : "LOW";

        /* ===== OVERVIEW ===== */
        document.getElementById("overview").innerHTML = `
            <h5>Digital Footprint Overview</h5>
            <ul>
                <li>Total platforms found: ${platformFound}</li>
                <li>Email exposure: ${data.email_results.valid ? "Yes" : "No"}</li>
                <li>Phone validity: ${data.phone_results.valid}</li>
            </ul>
        `;

        /* ===== PLATFORMS (FULL INTELLIGENCE) ===== */
        let pHTML = "<h5>Platform Breakdown</h5><ul>";
        for (let p in data.username_results) {
            const d = data.username_results[p];
            if (d.found) {
                pHTML += `
                <li>
                    <b>${p}</b><br>
                    URL: <a href="${d.url}" target="_blank">${d.url}</a><br>
                    Category: ${d.category}<br>
                    Exposure: ${d.exposure || "Public"}<br>
                    Intelligence: ${d.breach_indicator || "None"}
                </li><hr>`;
            } else {
                pHTML += `<li>${p}: Not Found</li>`;
            }
        }
        pHTML += "</ul>";
        document.getElementById("platforms").innerHTML = pHTML;

        /* ===== CONTACT ===== */
        document.getElementById("contact").innerHTML = `
            <h5>Email Intelligence</h5>
            <ul>
                <li>Provider: ${data.email_results.provider || "N/A"}</li>
                <li>Variants: ${(data.email_results.email_variations || []).join(", ")}</li>
                <li>Public exposure: ${data.profiles.GitHub?.email ? "Yes (GitHub)" : "No"}</li>
            </ul>

            <h5>Phone Intelligence</h5>
            <ul>
                <li>Country: ${data.phone_results.country || "N/A"}</li>
                <li>Carrier: ${data.phone_results.carrier || "N/A"}</li>
                <li>Valid: ${data.phone_results.valid}</li>
            </ul>
        `;

        /* ===== IDENTITY ===== */
        document.getElementById("identity").innerHTML = `
            <h5>Identity Consistency</h5>
            <ul>
                <li>Username reuse detected across multiple platforms</li>
                <li>Email consistency: ${(data.email_results.email_variations || []).length > 1 ? "Medium" : "Low"}</li>
                <li>Overall confidence: ${data.identity_confidence.confidence_score}%</li>
            </ul>
        `;

        /* ===== ANALYST NOTES ===== */
        document.getElementById("analyst").innerHTML = `
            <h5>Analyst Summary</h5>
            <p>
                Public identifiers show consistent correlation across ${platformFound} platforms.
                Identity confidence is assessed as <b>${data.identity_confidence.level}</b>.
                Only publicly available information was analyzed.
                No private, restricted, or paid data sources were accessed.
            </p>
        `;

        /* =====================================================
           🔧 FIX 1: UPDATE RADAR GRAPH (ADDED, NOTHING REMOVED)
        ====================================================== */
        if (data.radar_stats) {
            updateRadarGraph(data.radar_stats);
        }

        /* =====================================================
           🔧 FIX 2: DASHBOARD TOP STATS SYNC (ADDED ONLY)
        ====================================================== */

        const identityMatchEl = document.getElementById("identityMatchValue");
        if (identityMatchEl) {
            identityMatchEl.innerText = data.identity_confidence.confidence_score + "%";
        }

        const footprintEl = document.getElementById("footprintCount");
        if (footprintEl) {
            footprintEl.innerText = platformFound;
        }

        const threatEl = document.getElementById("threatLevelValue");
        if (threatEl) {
            threatEl.innerText = data.risk.level;
        }

    });
}
