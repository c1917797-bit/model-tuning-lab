# Delivery Mode

- mode: Report
- reason: forward-test prompt explicitly asks for a Chinese HTML analysis report.
- final_html_contract: Report uses a scrolling HTML structure and does not use section.slide as the main structure.
- export_command: python scripts/render_html_report.py 'CASE_RUN/final/index.html' 'CASE_RUN/final/export'
- export_outputs: desktop-full.png + report-render-manifest.json
