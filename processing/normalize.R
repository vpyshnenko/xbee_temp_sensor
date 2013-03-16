library(zoo)

# Load raw datasets
data_collector_raw <- read.csv("../data_collector.csv", header=F)
radiothermostat_raw <- read.csv("../radiothermostat.csv", header=F)
wu_raw <- read.csv("../wu.csv", header=F)

all_series = list()
# for Weather Underground, use reported observation time instead of API query time, as they may differ.
all_series$wu <- wu_raw[,2-3]
colnames(all_series$wu) <- c("ts","wu_t")
rm(wu_raw)

# no processing for radio thermostat time
all_series$radiothermostat <- radiothermostat_raw
colnames(all_series$radiothermostat) <- c("ts","rs_t","rs_h","rs_f")
rm(radiothermostat_raw)

sensors_ids = unique(data_collector_raw[[2]])
for(s in sensors_ids) {
  sname <- paste("sensor",s,sep="");
  all_series[[sname]] <-
    cbind(data_collector_raw[data_collector_raw[2]==s,1],data_collector_raw[data_collector_raw[2]==s,5]);
  colnames(all_series[[sname]]) <- c("ts",paste("sensor",s,"_t",sep=""))
}
rm(s,sname)
rm(data_collector_raw)


