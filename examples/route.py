from ipaddress import IPv4Network, IPv4Address

from wiederverwendbar.route import RouteManager, Route

if __name__ == '__main__':
    route_manager = RouteManager()
    test_route = Route(target=IPv4Network("192.168.200.0/24"), gateway=IPv4Address("192.168.65.1"))
    result_add = route_manager.create(test_route)
    all_routes = route_manager.get_all()
    result_delete = route_manager.delete(test_route)

    print()
