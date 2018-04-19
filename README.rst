::

              __       __    __
    .--.--.--|__.-----|  |--|  |--.-----.-----.-----.
    |  |  |  |  |__ --|     |  _  |  _  |     |  -__|
    |________|__|_____|__|__|_____|_____|__|__|_____|
                                       version 2.3.3

    Build composable event pipeline servers with minimal effort.



    ===========================
    wishbone.decode.checkresults
    ===========================

    Version: 0.0.1

    Converts Nagios checkresults to the internal metric format.
    ---------------------------------------------------------


        Converts the Nagios checkresults data into the internal Wishbone metric
        format.


        Parameters:

            - sanitize_hostname(bool)(False)
               |  If True converts "." to "_".
               |  Might be practical when FQDN hostnames mess up the namespace
               |  such as Graphite.

            - source(str)("@data")
               |  The field containing the perdata.

            - destination(str)("@data")
               |  The field to store the Metric data.


        Queues:

            - inbox:    Incoming events

            - outbox:   Outgoing events

