#!/bin/bash
# Cho lan chay moi nhat cua build-ios-shell xong, in ket qua + dong loi (dung cho vong sua loi).
GH=/c/Users/Win10Pro-22H2/AppData/Local/gh/bin/gh.exe
R=dominhtuanE/allstar-ios-build
ID=${1:-$("$GH" run list --repo $R --limit 1 --json databaseId --jq '.[0].databaseId')}
"$GH" run watch "$ID" --repo $R --exit-status --interval 30 > /dev/null 2>&1
echo "run=$ID exit=$?"
"$GH" run view "$ID" --repo $R 2>&1 | sed -n '/JOBS/,/ANNOTATIONS/p'
"$GH" run view "$ID" --repo $R --log-failed 2>&1 | grep -E "error:|error |BUILD FAILED|fatal|No such file|not found|Error:" | sed 's/^.*Z //' | sort | uniq | head -40 | cut -c1-400
