<p align="center"><img src="assets/banner.svg" alt="Azure Monitor: Be Told Before You Are Asked" width="100%"></p>

| | |
|-|-|
| **Time** | 90-105 min |
| **Cost** | free (a storage account and two alert rules cost cents) |
| **You need** | An Azure subscription where you can create resources, the Azure CLI (`az login` done), Python 3 and a terminal |

## How this lab works

1. **Fork** this repository to your own GitHub account (button at the top right).
2. Clone **your fork** in your Ubuntu environment (WSL on Windows, your OrbStack machine on Mac).
3. Read the lab below (the same text is in [`LAB.md`](LAB.md)) and follow the mission.
4. Answer the questions in [`SUBMISSION.md`](SUBMISSION.md). Where a question asks for output, paste it in a code block. No screenshots needed.
5. Commit and push. Open the **Actions** tab of your fork (click *I understand my workflows, go ahead and enable them* the first time). The **Lab check** shows what is still missing.
6. When the check is green, **submit the URL of your fork** in the course platform.

> [!NOTE]
> The check only looks at your answers and any files the lab asks you to commit. Your instructor reads your work and may ask you to explain any line.

<p align="center"><img src="assets/divider.svg" alt="" width="100%"></p>

## 🎬 The situation

<p align="center"><img src="assets/gifs/situation.gif" width="300" alt=""></p>

Beanie's receipts live in an Azure storage account. Two things can go wrong there and nobody would know: a bot starts hammering it (a bill, then an outage), or someone deletes the account by mistake (a disaster, with a name attached). Azure records both, in two very different places: **metrics** (numbers, every minute) and the **activity log** (who did what to which resource). Azure Monitor can alert on both, and both alerts need to reach a human through the same door: an **action group**.

> [!IMPORTANT]
> **Your mission**
> - Create one action group, `ag-beanie-oncall`, with an e-mail and a webhook receiver
> - Create a **metric alert** on the storage account's `Transactions` that fires on a traffic spike
> - Create an **activity log alert** that fires when a storage account is deleted
> - Let the checker attack your storage account and prove that both alerts fire
> - Tear down and prove it

**Time:** 105-120 min | **Cost:** a few cents (one storage account, alert rules) | **You need:** an Azure subscription, the Azure CLI, Python 3 and a terminal.

> [!NOTE]
> **If Azure answers `QuotaExceeded` or `SkuNotAvailable`, do not worry.** It is normal when Azure is in high demand, and it happens to everyone, including professionals. Run `az vm list-usage --location <region> -o table` to see your limits. To ask for more, open the portal: **Quotas > Compute > Request adjustment**, or open a support request. Often a different region or size works at once. This lab only needs a storage account, so you will rarely meet it here, but you will in the other Azure labs: get used to asking.

<p align="center"><img src="assets/divider.svg" alt="" width="100%"></p>

## Part 0 - The target

Fork this repository, clone your fork and run:

```bash
az login
./setup.sh
```

It creates the resource group `rg-monitor-alerts` and a storage account whose name starts with `stmon`, with a container `receipts`. Look at it in the portal: **Storage account > Monitoring > Metrics**. Pick the metric `Transactions`, aggregation `Sum`.

> [!NOTE]
> **Predict** Nobody is using the account. What does the graph show? What will it show when 300 requests arrive in one minute?

<p align="center"><img src="assets/divider.svg" alt="" width="100%"></p>

## Part 1 - The door: an action group

An alert rule never sends anything by itself. It points to an **action group**, a reusable list of receivers. Create **`ag-beanie-oncall`** in `rg-monitor-alerts` with:

