import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import threading
import streamlit as st


def get_secret(key: str, default: str = "") -> str:
    """Lit d'abord les variables d'environnement système puis bascule sur st.secrets."""
    if key in os.environ and os.environ[key]:
        return os.environ[key]
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default


def send_alert_email(
    subject: str,
    body_html: str,
    recipient_email: str = "eric.kuter@gouv.nc",
    async_send: bool = True,
) -> bool:
    """Envoie un e-mail HTML via SMTP (Google Workspace / Gmail / Relay GNC)."""

    def _envoyer():
        smtp_server = get_secret("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(get_secret("SMTP_PORT", "465"))
        smtp_user = get_secret("SMTP_EMAIL", "")
        smtp_password = get_secret("SMTP_PASSWORD", "")

        if not smtp_user or not smtp_password:
            print("❌ [SMTP ERROR] Identifiants SMTP manquant dans les secrets.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"SURETIX Incidents <{smtp_user}>"
        msg["To"] = recipient_email
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        try:
            if smtp_port == 465:
                with smtplib.SMTP_SSL(
                    smtp_server, smtp_port, timeout=15
                ) as server:
                    server.login(smtp_user, smtp_password)
                    server.sendmail(smtp_user, recipient_email, msg.as_string())
            else:
                with smtplib.SMTP(
                    smtp_server, smtp_port, timeout=15
                ) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.sendmail(smtp_user, recipient_email, msg.as_string())

            print(f"✅ [SMTP SUCCESS] E-mail transmis à {recipient_email}")
            return True
        except Exception as e:
            print(f"❌ [SMTP ERROR] Échec de l'envoi : {e}")
            if not async_send:
                raise e
            return False

    if async_send:
        threading.Thread(target=_envoyer, daemon=True).start()
        return True
    else:
        return _envoyer()


def envoyer_notification_relance_sla(
    incidents_souffrance: list,
    recipient_email: str = "eric.kuter@gouv.nc",
):
    """Envoie un rapport synthétique d'incidents inactifs (SLA dépassé) au chargé de sûreté."""
    if not incidents_souffrance:
        return

    sujet = f"🚨 [SURETIX SLA] {len(incidents_souffrance)} incident(s) en souffrance"

    lignes_table = ""
    for inc in incidents_souffrance:
        lignes_table += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{inc.get('code_ticket')}</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{inc.get('titre')}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #d9534f; font-weight: bold;">{str(inc.get('priorite')).upper()}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{inc.get('demandeur_email')}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{str(inc.get('statut')).upper()}</td>
        </tr>
        """

    corps_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
            <div style="background-color: #d9534f; color: white; padding: 12px 20px; border-radius: 4px;">
                <h3 style="margin: 0;">🚨 Alerte SLA SURETIX — Incidents Inactifs</h3>
            </div>
            <p style="margin-top: 15px;">Bonjour,</p>
            <p>Les tickets suivants ont dépassé leur échéance de traitement sans action enregistrée :</p>
            
            <table style="border-collapse: collapse; width: 100%; margin-top: 10px;">
                <thead>
                    <tr style="background-color: #f2f2f2; text-align: left;">
                        <th style="padding: 8px; border: 1px solid #ddd;">Code</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Intitulé</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Priorité</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Demandeur</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Statut</th>
                    </tr>
                </thead>
                <tbody>
                    {lignes_table}
                </tbody>
            </table>
            
            <p style="margin-top: 20px;">
                <a href="https://suretix.streamlit.app" 
                   style="background-color: #0d6efd; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block;">
                    Consulter SURETIX
                </a>
            </p>
            <hr style="margin-top: 25px; border: none; border-top: 1px solid #eee;" />
            <p style="font-size: 11px; color: #777;">
                Notification automatique générée par SURETIX — Gouvernement de la Nouvelle-Calédonie.
            </p>
        </body>
    </html>
    """

    send_alert_email(
        subject=sujet,
        body_html=corps_html,
        recipient_email=recipient_email,
        async_send=True,
    )