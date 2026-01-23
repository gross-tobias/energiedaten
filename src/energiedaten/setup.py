from EnergyChartsDatabase import *

EnergyChartsDatabase("localhost", "root", "", "energiedaten")._createTables()

EnergyChartsDatabase("localhost", "root", "", "energiedaten").saveDailyAverage(
        EnergyChartsClient().getSolarShareDailyAvg(), "Solar")
EnergyChartsDatabase("localhost", "root", "", "energiedaten").saveDailyAverage(
        EnergyChartsClient().getWindOnshoreShareDailyAvg(), "Wind Onshore")
EnergyChartsDatabase("localhost", "root", "", "energiedaten").saveDailyAverage(
        EnergyChartsClient().getWindOffshoreShareDailyAvg(), "Wind Offshore")
EnergyChartsDatabase("localhost", "root", "", "energiedaten").saveDailyAverage(
        EnergyChartsClient().getRenShareDailyAvg(), "Renewable")