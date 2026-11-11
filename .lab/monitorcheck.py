#!/usr/bin/env python3
import concurrent.futures, datetime, json, os, subprocess, sys, time, urllib.request, urllib.error
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
RG, LAB = "rg-monitor-alerts", "azure-monitor-alerts"
passed = failed = 0


def check(desc, ok, hint=""):
    global passed, failed
    if ok:
        passed += 1; print("PASS  " + desc, flush=True)
    else:
        failed += 1; print("FAIL  " + desc + (("   -> " + hint) if hint else ""), flush=True)


def az(*a, timeout=300):
    r = subprocess.run(("az",) + a, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def azj(*a):
    rc, out, err = az(*a, "-o", "json")
    try:
        return json.loads(out) if rc == 0 and out.strip() else None
    except Exception:
        return None


def finish():
    print()
    print(("ALL CHECKS PASSED (%d/%d)" % (passed, passed)) if failed == 0 else ("%d check(s) failed, %d passed" % (failed, passed)))
    sys.exit(1 if failed else 0)


def wait_for(fn, secs, step=20):
    end = time.time() + secs
    while time.time() < end:
        try:
            r = fn()
            if r:
                return r
        except Exception:
            pass
        time.sleep(step)
    return None


sub = azj("account", "show") or {}
sid = sub.get("id", "")
print("Subscription %s" % sub.get("name"))
rg = azj("group", "show", "-n", RG)
check("resource group %s exists (run ./setup.sh)" % RG, bool(rg))
if not rg:
    finish()
sas = azj("storage", "account", "list", "-g", RG) or []
sa = next((s for s in sas if s["name"].startswith("stmon") and not s["name"].startswith("stmontmp")), None)
check("the storage account to watch exists", bool(sa))
if not sa:
    finish()

print("== The action group ==")
ag = next((g for g in (azj("monitor", "action-group", "list", "-g", RG) or []) if g["name"] == "ag-beanie-oncall"), None)
check("an action group named ag-beanie-oncall exists and is enabled", bool(ag) and ag.get("enabled"), "az monitor action-group create")
if ag:
    check("it has an e-mail receiver and a webhook receiver", len(ag.get("emailReceivers") or []) >= 1 and len(ag.get("webhookReceivers") or []) >= 1, "e-mail: who is paged; webhook: where a chat or ticket system listens")
    check("its short name is set (max 12 characters, it appears in SMS and e-mails)", 1 <= len(ag.get("groupShortName") or "") <= 12)

print("== The metric alert ==")
ma = next((a for a in (azj("monitor", "metrics", "alert", "list", "-g", RG) or []) if a["name"] == "alert-storage-transactions"), None)
check("a metric alert named alert-storage-transactions exists and is enabled", bool(ma) and ma.get("enabled"), "az monitor metrics alert create")
if ma:
    crit = (ma.get("criteria") or {}).get("allOf", [{}])[0]
    check("it watches the storage account itself", sa["id"].lower() in [s.lower() for s in ma.get("scopes", [])])
    check("metric Transactions, aggregation Total, operator GreaterThan", crit.get("metricName") == "Transactions" and crit.get("timeAggregation") == "Total" and crit.get("operator") == "GreaterThan", str(crit)[:150])
    check("threshold between 20 and 500 transactions", 20 <= float(crit.get("threshold", 0)) <= 500, "threshold %s" % crit.get("threshold"))
    check("window PT5M, evaluated every PT1M, severity 0 to 2", ma.get("windowSize") == "PT5M" and ma.get("evaluationFrequency") == "PT1M" and ma.get("severity") in (0, 1, 2), "%s / %s / sev %s" % (ma.get("windowSize"), ma.get("evaluationFrequency"), ma.get("severity")))
    check("it triggers the action group", bool(ag) and any(x.get("actionGroupId", "").lower() == ag["id"].lower() for x in ma.get("actions", [])))

print("== The activity log alert ==")
la = next((a for a in (azj("monitor", "activity-log", "alert", "list", "-g", RG) or []) if a["name"] == "alert-storage-deleted"), None)
check("an activity log alert named alert-storage-deleted exists and is enabled", bool(la) and la.get("enabled"), "az monitor activity-log alert create")
if la:
    conds = {c["field"]: c["equals"] for c in (la.get("condition") or {}).get("allOf", [])}
    check("it matches the operation Microsoft.Storage/storageAccounts/delete in the Administrative category", conds.get("operationName", "").lower() == "microsoft.storage/storageaccounts/delete" and conds.get("category") == "Administrative", str(conds))
    scopes = [s.lower() for s in la.get("scopes", [])]
    check("its scope covers the resource group (or the subscription)", any(("/resourcegroups/" + RG) in s or s == "/subscriptions/" + sid.lower() for s in scopes), str(scopes))
    check("it triggers the action group", bool(ag) and any(x.get("actionGroupId", "").lower() == ag["id"].lower() for x in (la.get("actions") or {}).get("actionGroups", [])))
if not (ma and la and ag):
    finish()

print("== Make it fire (about 10 minutes) ==")
t0 = datetime.datetime.utcnow()
rc, key, err = az("storage", "account", "keys", "list", "-g", RG, "-n", sa["name"], "--query", "[0].value", "-o", "tsv")
key = key.strip()
exp = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%MZ")
rc, sastoken, err = az("storage", "container", "generate-sas", "--account-name", sa["name"], "-n", "receipts", "--permissions", "rl", "--expiry", exp, "--account-key", key, "-o", "tsv")
sastoken = sastoken.strip()
url = "https://%s.blob.core.windows.net/receipts?restype=container&comp=list&%s" % (sa["name"], sastoken)


def hit(_):
    try:
        return urllib.request.urlopen(url, timeout=15).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def burst(n=300):
    with concurrent.futures.ThreadPoolExecutor(20) as ex:
        return list(ex.map(hit, range(n)))


codes = burst()
check("300 read requests were sent to the storage account (%d answered 200)" % codes.count(200), codes.count(200) > 200, str(set(codes)))
# a throwaway account is created and deleted to trigger the activity log alert
tmp = "stmontmp" + sid.replace("-", "")[:10]
az("storage", "account", "create", "-g", RG, "-n", tmp, "-l", rg["location"], "--sku", "Standard_LRS", "--tags", "lab=" + LAB, "owner=checker")
rc, o, e = az("storage", "account", "delete", "-g", RG, "-n", tmp, "--yes")
check("a throwaway storage account was created and deleted (this is the event the activity log alert watches)", rc == 0, e[-150:])


def fired(rule):
    def f():
        burst(150)
        rc, out, err = az("rest", "--method", "get", "--url", "/subscriptions/%s/providers/Microsoft.AlertsManagement/alerts?api-version=2019-05-05-preview&targetResourceGroup=%s" % (sid, RG))
        try:
            items = json.loads(out).get("value", [])
        except Exception:
            return None
        return [i for i in items if i["properties"]["essentials"].get("alertRule", "").endswith("/" + rule) and i["properties"]["essentials"]["startDateTime"] >= t0.strftime("%Y-%m-%dT%H:%M:%S")] or None
    return f


m = wait_for(fired("alert-storage-transactions"), 780, 30)
check("the metric alert FIRED (%s)" % ("severity %s after %d s" % (m[0]["properties"]["essentials"]["severity"], (datetime.datetime.utcnow() - t0).total_seconds()) if m else "it did not"), bool(m), "metrics arrive 1 to 3 minutes late; is the threshold lower than 300 and is the scope the storage account?")
l = wait_for(fired("alert-storage-deleted"), 300, 20)
check("the activity log alert FIRED for the deletion", bool(l))
finish()
