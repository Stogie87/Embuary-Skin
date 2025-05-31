# -*- coding: utf-8 -*-
# Gismeteo Wetter-API Parser für Kodi (robust/future-proof)

import calendar
import time
import requests

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

class GismeteoError(Exception):
    pass

class GismeteoClient(object):
    _base_url = 'https://services.gismeteo.net/inform-service/inf_chrome'

    def __init__(self, lang='en'):
        self._lang = lang
        self._client = requests.Session()

    def __del__(self):
        self._client.close()

    def _extract_xml(self, r):
        try:
            x = etree.fromstring(r.content)
        except Exception as e:
            print("Gismeteo: Fehler beim XML-Parsing:", e)
            raise GismeteoError(e)
        return x

    def _get(self, url, params=None, *args, **kwargs):
        params = params or {}
        params['lang'] = self._lang
        try:
            r = self._client.get(url, params=params, *args, **kwargs)
            r.raise_for_status()
        except Exception as e:
            print("Gismeteo: HTTP-Fehler:", e)
            raise GismeteoError(e)
        return r

    def _get_locations_list(self, root):
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

    def _get_date(self, source, tzone):
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

    def _get_fact_forecast(self, xml_location):
        fact = xml_location.find('fact')
        if fact is None or not len(fact):
            print("Gismeteo: <fact> fehlt oder ist leer!")
            return {}
        values = fact.find('values')
        if values is None:
            print("Gismeteo: <values> fehlt in <fact>!")
            return {}
        return self._get_item_forecast(values, self._get_int(xml_location.attrib.get('tzone', 0)))

    def _get_item_forecast(self, xml_values, tzone):
        # xml_values ist nun das <values> Tag direkt
        result = {}
        attrib = xml_values.attrib
        if not attrib:
            print("Gismeteo: <values> leer!")
            return result
        # Robust: Alle Werte mit .get abfragen
        result['date'] = self._get_date(xml_values.attrib.get('valid', 0), tzone)
        if 'sunrise' in attrib:
            result['sunrise'] = self._get_date(self._get_float(attrib.get('sunrise')), tzone)
        if 'sunset' in attrib:
            result['sunset'] = self._get_date(self._get_float(attrib.get('sunset')), tzone)
        result['temperature'] = {
            'air': self._get_int(attrib.get('t')),
            'comfort': self._get_int(attrib.get('hi')),
        }
        if 'water_t' in attrib:
            result['temperature']['water'] = self._get_int(attrib.get('water_t'))
        result['description'] = attrib.get('descr', '')
        result['humidity'] = self._get_int(attrib.get('hum'))
        result['pressure'] = self._get_int(attrib.get('p'))
        result['cloudiness'] = attrib.get('cl', '')
        result['storm'] = (attrib.get('ts', '0') == '1')
        result['precipitation'] = {
            'type': attrib.get('pt', ''),
            'amount': self._get_float(attrib.get('prflt')),
            'intensity': attrib.get('pr', ''),
        }
        if 'ph' in attrib:
            result['phenomenon'] = self._get_int(attrib.get('ph'))
        if 'tod' in attrib:
            result['tod'] = self._get_int(attrib.get('tod'))
        result['icon'] = attrib.get('icon', '')
        result['gm'] = attrib.get('grade', '')
        result['wind'] = {
            'speed': self._get_float(attrib.get('ws')),
            'direction': attrib.get('wd', ''),
        }
        return result

    def _get_days_forecast(self, xml_location):
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
                # Untergeordnete <forecast> für Stundenwerte
                for xml_forecast in xml_day.findall('forecast'):
                    if 'hourly' not in day:
                        day['hourly'] = []
                    values = xml_forecast.find('values')
                    if values is not None:
                        day['hourly'].append(self._get_item_forecast(values, tzone))
            result.append(day)
        return result

    @staticmethod
    def _get_int(value):
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _get_float(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def cities_search(self, keyword):
        url = self._base_url + '/cities/'
        u_params = {'startsWith': keyword}
        r = self._get(url, params=u_params)
        x = self._extract_xml(r)
        return self._get_locations_list(x)

    def cities_ip(self, count=1):
        url = self._base_url + '/cities/'
        u_params = {'mode': 'ip', 'count': count, 'nocache': 1}
        r = self._get(url, params=u_params)
        x = self._extract_xml(r)
        return self._get_locations_list(x)

    def cities_nearby(self, lat, lng, count=5):
        url = self._base_url + '/cities/'
        u_params = {'lat': lat, 'lng': lng, 'count': count, 'nocache': 1}
        r = self._get(url, params=u_params)
        x = self._extract_xml(r)
        return self._get_locations_list(x)

    def forecast(self, city_id):
        url = self._base_url + '/forecast/'
        u_params = {'city': city_id}
        r = self._get(url, params=u_params)
        x = self._extract_xml(r)
        # --- Location-Infos ---
        info = {
            'name': x[0].attrib.get('name', x[0].attrib.get('n', 'Unbekannt')),
            'id': x[0].attrib.get('id', ''),
            'kind': x[0].attrib.get('kind', ''),
            'country': x[0].attrib.get('country_name', ''),
            'district': x[0].attrib.get('district_name', ''),
            'lat': x[0].attrib.get('lat', ''),
            'lng': x[0].attrib.get('lng', ''),
            'cur_time': self._get_date(x[0].attrib.get('cur_time', 0), self._get_int(x[0].attrib.get('tzone', 0))),
            'current': self._get_fact_forecast(x[0]),
            'days': self._get_days_forecast(x[0]),
        }
        return info
