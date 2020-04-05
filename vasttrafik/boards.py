from datetime import datetime, timedelta
from math import ceil

import tabulate


def get_columns():
    return {"arrival":
                [('sname', 'Line'),
                 ('time', 'Arrival'),
                 ('rtTime', 'Prel.Arrival'),
                 ('track', 'Track'),
                 ('direction', 'Direction')],
            "departure":
                [('sname', 'Line'),
                 ('time', 'Departure'),
                 ('rtTime', 'Prel.Departure'),
                 ('track', 'Track'),
                 ('direction', 'Direction')]}


class _Board:

    def __init__(self, json_document, current_time, request_columns):
        self.json_document = json_document
        self.current_time = current_time
        self.columns = request_columns

    def to_table(self, sort_by_line_num=False):
        """ Print json document as table """
        headers = []
        for _, header in self.columns:
            headers.append(header)
        table = []
        for element in self.json_document:
            row = []
            for item, _ in self.columns:
                if item in element:
                    row.append(element[item])
                else:
                    row.append(None)
            table.append(row)
        if sort_by_line_num:
            table.sort(key=lambda x: (x[0], x[3], x[1]))
        return tabulate.tabulate(table, headers)

    def to_table_with_diff(self, sort_by_line_num=False):
        """ Print json document as table """
        headers = []
        for _, header in self.columns:
            headers.append(header)
        table = []
        for element in self.json_document:
            row = []
            for item, _ in self.columns:
                if item in element:
                    value = element[item]
                    if item == 'rtTime':
                        value = self.__get_minutes_until_departure_from_element(element)
                    row.append(value)
                else:
                    row.append(None)
            table.append(row)
        if sort_by_line_num:
            table.sort(key=lambda x: (x[0], x[3], x[1]))
        return tabulate.tabulate(table, headers)

    def __get_minutes_until_departure_from_element(self, element):
        date = element['rtDate']
        time = element['rtTime']
        date_time = datetime.strptime("{} {}".format(date, time), "%Y-%m-%d %H:%M")
        current_date_time = datetime.now()
        minutes_until_depature = ceil((date_time - current_date_time) / timedelta(minutes=1))
        return minutes_until_depature if minutes_until_depature != 0 else 'Nu'


class ArrivalBoard(_Board):

    def __init__(self, json_document, current_time):
        super().__init__(json_document, current_time, get_columns()["arrival"])


class DepartureBoard(_Board):

    def __init__(self, json_document, current_time):
        super().__init__(json_document, current_time, get_columns()["departure"])
