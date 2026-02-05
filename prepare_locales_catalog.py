"""Convert Articles.strings files to JSON locales.

To update locales extract folder catalog from assets/catalog in the android APK
and copy it to the same directory as this file. Run `python prepare_locales_catalog.py`
and this script will create the articles.{locale}.json files under bring-api/locales.
"""

import glob
import json
import os
import re

for filename in glob.glob("**/Articles.strings", root_dir="./catalog", recursive=True):
    with open(os.path.join(os.getcwd(), "catalog", filename), encoding="UTF-8") as f:
        file = f.read()
        result = dict(
            re.findall(
                "^(.*)=(.*)$",
                file.replace("\\", ""),
                flags=re.MULTILINE,
            )
        )
        locale = os.path.split(filename)[0]

        with open(
            f"bring_api{os.sep}locales{os.sep}articles.{locale[0:2].lower()}-{locale[3:5]}.json",
            "w",
            encoding="utf-8",
        ) as t:
            json.dump(result, t, ensure_ascii=False, indent=2)
