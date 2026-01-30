

#  Northbridge Secure Banking System (Very Simple Explanation)

## What is this?

This project is a **small online banking system** built to show **how banks keep things safe** using technology.

It is not a real bank.
It is a **demonstration system** that shows:

* who is allowed to do what
* how money movements are controlled
* how all actions are recorded for review

---

## Why was this built?

Banks must:

* protect customer accounts
* prevent mistakes and fraud
* prove what happened if something goes wrong

This project shows **how those protections work in practice**, not just on paper.



## What can people do in the system?

###  Normal Users

A normal user can:

* Create an account
* Log in
* See their own account
* Add money to their account
* Send money to another user
* See their past transactions

A normal user **cannot**:

* See other people’s accounts
* See system logs
* Access admin features

---

###  Admin Users

An admin user can:

* Do everything a normal user can
* View system activity records (audit logs)

Admins are **restricted and monitored** — even their actions are recorded.

---

## How does the system protect accounts?

###  Logging In

Users must log in using:

* an email
* a password

If the password is wrong:

* access is denied
* the failed attempt is recorded

Passwords are **never stored in readable form**.

---

### Permissions

The system checks:

* who you are
* what role you have (user or admin)

This stops users from accessing things they are not allowed to see.

---

###  Money Rules

The system enforces rules such as:

* You cannot add a negative amount of money
* You cannot send money to yourself
* You cannot send more money than you have

If a rule is broken:

* the action is stopped
* the attempt is recorded

---

## What is an audit log?

An **audit log** is a record of what happened in the system.

It records:

* who did something
* what they tried to do
* whether it worked or failed
* when it happened

This is important because banks must be able to:

* investigate problems
* detect misuse
* prove accountability

---

## What actions are recorded?

The system records:

* account creation
* logins (successful and failed)
* viewing account information
* adding money
* sending money
* admin access to logs

Nothing important happens **without being recorded**.

---

## Why is this useful?

This system shows:

* how security rules work
* how mistakes are prevented
* how actions can be reviewed later

It proves that **risk control is built into the system**, not added later.

---

## How do you run it?

Start the system with:

```bash
uvicorn app.main:app --reload
```

Then open:

* `http://127.0.0.1:8000/` – system overview
* `http://127.0.0.1:8000/docs` – interactive testing



## Final Explanation (one sentence)

This project shows how a bank can control access, protect money, and keep records of everything that happens using software.




