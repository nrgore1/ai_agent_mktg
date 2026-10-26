# Publishing accounts

A publishing account is the identity and permission scope used for a communication. Account connection never authorizes unlimited communications.

GitHub: choose a repository you own for legitimate product updates or feedback. Provide a fine-grained token restricted to that repository with Issues write permission through server secrets. The implemented connector creates an issue with approved title/content and a delivery correlation marker. It is not a general marketing broadcaster. See [official GitHub API](https://docs.github.com/en/rest/issues/issues#create-an-issue).

Email: choose an authenticated sender domain/mailbox and a sandbox recipient you control. Configure SMTP host, TLS port, username, password and sender server-side. The current adapter permits only that exact test recipient, requires product-specific opt-in and checks suppressions. Production campaign email needs unsubscribe handling, bounce processing and delivery reconciliation before enablement.

LinkedIn/X: name the intended company page or account. Their separate developer app, OAuth scopes, authorized APIs and test environment must be implemented and approved; no connector is currently provided. Product Hunt, Reddit and HN initially use manual packages. HN submissions must follow its [official guidelines](https://news.ycombinator.com/newsguidelines.html), including the restriction on generated text. No voting/review manipulation.

Supply only service names and account/repository identifiers in chat. Put credentials in the server's protected environment. `GROWTHPILOT_ENABLE_LIVE` defaults false. Before enabling it, test the selected connector in an owned sandbox, verify delivery receipts, validate recipient consent, and review exact actions in the console.
