import vasttrafik as vt


def main():
    key = ''
    secret = ''
    journey_planner = vt.JourneyPlanner(key, secret)
    departure_board = journey_planner.get_departure_board_from_stop_name("lindholmen")
    print(departure_board.to_table_with_diff(sort_by_line_num=True))


if __name__ == '__main__':
    main()
