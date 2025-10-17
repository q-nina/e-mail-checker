# Email Syntax, MX, and SMTP Validation App

A Streamlit-based web tool that validates email addresses for syntax correctness, MX record presence, and optionally SMTP recipient deliverability.
It’s designed for quick verification of email lists and for testing emails.

Test out the live app here: [Email Checker App](https://e-mail-checker.streamlit.app/)

## Features

**Email Syntax Validation**

* Detects common syntax issues (invalid characters, misplaced dots, etc.)
* Highlights the exact position of syntax errors

**MX Record Lookup**

* Checks if a domain has valid mail exchange (MX) records
* Confirms whether the domain can theoretically receive emails

**SMTP Recipient Check (Optional)**

* Attempts to connect to mail servers and verify if the recipient exists
* Does not send any actual emails
* May take long due to server response times

**Interactive Results Table**

* Displays results in a table
* CSV download


## How It Works

1. **Syntax Validation:**
   Uses regex-based logic to check the structure of each email address and locate issues.

2. **MX Record Check:**
   Looks up DNS MX records to verify that the domain is configured to receive mail.

3. **SMTP Recipient Check (Optional):**
   Optionally connects to the mail server to verify if it accepts the recipient address (without sending mail).


## Local Installation

### 1. Clone this repository

```bash
git clone https://github.com/q-nina/e-mail-checker.git
cd e-mail-checker
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Streamlit app

```bash
streamlit run app.py
```

##  Notes

* **MX check** does not guarantee deliverability — only that a mail server exists.
* **SMTP check** may not be supported by all providers (e.g., Outlook often blocks it).
* Be mindful that repeated SMTP checks on many domains may trigger anti-spam protections.

## License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

## Author

Developed by [q-nina](https://github.com/q-nina).

