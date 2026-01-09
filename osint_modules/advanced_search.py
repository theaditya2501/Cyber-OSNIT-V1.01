import requests
import smtplib
import dns.resolver

def check_pgp_keys(email):
    """
    Searches public HKP keyservers for PGP keys associated with the email.
    """
    url = f"https://keyserver.ubuntu.com/pks/lookup?search={email}&op=index&fingerprint=on&options=mr"
    try:
        r = requests.get(url, timeout=5)
        if "pub:" in r.text:
            return {
                "found": True,
                "server": "keyserver.ubuntu.com",
                "details": "PGP Key Found (Encrypted Comm Used)"
            }
    except:
        pass
    return {"found": False}

def smtp_analysis(email):
    """
    Performs a 'Safe' SMTP analysis (DNS MX Record + Banner Grab).
    """
    try:
        domain = email.split('@')[1]
        records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange)
        
        # Connect to Mail Server (Banner Grab only)
        server = smtplib.SMTP(mx_record, 25, timeout=5)
        server.ehlo()
        banner = server.docmd("NOOP")[1].decode('utf-8', errors='ignore')
        server.quit()

        return {
            "valid_mx": True,
            "mx_server": mx_record,
            "banner": banner[:50] + "..." 
        }
    except Exception as e:
        return {"valid_mx": False, "error": str(e)}

def run_advanced_search(email):
    return {
        "pgp": check_pgp_keys(email),
        "smtp": smtp_analysis(email)
    }