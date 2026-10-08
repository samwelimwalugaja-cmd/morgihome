"""Custom SMTP email backend for MorgiHome.

Django's default smtplib backend uses socket.gethostname()/getfqdn() as the
HELO/EHLO argument. On Windows machines whose computer name contains spaces
(e.g. "Samweli-31.BUNI OFFICE"), Gmail rejects the handshake with:

    5.5.4 HELO/EHLO argument "..." invalid, closing connection

This backend sanitises the local hostname before handing it to smtplib.
"""

import smtplib
import socket
import ssl

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend as DjangoSmtpBackend


class EmailBackend(DjangoSmtpBackend):
    """SMTP backend that provides a Gmail-safe EHLO hostname."""

    def open(self, stream=None):
        if self.connection:
            return False

        # Prefer an explicit hostname from settings, otherwise sanitise the
        # local machine name so it is a valid SMTP EHLO argument.
        local_hostname = getattr(settings, "EMAIL_LOCALHOSTNAME", None)
        if not local_hostname:
            local_hostname = socket.gethostname()

        # SMTP EHLO hostnames must be dot-separated labels without spaces or
        # underscores. Replace whitespace/underscores with hyphens.
        local_hostname = (
            local_hostname.strip()
            .replace(" ", "-")
            .replace("\t", "-")
            .replace("_", "-")
        )

        # If the hostname still looks invalid (no dots, empty, etc.), fall back
        # to a safe placeholder so Gmail accepts the handshake.
        if not local_hostname or "." not in local_hostname:
            local_hostname = "localhost.localdomain"

        connection_params = {"local_hostname": local_hostname, "timeout": self.timeout}

        if self.use_ssl:
            connection_class = smtplib.SMTP_SSL
        else:
            connection_class = smtplib.SMTP

        try:
            self.connection = connection_class(
                self.host, self.port, **connection_params
            )
            self.connection.set_debuglevel(getattr(self, "debug_level", 0))
            if not self.use_ssl and self.use_tls:
                # Python 3.14 removed the deprecated keyfile/certfile arguments
                # from smtplib.starttls(); use an SSL context instead.
                context = ssl.create_default_context()
                if self.ssl_certfile:
                    context.load_cert_chain(
                        certfile=self.ssl_certfile, keyfile=self.ssl_keyfile
                    )
                self.connection.starttls(context=context)
                self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except OSError:
            if not self.fail_silently:
                raise
            return False
        except smtplib.SMTPException:
            if not self.fail_silently:
                raise
            return False
