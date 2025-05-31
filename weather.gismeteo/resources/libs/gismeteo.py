# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import calendar
import time
from typing import Any, Dict, List

import requests

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

__all__ = ['GismeteoError', 'GismeteoClient']

class GismeteoError(Exception):
    pass

class GismeteoClient(object):
    _base_url = 'https://services.gismeteo.net/inform-service/inf_chrome'

    def __init__(self, lang: str = 'en') -> None:
        self._lang = lang
        self._client = requests.Session()

    def __del__(self):
        self._client.close()

    @staticmethod
    def _extract_xml(r: requests.Response) -> etree.Element:
        try:
            return etree.fromstring(r.content)
        except Exception as e:
            raise GismeteoError(f'Fehler beim Parsen der XML-Antwort: {e}')

    def _get(self, url: str, params: dict = None, *args, **kwargs) -> requests.Response:
        params = params or {}
        params['lang'] = self._lang
        try:
            return self._client.get(url, params=params, *args, **kwargs)
        except Exception as e:
            raise GismeteoError(f'HTTP-Request fehlgeschlagen: {e}')

    # ------------- Locations -----------------
    @staticmethod
    def _get_locations_list(root: etree.Element) -> List[Dict[str, Any]]:
        result = []
        for item in root:
            location = {
                'name': item.attrib.get('n', item.attrib.get('name', 'Unbekannt')),
                'id': item.attrib.get('id', ''),
                'country': item.attrib.get('country_name', ''),
                'district': item.attrib.get('district_name', ''),
                'lat': item.attrib.get('lat', ''),
                'lng': item.attrib.get('lng', ''),
                'kind': item.attrib.get('kind', ''),
            }
            result.append(location)
        return result

    # ------------- Datumshandling -------------
    @staticmethod
    def _get_date(source: Any, tzone: int) -> Dict[str, Any]:
        if not source:
            return {'local': '', 'utc': '', 'unix': 0, 'offset': tzone or 0}
        try:
            if isinstance(source, float):
                local_stamp = int(source)
                local_date = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(local_stamp))
            else:
                local_date = str(source) if len(str(source)) > 10 else str(source) + 'T00:00:00'
                local_stamp = calendar.timegm(time.strptime(local_date, '%Y-%m-%dT%H:%M:%S'))
        except Exception:
            local_date = '1970-01-01T00:00:00'
            local_stamp = 0
        utc_stamp = local_stamp - (tzone * 60 if tzone else 0)
        return {
            'local': local_date,
            'utc': time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(utc_stamp)),
            'unix': utc_stamp,
            'offset': tzone or 0
        }

    # ------------- Forecast Handling -------------
    def _get_forecast_info(self, root: etree.Element) -> Dict[str, Any]:
        if not root or not len(root):
            raise GismeteoError('Fehler: Keine Standortdaten gefunden.')

        xml_location = root[0]
        tzone = self._get_int(xml_location.attrib.get('tzone', 0))
        return {
            'name': xml_location.attrib.get('name', xml_location.attrib.get('n', 'Unbekannt')),
            'id': xml_location.attrib.get('id', ''),
            'kind': xml_location.attrib.get('kind', ''),
            'country': xml_location.attrib.get('country_name', ''),
            'district': xml_location.attrib.get('district_name', ''),
            'lat': xml_location.attrib.get('lat', ''),
            'lng': xml_location.attrib.get('lng', ''),
            'cur_time': self._get_date(xml_location.attrib.get('cur_time', 0), tzone),
            'current': self._get_fact_forecast(xml_location),
            'days': self._get_days_forecast(xml_location),
        }

    def _get_item_forecast(self, xml_item: etree.Element, tzone: int) -> Dict[str, Any]:
        result = {}
        if not xml_item or not len(xml_item):
            return result
        xml_values = xml_item[0]
        result['date'] = self._get_date(xml_item.attrib.get('valid', 0), tzone)
        if xml_item.attrib.get('sunrise') is not None:
            result['sunrise'] = self._get_date(self._get_float(xml_item.attrib.get('sunrise')), tzone)
        if xml_item.attrib.get('sunset') is not None:
            result['sunset'] = self._get_date(self._get_float(xml_item.attrib.get('sunset')), tzone)
        result['temperature'] = {
            'air': self._get_int(xml_values.attrib.get('t')),
            'comfort': self._get_int(xml_values.attrib.get('hi')),
        }
        if xml_values.attrib.get('water_t') is not None:
            result['temperature']['water'] = self._get_int(xml_values.attrib.get('water_t'))
        result['description'] = xml_values.attrib.get('descr', '')
        result['humidity'] = self._get_int(xml_values.attrib.get('hum'))
        result['pressure'] = self._get_int(xml_values.attrib.get('p'))
        result['cloudiness'] = xml_values.attrib.get('cl', '')
        result['storm'] = (xml_values.attrib.get('ts', '0') == '1')
        result['precipitation'] = {
            'type': xml_values.attrib.get('pt', ''),
            'amount': self._get_float(xml_values.attrib.get('prflt')),
            'intensity': xml_values.attrib.get('pr', ''),
        }
        if xml_values.attrib.get('ph'):
            result['phenomenon'] = self._get_int(xml_values.attrib.get('ph'))
        if xml_item.attrib.get('tod') is not None:
            result['tod'] = self._get_int(xml_item.attrib.get('tod'))
        result['icon'] = xml_values.attrib.get('icon', '')
        result['gm'] = xml_values.attrib.get('grade', '')
        result['wind'] = {
            'speed': self._get_float(xml_values.attrib.get('ws')),
            'direction': xml_values.attrib.get('wd', ''),
        }
        return result

    def _get_fact_forecast(self, xml_location: etree.Element) -> Dict[str, Any]:
        fact = xml_location.find('fact')
        if fact is None:
            return {}
        return self._get_item_forecast(fact, self._get_int(xml_location.attrib.get('tzone', 0)))

    def _get_days_forecast(self, xml_location: etree.Element) -> List[Dict[str, Any]]:
        tzone = self._get_int(xml_location.attrib.get('tzone', 0))
        result = []
        for xml_day in xml_location.findall('day'):
            if xml_day.attrib.get('icon') is None:
                continue
            day = {
                'date': self._get_date(xml_day.attrib.get('date', 0), tzone),
                'sunrise': self._get_date(self._get_float(xml_day.attrib.get('sunrise')), tzone) if xml_day.attrib.get('sunrise') else {},
                'sunset': self._get_date(self._get_float(xml_day.attrib.get('sunset')), tzone) if xml_day.attrib.get('sunset') else {},
                'temperature': {
                    'min': self._get_int(xml_day.attrib.get('tmin')),
                    'max': self._get_int(xml_day.attrib.get('tmax')),
                },
                'description': xml_day.attrib.get('descr', ''),
                'humidity': {
                    'min': self._get_int(xml_day.attrib.get('hummin')),
                    'max': self._get_int(xml_day.attrib.get('hummax')),
                    'avg': self._get_int(xml_day.attrib.get('hum')),
                },
                'pressure': {
                    'min': self._get_int(xml_day.attrib.get('pmin')),
                    'max': self._get_int(xml_day.attrib.get('pmax')),
                    'avg': self._get_int(xml_day.attrib.get('p')),
                },
                'cloudiness': xml_day.attrib.get('cl', ''),
                'storm': (xml_day.attrib.get('ts', '0') == '1'),
                'precipitation': {
                    'type': xml_day.attrib.get('pt', ''),
                    'amount': self._get_float(xml_day.attrib.get('prflt')),
                    'intensity': xml_day.attrib.get('pr', ''),
                },
                'icon': xml_day.attrib.get('icon', ''),
                'gm': xml_day.attrib.get('grademax', ''),
                'wind': {
                    'speed': {
                        'min': self._get_float(xml_day.attrib.get('wsmin')),
                        'max': self._get_float(xml_day.attrib.get('wsmax')),
                        'avg': self._get_float(xml_day.attrib.get('ws')),
                    },
                    'direction': xml_day.attrib.get('wd', ''),
                },
            }
            if len(xml_day):
                day['hourly'] = self._get_hourly_forecast(xml_day, tzone)
            result.append(day)
        return result

    def _get_hourly_forecast(self, xml_day: etree.Element, tzone: int) -> List[Dict[str, Any]]:
        result = []
        for xml_forecast in xml_day.findall('forecast'):
            item = self._get_item_forecast(xml_forecast, tzone)
            result.append(item)
        return result

    # ------------- Hilfsmethoden -------------
    @staticmethod
    def _get_int(value: Any) -> int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _get_float(value: Any) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    # ------------- Public API -------------
    def cities_search(self, keyword: str) -> List[Dict[str, Any]]:
        url = self._base_url + '/cities/'
        u_params = {'startsWith': keyword}
        r = self._get(url, params=u_params)
        x = self._extract_xml(r)
        return self._get_locations_list(x)

    def cities_ip(self, count: int = 1) -> List[Dict[str, Any]]:
        url = self._base_url + '/cities/'
        u_params = {'mode': 'ip', 'count': count, 'nocache': 1}
        r = self._get(url, params=u_params)
        x = self._extract_xml(r)
        return self._get_locations_list(x)

    def cities_nearby(self, lat: str, lng: str, count: int = 5) -> List[Dict[str, Any]]:
        url = self._base_url + '/cities/'
        u_params = {'lat': lat, 'lng': lng, 'count': count, 'nocache': 1}
        r = self._get(url, params=u_params)
        x = self._extract_xml(r)
        return self._get_locations_list(x)

    def forecast(self, city_id: str) -> Dict[str, Any]:
        url = self._base_url + '/forecast/'
        u_params = {'city': city_id}
        r = self._get(url, params=u_params)
        x = self._extract_xml(r)
        return self._get_forecast_info(x)
