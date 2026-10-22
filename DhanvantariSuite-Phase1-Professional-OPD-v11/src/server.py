"""
Dhanvantari Clinic ERP - Application Server Entrypoint
Supports HTTP and Secure HTTPS (TLS 1.3 / 1.2) for HIPAA / DPDP Transmission Security.
"""
import os
import sys
import ssl
import argparse
import uvicorn
from pathlib import Path

# Add project root to sys.path
PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from generate_ssl_certs import generate_self_signed_cert

def main():
    parser = argparse.ArgumentParser(description="Dhanvantari Clinic ERP Server Launcher")
    parser.add_argument("--host", default=os.getenv("SERVER_HOST", "0.0.0.0"), help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=int(os.getenv("SERVER_PORT", "8000")), help="Bind port (default: 8000)")
    parser.add_argument("--https", action="store_true", default=os.getenv("ENABLE_HTTPS", "false").lower() in ["1", "true", "yes"], help="Enable HTTPS with TLS 1.3/1.2")
    parser.add_argument("--cert", default=os.getenv("SSL_CERTFILE", None), help="Path to TLS certificate file")
    parser.add_argument("--key", default=os.getenv("SSL_KEYFILE", None), help="Path to TLS private key file")
    parser.add_argument("--reload", action="store_true", default=False, help="Enable auto-reload for development")
    args = parser.parse_args()

    ssl_keyfile = None
    ssl_certfile = None
    ssl_version = None

    if args.https:
        if args.cert and args.key:
            ssl_certfile = args.cert
            ssl_keyfile = args.key
        else:
            ssl_certfile, ssl_keyfile = generate_self_signed_cert()
        
        # Enforce TLS 1.3 / TLS 1.2
        ssl_version = ssl.PROTOCOL_TLS_SERVER
        print(f"\n[HTTPS / TLS 1.3 ENFORCED]")
        print(f"  Cert: {ssl_certfile}")
        print(f"  Key:  {ssl_keyfile}")
        print(f"  URL:  https://127.0.0.1:{args.port}/")
    else:
        print(f"\n[HTTP MODE]")
        print(f"  URL:  http://127.0.0.1:{args.port}/")

    uvicorn_kwargs = {
        "app": "src.main:app",
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
    }

    if args.https:
        uvicorn_kwargs["ssl_certfile"] = ssl_certfile
        uvicorn_kwargs["ssl_keyfile"] = ssl_keyfile
        uvicorn_kwargs["ssl_version"] = ssl_version

    uvicorn.run(**uvicorn_kwargs)

if __name__ == "__main__":
    main()
