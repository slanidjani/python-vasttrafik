# -*- coding: utf-8 -*-
"""
Västtrafik API
"""

import base64
import json
import requests
from datetime import datetime
from datetime import timedelta
from .boards import ArrivalBoard, DepartureBoard

TOKEN_URL = 'https://api.vasttrafik.se/token'
API_BASE_URL = 'https://api.vasttrafik.se/bin/rest.exe/v2'
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M'


class Error(Exception):
    pass


def _get_node(response, *ancestors):
    """ Traverse tree to node """
    document = response
    for ancestor in ancestors:
        if ancestor not in document:
            return {}
        else:
            document = document[ancestor]
    return document


class JourneyPlanner:
    """ Journey planner class"""

    def __init__(self, key, secret, expiry=59):
        self._key = key
        self._secret = secret
        self._expiry = expiry
        self._token = None
        self._token_expire_date = None
        self.update_token()

    def update_token(self):
        """ Get token from key and secret """
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + base64.b64encode(
                (self._key + ':' + self._secret).encode()).decode()
        }
        data = {'grant_type': 'client_credentials'}

        response = requests.post(TOKEN_URL, data=data, headers=headers)
        obj = json.loads(response.content.decode('UTF-8'))
        self._token = obj['access_token']
        self._token_expire_date = (
                datetime.now() +
                timedelta(minutes=self._expiry))

    # LOCATION

    def get_all_stops(self):
        """ location.allstops """
        response = self._request(
            'location.allstops')
        return _get_node(response, 'LocationList', 'StopLocation')

    def get_stops_by_nearby_stops(self, origin_coord_lat, origin_coord_long):
        """ location.nearbystops """
        response = self._request(
            'location.nearbystops',
            originCoordLat=origin_coord_lat,
            originCoordLong=origin_coord_long)
        return _get_node(response, 'LocationList', 'StopLocation')

    def get_stops_by_nearby_address(self, origin_coord_lat, origin_coord_long):
        """ location.nearbyaddress """
        response = self._request(
            'location.nearbyaddress',
            originCoordLat=origin_coord_lat,
            originCoordLong=origin_coord_long)
        return _get_node(response, 'LocationList', 'CoordLocation')

    def get_stops_by_name(self, name):
        """ location.name """
        response = self._request(
            'location.name',
            input=name)
        return _get_node(response, 'LocationList', 'StopLocation')

    # ARRIVAL BOARD

    def get_arrival_board_at_stop(self, stop_id, date=None, direction=None):
        """ arrivalBoard """
        date = date if date else datetime.now()
        request_parameters = {
            'id': stop_id,
            'date': date.strftime(DATE_FORMAT),
            'time': date.strftime(TIME_FORMAT)
        }
        if direction:
            request_parameters['directiona'] = direction
        response = self._request(
            'arrivalBoard',
            **request_parameters)
        return ArrivalBoard(_get_node(response, 'ArrivalBoard', 'Arrival'), date.strftime(TIME_FORMAT))

    # DEPARTURE BOARD

    def get_departure_board_at_stop(self, stop_id, date=None, direction=None):
        """ departureBoard """
        date = date if date else datetime.now()
        request_parameters = {
            'id': stop_id,
            'date': date.strftime(DATE_FORMAT),
            'time': date.strftime(TIME_FORMAT)
        }
        if direction:
            request_parameters['direction'] = direction
        response = self._request(
            'departureBoard',
            **request_parameters)
        return DepartureBoard(_get_node(response, 'DepartureBoard', 'Departure'), date.strftime(TIME_FORMAT))

    def get_arrival_board_from_stop_name(self, stop_name, date=None, direction=None):
        return self.__get_board_from_stop_name('arrival', stop_name, date, direction)

    def get_departure_board_from_stop_name(self, stop_name, date=None, direction=None):
        return self.__get_board_from_stop_name('departure', stop_name, date, direction)

    def __get_board_from_stop_name(self, board_type, stop_name, date=None, direction=None):
        first_matched_stop = self.get_stops_by_name(stop_name)[0]
        assert stop_name.casefold() in first_matched_stop['name'].casefold(), \
            'Stop match {} does not match found stop {}'.format(stop_name, first_matched_stop['name'])
        if board_type == 'arrival':
            return self.get_arrival_board_at_stop(first_matched_stop["id"], date, direction)
        elif board_type == 'departure':
            return self.get_departure_board_at_stop(first_matched_stop["id"], date, direction)
        else:
            raise Exception

    # TRIP

    def get_trip_from_origin_dest_id(self, origin_id, dest_id, date=None):
        """ trip """
        date = date if date else datetime.now()
        response = self._request(
            'trip',
            originId=origin_id,
            destId=dest_id,
            date=date.strftime(DATE_FORMAT),
            time=date.strftime(TIME_FORMAT))
        return _get_node(response, 'TripList', 'Trip')

    def _request(self, service, **parameters):
        """ request builder """
        urlformat = "{baseurl}/{service}?{parameters}&format=json"
        url = urlformat.format(
            baseurl=API_BASE_URL,
            service=service,
            parameters="&".join([
                "{}={}".format(key, value) for key, value in parameters.items()
            ]))
        if datetime.now() > self._token_expire_date:
            self.update_token()
        headers = {'Authorization': 'Bearer ' + self._token}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(res.content.decode('UTF-8'))
        else:
            raise Error('Error: ' + str(res.status_code) +
                        str(res.content))
