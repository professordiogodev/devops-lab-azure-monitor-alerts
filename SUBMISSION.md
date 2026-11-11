# Submission

Fork URL: <!-- paste the URL of your fork here -->

## Files to commit

- [ ] `notes.md` with your commands (optional)

## Questions

Answer in your own words. Where a question asks for output, paste it in a code block.

### Q1. Paste your action group (name, receivers). Why is an action group a separate resource from an alert rule, and what is the benefit of one group used by many rules? What are the other kinds of receiver besides e-mail and webhook?

**Your answer:**

<!-- replace this line with your answer -->

### Q2. Paste your metric alert (scope, metric, aggregation, window, frequency, threshold, severity). Explain window size and evaluation frequency in your own words. What is the difference between a static and a dynamic threshold?

**Your answer:**

<!-- replace this line with your answer -->

### Q3. Paste the activity log alert. What is the difference between a metric alert and an activity log alert (what each one watches, and how fast each reacts)? Why is "someone deleted the storage account" an activity log event and not a metric?

**Your answer:**

<!-- replace this line with your answer -->

### Q4. Paste the fired alert (from the Alerts blade or the REST call): its state, severity, the time the traffic started and the time the alert fired. What explains the delay? What does the monitor condition `Fired`/`Resolved` differ from the alert state `New`/`Acknowledged`/`Closed`?

**Your answer:**

<!-- replace this line with your answer -->

### Q5. Alert fatigue: your rule fires on `Transactions > 50`. Is that a good rule for a production storage account? Name two changes (a dynamic threshold, a different metric, a longer window, severity, a suppression window) that make an alert worth waking someone for.

**Your answer:**

<!-- replace this line with your answer -->

### Q6. Who receives the notification when your alert fires, and what do they need to find in it to act without opening a laptop? What is missing from a default e-mail?

**Your answer:**

<!-- replace this line with your answer -->

### Q7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.

**Your answer:**

<!-- replace this line with your answer -->

### Q8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.

**Your answer:**

<!-- replace this line with your answer -->
