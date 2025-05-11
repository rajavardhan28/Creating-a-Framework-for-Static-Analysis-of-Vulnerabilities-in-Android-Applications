import os
import json
import re
from androguard.misc import AnalyzeAPK
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Dangerous permissions to check for
DANGEROUS_PERMISSIONS = [
    "android.permission.READ_SMS",
    "android.permission.SEND_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.READ_CONTACTS",
    "android.permission.WRITE_CONTACTS",
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
    "android.permission.INTERNET"
]

# Patterns for detecting possible hardcoded secrets
PATTERNS = [
    r"(AKIA|AIza)[0-9A-Z]{16,}",
    r"([A-Za-z0-9]{32,})",  # Catch other base64 encoded strings
    r"AIza[0-9A-Za-z_-]{35}",  # Firebase keys
    r"aws_secret_access_key[\"']?\s*[:=]?\s*[\"']?([A-Za-z0-9+/=]{40})",  # AWS secrets
    r"([A-Za-z0-9]{16,32})"  # Base64-like strings, like API keys
]

def analyze_apk(apk_path):
    a, d, dx = AnalyzeAPK(apk_path)

    # Get the 'debuggable' status from the AndroidManifest.xml
    manifest = a.get_android_manifest_xml()
    debuggable = manifest.find("application").get("debuggable", "false") == "true"

    # Analyze permissions, activities, services, etc.
    analysis = {
        "package_name": a.get_package(),
        "permissions": a.get_permissions(),
        "dangerous_permissions": list(filter(lambda p: p in DANGEROUS_PERMISSIONS, a.get_permissions())),
        "activities": a.get_activities(),
        "services": a.get_services(),
        "receivers": a.get_receivers(),
        "providers": a.get_providers(),
        "is_debuggable": debuggable,  # Use the debuggable status from manifest
        "hardcoded_secrets": find_hardcoded_secrets(dx)
    }

    return analysis

def find_hardcoded_secrets(dx):
    secrets = []
    
    # Iterate through all methods to find potential hardcoded secrets
    for method in dx.get_methods():
        # Get the basic blocks of the method, which contains bytecode instructions
        basic_blocks = method.get_basic_blocks()

        for block in basic_blocks:
            for instruction in block.get_instructions():
                # Check if the instruction contains hardcoded secrets (API keys)
                for pattern in PATTERNS:
                    matches = re.findall(pattern, str(instruction))
                    if matches:
                        secrets.extend(matches)

    return list(set(secrets))

def save_json(data, output_path):
    # Save analysis results as a JSON file
    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)

def create_pdf(json_data, output_path):
    # Create a PDF report from the JSON data
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("APK Analysis Report", styles['Title']))
    story.append(Spacer(1, 12))

    # Section for APK details
    section_style = styles['Heading2']
    section_style.fontName = 'Helvetica-Bold'
    section_style.fontSize = 14

    for key, value in json_data.items():
        if value:
            story.append(Paragraph(f"<b>{key}:</b>", section_style))
            if isinstance(value, list):
                for item in value:
                    story.append(Paragraph(f"- {item}", styles['Normal']))
            else:
                story.append(Paragraph(str(value), styles['Normal']))
            story.append(Spacer(1, 12))

    doc.build(story)

# You can test with:
# result = analyze_apk('path_to_apk')
# save_json(result, 'output.json')
# create_pdf(result, 'output.pdf')
