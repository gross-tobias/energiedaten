import requests

class EnergyChartsClient:
    def __init__(self, baseUrl="https://api.energy-charts.info"):
        self.baseUrl = baseUrl

    def getPublicPower(self, country="de", start=None, end=None, subtype=None):
        params = {"country": country, "start": start, "end": end, "subtype": subtype}
        return self._fetch("/public_power", params)

    def getPublicPowerForecast(self, country="de", productionType="solar", forecastType="current", start=None, end=None):
        params = {
            "country": country, 
            "production_type": productionType, 
            "forecast_type": forecastType, 
            "start": start, 
            "end": end
        }
        return self._fetch("/public_power_forecast", params)

    def getTotalPower(self, country="de", start=None, end=None):
        params = {"country": country, "start": start, "end": end}
        return self._fetch("/total_power", params)

    def getInstalledPower(self, country="de", timeStep="yearly", installationDecommission=False):
        params = {
            "country": country, 
            "time_step": timeStep, 
            "installation_decommission": str(installationDecommission).lower()
        }
        return self._fetch("/installed_power", params)

    def getPrice(self, bzn="DE-LU", start=None, end=None):
        params = {"bzn": bzn, "start": start, "end": end}
        return self._fetch("/price", params)

    def getCbet(self, country="de", start=None, end=None):
        params = {"country": country, "start": start, "end": end}
        return self._fetch("/cbet", params)

    def getCbpf(self, country="de", start=None, end=None):
        params = {"country": country, "start": start, "end": end}
        return self._fetch("/cbpf", params)

    def getSignal(self, country="de", postalCode=None):
        params = {"country": country, "postal_code": postalCode}
        return self._fetch("/signal", params)

    def getRenShareForecast(self, country="de"):
        return self._fetch("/ren_share_forecast", {"country": country})

    def getRenShareDailyAvg(self, country="de", year=-1):
        return self._fetch("/ren_share_daily_avg", {"country": country, "year": year})

    def getSolarShare(self, country="de"):
        return self._fetch("/solar_share", {"country": country})

    def getSolarShareDailyAvg(self, country="de", year=-1):
        return self._fetch("/solar_share_daily_avg", {"country": country, "year": year})

    def getWindOnshoreShare(self, country="de"):
        return self._fetch("/wind_onshore_share", {"country": country})

    def getWindOnshoreShareDailyAvg(self, country="de", year=-1):
        return self._fetch("/wind_onshore_share_daily_avg", {"country": country, "year": year})

    def getWindOffshoreShare(self, country="de"):
        return self._fetch("/wind_offshore_share", {"country": country})

    def getWindOffshoreShareDailyAvg(self, country="de", year=-1):
        return self._fetch("/wind_offshore_share_daily_avg", {"country": country, "year": year})

    def getFrequency(self, region="DE-Freiburg", start=None, end=None):
        params = {"region": region, "start": start, "end": end}
        return self._fetch("/frequency", params)

    def _fetch(self, endpoint, params):
        cleanParams = {k: v for k, v in params.items() if v is not None}
        response = requests.get(f"{self.baseUrl}{endpoint}", params=cleanParams)
        response.raise_for_status()
        return response.json()
    