- an **e-mail** receiver (use any address; it is not confirmed in this lab);
- a **webhook** receiver (any HTTPS URL, for example a chat tool's incoming webhook);
- a **short name** of 12 characters at most (it appears in SMS and e-mails).

```bash
az monitor action-group create --help
```

> [!NOTE]
> **Think** Why one action group for many alert rules rather than e-mail addresses inside each rule? What happens on the day the on-call person changes?

<p align="center"><img src="assets/divider.svg" alt="" width="100%"></p>

## Part 2 - The metric alert

Create **`alert-storage-transactions`** on your storage account:

- metric **`Transactions`**, aggregation **Total**, operator **greater than**, a threshold you choose (between 20 and 500) that normal traffic never reaches;
- **window 5 minutes, evaluated every 1 minute**;
- severity 0, 1 or 2 (0 is the most urgent: what deserves a 3 a.m. call?);
- it triggers your action group.

```bash
az monitor metrics alert create --help
```

> [!NOTE]
> **Think** With a 5-minute window evaluated every minute, how long after the spike starts can the alert fire at best? What does a 1-minute window gain, and what does it cost in false alarms?

<p align="center"><img src="assets/divider.svg" alt="" width="100%"></p>

## Part 3 - The activity log alert

Metrics tell you about traffic. To know **who deleted something**, you need the activity log. Create **`alert-storage-deleted`**:

- scope: your resource group (or the subscription);
- condition: category **Administrative** and operation **`Microsoft.Storage/storageAccounts/delete`**;
- it triggers the same action group.

```bash
az monitor activity-log alert create --help
```

> [!NOTE]
> **Think** This alert has no threshold and no window. Why? And what would be the cost of making the alert too broad, for example every "write" operation?

<p align="center"><img src="assets/divider.svg" alt="" width="100%"></p>

## Part 4 - Prove it

<p align="center"><img src="assets/gifs/verify.gif" width="300" alt=""></p>

```bash
./verify.sh
```

It reads the configuration of your three resources, then attacks: it sends 300 read requests to your storage account, creates and deletes a throwaway storage account, and waits for Azure to report both alerts as **Fired**. It takes about 10 to 15 minutes. Metrics arrive one to three minutes late, which is part of the lesson. Fix what is red and run it again until it ends with **ALL CHECKS PASSED**. Paste the output into `SUBMISSION.md` **before** you tear down. Then open **Monitor > Alerts** in the portal and look at the two fired alerts.

> [!TIP]
> **Stuck?** The metric alert never fires: the scope must be the storage account itself, the threshold must be below 300, and the aggregation must be `Total` (not `Average`). The activity log alert never fires: the operation name must be exactly as written and the scope must include the resource group. Action group checks fail: both a receiver of type e-mail and of type webhook are needed.

<p align="center"><img src="assets/divider.svg" alt="" width="100%"></p>

## Level up (optional)

- Add an alert on **availability** or on `Ingress` bytes, with a dynamic threshold. When is a dynamic threshold better than a fixed one?
- Add an **alert processing rule** that mutes the alerts during a maintenance window. Why not delete the alert instead?
- Add an alert on a **log query** (needs a Log Analytics workspace). What can it express that a metric cannot?

<p align="center"><img src="assets/divider.svg" alt="" width="100%"></p>

## Teardown (mandatory)

```bash
./teardown.sh
./verify-teardown.sh
```

The second command must print `TEARDOWN VERIFIED (`. Paste it into `SUBMISSION.md`.

<!-- teardown:start (generated by labs.py, do not edit) -->
## Tear down (mandatory)

<p align="center"><img src="assets/gifs/teardown.gif" width="300" alt=""></p>

Resources left behind cost money, keep doors open and pollute the next lab. Removing what you created is part of the job, so it is part of the submission: **you must prove it is gone**.

Do this **last**, after you have pasted your `verify` output into `SUBMISSION.md` (once you tear down, the lab can no longer be verified).

1. Run `./teardown.sh`. It deletes the resource group `rg-monitor-alerts` with the storage account, the action group and both alert rules.

Then run the proof:

```bash
./verify-teardown.sh
```

It prints a list of checks and must end with **TEARDOWN VERIFIED**. If it reports leftovers, remove them and run it again. Paste the full output in your submission.
<!-- teardown:end -->

<!-- submission:start (generated by labs.py, do not edit) -->
## 📬 Submission

Answer the questions in `SUBMISSION.md` in **your fork** (paste output in code blocks where asked), push, then submit the **URL of your fork**.

**Files to commit**

- `notes.md` with your commands (optional)

**Questions to answer**

1. Paste your action group (name, receivers). Why is an action group a separate resource from an alert rule, and what is the benefit of one group used by many rules? What are the other kinds of receiver besides e-mail and webhook?
2. Paste your metric alert (scope, metric, aggregation, window, frequency, threshold, severity). Explain window size and evaluation frequency in your own words. What is the difference between a static and a dynamic threshold?
3. Paste the activity log alert. What is the difference between a metric alert and an activity log alert (what each one watches, and how fast each reacts)? Why is "someone deleted the storage account" an activity log event and not a metric?
4. Paste the fired alert (from the Alerts blade or the REST call): its state, severity, the time the traffic started and the time the alert fired. What explains the delay? What does the monitor condition `Fired`/`Resolved` differ from the alert state `New`/`Acknowledged`/`Closed`?
5. Alert fatigue: your rule fires on `Transactions > 50`. Is that a good rule for a production storage account? Name two changes (a dynamic threshold, a different metric, a longer window, severity, a suppression window) that make an alert worth waking someone for.
6. Who receives the notification when your alert fires, and what do they need to find in it to act without opening a laptop? What is missing from a default e-mail?
7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.
8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.
<!-- submission:end -->
