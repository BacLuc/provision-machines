from pyinfra import host
import io

from pyinfra.operations import (
    files,
    server,
)

if host.data.get("firefox", {}).get("enabled", False):
    # Set defaults for firefox role
    firefox_defaults = {
        "policies": {
            "policies": {
                "ExtensionSettings": {
                    "uBlock0@raymondhill.net": {
                        "installation_mode": "normal_installed",
                        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi",
                        "private_browsing": True,
                    },
                    "keepassxc-browser@keepassxc.org": {
                        "installation_mode": "normal_installed",
                        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/keepassxc-browser/latest.xpi",
                        "private_browsing": True,
                    },
                    "idcac-pub@guus.ninja": {
                        "installation_mode": "normal_installed",
                        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/istilldontcareaboutcookies/latest.xpi",
                        "private_browsing": True,
                    },
                    "jid1-MnnxcxisBPnSXQ@jetpack": {
                        "installation_mode": "normal_installed",
                        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/privacy-badger17/latest.xpi",
                        "private_browsing": True,
                    },
                    "addon@darkreader.org": {
                        "installation_mode": "normal_installed",
                        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/darkreader/latest.xpi",
                        "private_browsing": True,
                    },
                    "{11a68c03-baa3-41fb-869c-5172c4c4dd2e}": {
                        "installation_mode": "normal_installed",
                        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/tab_search/latest.xpi",
                        "private_browsing": True,
                    },
                },
                "Bookmarks": [
                    {
                        "Title": "searxng",
                        "URL": "localhost:13308",
                        "Favicon": "http://localhost:13308/static/themes/simple/img/favicon.svg",
                        "Placement": "toolbar",
                    },
                    {
                        "Title": "openwebui",
                        "URL": "localhost:13307",
                        "Favicon": "http://localhost:13307/static/favicon.svg",
                        "Placement": "toolbar",
                    },
                ],
                "SearchEngines": {
                    "Add": [
                        {
                            "Name": "searxng",
                            "URLTemplate": "http://localhost:13308/search?q={searchTerms}",
                            "Method": "GET",
                            "IconURL": "http://localhost:13308/static/themes/simple/img/favicon.svg",
                            "Alias": "searxng",
                            "Description": "searxng",
                        },
                    ],
                    "Default": "searxng",
                },
                "PasswordManagerEnabled": False,
                "GenerativeAI": {"Enabled": False},
                "Preferences": {},
            },
        },
    }
    
    # Combine defaults with host data
    firefox = firefox_defaults.copy()
    if host.data.get("firefox"):
        firefox.update(host.data.get("firefox", {}))

    # Install firefox
    # Note: snap operations would need to be implemented separately
    # as pyinfra doesn't have direct snap support
    # server.shell(
    #     name="Install firefox",
    #     commands=["snap install firefox"],
    #     _sudo=True,
    # )

    # Create /etc/firefox/policies directory
    files.directory(
        name="Create /etc/firefox/policies directory",
        path="/etc/firefox/policies",
        _sudo=True,
        mode="755",
    )

    # Install firefox addons via policies.json
    files.put(
        name="Install firefox addons via policies.json",
        src=io.StringIO(str(firefox["policies"]).replace("'", '"')),
        dest="/etc/firefox/policies/policies.json",
        _sudo=True,
        mode="644",
    )