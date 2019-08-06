import socket
import psutil
import random

from horovod.run.util import threads


def _get_local_host_addresses():
    local_addresses = []
    for intf_info_list in psutil.net_if_addrs().values():
        for intf_info in intf_info_list:
            if intf_info.family == socket.AF_INET:
                local_addresses.append(intf_info.address)
    return local_addresses


def get_local_host_intfs():
    return set(psutil.net_if_addrs().keys())


def filter_local_addresses(all_host_names):
    local_addresses = _get_local_host_addresses()

    def resolve_host_name(host_name):
        try:
            return socket.gethostbyname(host_name)
        except socket.gaierror:
            return None

    args_list = [[host] for host in all_host_names]
    host_addresses = threads.execute_function_multithreaded(
        resolve_host_name, args_list)

    # host_addresses is a map
    remote_host_names = []
    for i in range(len(all_host_names)):
        host_address = host_addresses[i]
        host_name = all_host_names[i]

        if not host_address or host_address not in local_addresses:
            remote_host_names.append(host_name)

    return remote_host_names


# Given server factory and handler, find a usable port
def find_port(server_factory, handler):
    min_port = 1024
    max_port = 65536
    num_ports = max_port - min_port
    start_port = random.randrange(0, num_ports)
    for port_offset in range(num_ports):
        try:
            port = min_port + (start_port + port_offset) % num_ports
            addr = ('', port)
            server = server_factory(addr, handler)
            return server, port
        except Exception as e:
            pass

    raise Exception('Rendezvous ERROR: Unable to find a port to bind to.')
