#!/usr/bin/env python3

import argparse
import sys
from typing import List, Tuple

import testcases
from implementations import IMPLEMENTATIONS, Role
from interop import InteropRunner
from testcases import MEASUREMENTS, TESTCASES

implementations = {
    name: {"image": value["image"], "url": value["url"]}
    for name, value in IMPLEMENTATIONS.items()
}
client_implementations = [
    name
    for name, value in IMPLEMENTATIONS.items()
    if value["role"] == Role.BOTH or value["role"] == Role.CLIENT
]
server_implementations = [
    name
    for name, value in IMPLEMENTATIONS.items()
    if value["role"] == Role.BOTH or value["role"] == Role.SERVER
]


def main():
    def get_args():
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-d",
            "--debug",
            action="store_const",
            const=True,
            default=False,
            help="turn on debug logs",
        )
        parser.add_argument(
            "-s", "--server", help="server implementations (comma-separated)"
        )
        parser.add_argument(
            "-c", "--client", help="client implementations (comma-separated)"
        )
        parser.add_argument(
            "-t",
            "--test",
            help="test cases (comma-separatated). Valid test cases are: "
            + ", ".join([x.name() for x in TESTCASES + MEASUREMENTS]),
        )
        parser.add_argument(
            "-r",
            "--replace",
            help="replace path of implementation. Example: -r myquicimpl=dockertagname",
        )
        parser.add_argument(
            "-l",
            "--log-dir",
            help="log directory",
            default="",
        )
        parser.add_argument(
            "-f", "--save-files", help="save downloaded files if a test fails"
        )
        parser.add_argument(
            "-j", "--json", help="output the matrix to file in json format"
        )
        parser.add_argument(
            "-a", "--default-delay", help="Set default Delay", default = "15ms"
        )
        parser.add_argument(
            "-b", "--custom-name", help="Set custom component of log folder", default = ""
        )
        parser.add_argument(
            "-e", "--drop-to-client", help="Set custom packets to drop towards the client", default = ""
        )
        parser.add_argument(
            "-g", "--drop-to-server", help="Set custom packets to drop towards the server", default = ""
        )
        parser.add_argument(
            "-i", "--bandwidth", help="Set custom bandwidth", default = ""
        )
        parser.add_argument(
            "-k", "--queue", help="Set custom queue size", default = ""
        )
        parser.add_argument(
            "-m", "--enable-instant-ack", help="Enables sending ACK separately from SH.", default = ""
        )
        parser.add_argument(
            "-n", "--instant-ack-delay", help="Sets delay after sending the instant ACK.", default = ""
        )
        parser.add_argument(
            "-o", "--delay-first-packet", help="Sets delay before first packet is send. Independent of instant ACK or coalesced.", default = ""
        )
        parser.add_argument(
            "-p", "--pcap_disable", help="Disable storing pcaps.", default=False, const=True, action="store_const",
        )
        parser.add_argument(
            "-q", "--file-size", help="File size for goodput measurement in MB", default = "10"
        )
        parser.add_argument(
                    "-u", "--repetitions", help="# repetitions", default = "100"
                )
        parser.add_argument(
            "-v", "--cert-chain-length", help="length of cert chain", default = "1"
        )

        parser.add_argument(
            "-w", "--disable-qlog", help="disable qlog logging", default=False, const=True, action="store_const",
        )

        return parser.parse_args()

    replace_arg = get_args().replace
    if replace_arg:
        for s in replace_arg.split(","):
            pair = s.split("=")
            if len(pair) != 2:
                sys.exit("Invalid format for replace")
            name, image = pair[0], pair[1]
            if name not in IMPLEMENTATIONS:
                sys.exit("Implementation " + name + " not found.")
            implementations[name]["image"] = image

    def get_impls(arg, availableImpls, role) -> List[str]:
        if not arg:
            return availableImpls
        impls = []
        for s in arg.split(","):
            if s not in availableImpls:
                sys.exit(role + " implementation " + s + " not found.")
            impls.append(s)
        return impls

    def get_tests_and_measurements(
        arg,
    ) -> Tuple[List[testcases.TestCase], List[testcases.TestCase]]:
        if arg is None:
            return TESTCASES, MEASUREMENTS
        elif arg == "onlyTests":
            return TESTCASES, []
        elif arg == "onlyMeasurements":
            return [], MEASUREMENTS
        elif not arg:
            return []
        tests = []
        measurements = []
        for t in arg.split(","):
            if t in [tc.name() for tc in TESTCASES]:
                tests += [tc for tc in TESTCASES if tc.name() == t]
            elif t in [tc.name() for tc in MEASUREMENTS]:
                measurements += [tc for tc in MEASUREMENTS if tc.name() == t]
            else:
                print(
                    (
                        "Test case {} not found.\n"
                        "Available testcases: {}\n"
                        "Available measurements: {}"
                    ).format(
                        t,
                        ", ".join([t.name() for t in TESTCASES]),
                        ", ".join([t.name() for t in MEASUREMENTS]),
                    )
                )
                sys.exit()
        return tests, measurements

    t = get_tests_and_measurements(get_args().test)
    return InteropRunner(
        implementations=implementations,
        servers=get_impls(get_args().server, server_implementations, "Server"),
        clients=get_impls(get_args().client, client_implementations, "Client"),
        tests=t[0],
        measurements=t[1],
        output=get_args().json,
        debug=get_args().debug,
        log_dir=get_args().log_dir,
        save_files=get_args().save_files,
        custom_name=get_args().custom_name,
        default_delay=get_args().default_delay,
        drop_to_server=get_args().drop_to_server,
        drop_to_client=get_args().drop_to_client,
        enable_instant_ack=get_args().enable_instant_ack,
        enable_instant_ack_delay=get_args().instant_ack_delay,
        enable_first_packet_delay=get_args().delay_first_packet,
        repetitions=get_args().repetitions,
        pcaps_disable=get_args().pcap_disable,
        file_size=get_args().file_size,
        cert_chain=get_args().cert_chain_length,
        enable_qlog=not get_args().disable_qlog,
    ).run()


if __name__ == "__main__":
    sys.exit(main())
