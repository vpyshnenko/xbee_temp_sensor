library(signal)

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
  if(s==0)
    continue; # ID0 is reserved for server
  sname <- paste("sensor",s,sep="");
  all_series[[sname]] <-
    cbind(data_collector_raw[data_collector_raw[2]==s,1],data_collector_raw[data_collector_raw[2]==s,5]);
  colnames(all_series[[sname]]) <- c("ts",paste("sensor",s,"_t",sep=""))
}
rm(s,sname)
rm(data_collector_raw)

# Find start and end times of all time series
start_times <- NULL
end_times <- NULL
for(s in all_series) {
  start_times <- c(start_times,min(s[,1]))
  end_times <- c(end_times,max(s[,1]))  
}

# find intersection
start_time <- max(start_times)
end_time <- min(end_times)

# resampling
new_ts<-seq(start_time,end_time,length.out=1000)
new_s1<-interp1(all_series$sensor1[,1],all_series$sensor1[,2],new_ts,method="spline")
plot(new_ts,new_s1,type="l")
lines(all_series$sensor1,col="red")
