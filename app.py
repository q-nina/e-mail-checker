from email_check_and_validate import validate_email_syntax, check_mx_records, check_smtp_recipient

import streamlit as st
import pandas as pd
import html

EXAMPLE_INPUT = "support-in@google.com, simple@example.com, user@outlook.com, john.doe@gmail.com, user@unknown-xxx.com, invalid..email@example.com, ., "

st.title("Email Syntax with MX and SMTP Validation")
st.markdown(f"""
Reliable email validation is essential to ensure successful communication and maintain high email deliverability by validating addresses thoroughly.

This app allows you to validate email addresses for correct syntax, check for MX records, and optionally verify deliverability with SMTP recipient acceptance, all with user privacy in mind..

Features:
- **Without ads and data collection**
- Syntax validation with error highlighting and position indicator
- MX record lookup for domain verification
- Optional SMTP recipient check for deliverability
- Results displayed in a table, downloadable as CSV

Try out the tool with this sample input:

`{EXAMPLE_INPUT}`
""")

with st.expander("See additional notes:"):
    st.markdown("""**Note:**
- Non-exhaustive regex patterns and checks for email validation (!)
- Catches most common errors, especially with invalid characters and dot placement.
- Checks responsiveness of mail server via SMTP if MX records exist.

**Example SMTP check behaviors:**
- Outlook emails usually cannot be verified via SMTP, but MX records are returned.
- Gmail emails can be verified via SMTP.
- Other domains may vary, but often if MX records exist, the email can be valid even if "SMTP check: No responsive mail servers found".
    
See footnotes at the bottom of the app for more information.
    """)

if st.button("Insert Example Input", help="Insert Example Input into the text area. Click \"Check Emails\" to run the example."):
    st.session_state["email_input"] = EXAMPLE_INPUT

email_input = st.text_area(
    "Enter email(s) (comma separated):",
    key="email_input"
)

check_smtp = st.checkbox("Perform SMTP check (slower)", value=False, help="Check SMTP recipient acceptance, i.e. whether the mail server accepts emails without sending actual emails. Only performed if MX records exist. This may be slow depending on the number of emails and server responsiveness.")

def show_email_error(email_var: str, error_input: dict):
    if "position" in error_input:
        pos = error_input["position"]
    else:
        pos = None
    if pos is not None and 0 <= pos < len(email_var):
        safe_email = html.escape(email_var)
        st.markdown(f"**Email:** `{safe_email}`<br>" + f"{'&nbsp; ' * (pos + 8)}^", unsafe_allow_html=True)
        st.markdown(f"**Error:** {error_input['message']} (at position {pos})")
    else:
        st.markdown(f"**Email:** `{email_var}`")
        st.markdown(f"**Error:** {error_input['message']}")

if st.button("Check Emails", help="Check Emails for Syntax, MX Records, and optionally SMTP Recipient Acceptance"):
    results_container = st.empty()
    emails = [e.strip() for e in email_input.split(",") if e.strip()]
    results = []
    total = len(emails)
    with results_container.container():
        with st.status("Checking emails...", expanded=True) as status:
            for idx, email in enumerate(emails):
                status.update(label=f"Checking email {email} ({idx + 1}/{total})")
                row = {"Email": email}
                is_valid, error = validate_email_syntax(email)
                row["Valid Syntax"] = is_valid
                row["Syntax Error"] = error["message"] if error else ""
                row["MX Records"] = ""
                row["MX Error"] = ""
                row["SMTP Status"] = ""
                row["SMTP Message"] = ""

                if not is_valid and row:
                    show_email_error(row["Email"], error)
                else:
                    st.markdown(f"**Email:** `{row['Email']}`")
                st.markdown(f"- {'✅ Valid Syntax' if is_valid else f'❌ Invalid Syntax: {row['Syntax Error']}'}")

                if is_valid:
                    status.update(label=f"Checking MX Records... ({idx + 1}/{total})")
                    ok, mx = check_mx_records(email.split("@")[-1])
                    if ok:
                        row["MX Records"] = ", ".join([f"{pref}:{host}" for pref, host in mx])
                    else:
                        row["MX Error"] = mx

                    safe_mx_records = html.escape(row["MX Records"])
                    safe_mx_errors = html.escape(row["MX Error"])
                    st.markdown(
                        f"- {'✅ MX Check Successful <br> `' + safe_mx_records + "`" if row['MX Records'] 
                        else f'❌ MX Error {safe_mx_errors.replace('Server Do', '<br>Server Do')}'}",
                        unsafe_allow_html=True)

                    if check_smtp and ok:
                        status.update(label=f"Checking SMTP Recipient... ({idx + 1}/{total})")
                        smtp_ok, smtp_msg = check_smtp_recipient(email)
                        row["SMTP Status"] = "Accepted" if smtp_ok else "Rejected"
                        row["SMTP Message"] = smtp_msg

                        st.markdown(
                            f"- {'✅ SMTP Accepted' if row['SMTP Status'] == "Accepted" 
                            else '❌ SMTP Rejected'} `{row['SMTP Message']}")

                status.update(label=f"Checked {idx + 1}/{total} emails")
                st.markdown("---")
                results.append(row)

    status.update(label="Done!", state="complete")

    df = pd.DataFrame(results)
    st.dataframe(df)

    csv = df.to_csv(index=False)
    st.download_button(
        label="Download results as CSV",
        data=csv,
        file_name="email_results.csv",
        mime="text/csv"
    )

# go back to top button
st.markdown(
    """
    <a href="#email-syntax-with-mx-and-smtp-validation" style="
        display: inline-block;
        padding: 0.5em 1.2em;
        border-radius: 6px;
        text-decoration: none;
        font-weight: 600;
        font-size: 1em;
        margin-top: 1em;
        box-shadow: 0 2px 6px rgba(0,0,0,0.07);
        transition: background 0.2s;
    " onmouseover="this.style.background='#1e40af'" onmouseout="this.style.background='#2563eb'">
        Go back to top
    </a>
    """,
    unsafe_allow_html=True
)

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
        © 2025 q-nina — <a href="https://github.com/q-nina/e-mail-checker.git" target="_blank">GitHub Repository</a> <br>
    
    **Feedback or issues?**  
    Please report them on [GitHub Issues](https://github.com/q-nina/e-mail-checker/issues)
    </div>
    """,
    unsafe_allow_html=True
)