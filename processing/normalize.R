library(signal)

# Remove outliers from a series of observations.
# We use Chauvenet's criterion to remove outlier rows based on observation
# column values.
remove_outliers <- function(xy,c) {
  m<-mean(xy[,c])
  s<-sd(xy[,c])
  n<-nrow(xy)
  v=dnorm(xy[,c],m,s)*n
  xy[v>=0.5,]
}

# Load raw datasets
data_collector_raw <- read.csv("../data_collector.csv", header=F)
radiothermostat_raw <- read.csv("../radiothermostat.csv", header=F)
wu_raw <- read.csv("../wu.csv", header=F)

all_series = list()
# for Weather Underground, use reported observation time instead of API query time, as they may differ.
all_series$wu <- remove_outliers(wu_raw[,2-3],2)
colnames(all_series$wu) <- c("ts","wu_t")
rm(wu_raw)

# no processing for radio thermostat time
all_series$radiothermostat <- remove_outliers(radiothermostat_raw,2)
colnames(all_series$radiothermostat) <- c("ts","rs_t","rs_h","rs_f")
rm(radiothermostat_raw)

sensors_ids = unique(data_collector_raw[[2]])
for(s in sensors_ids) {
  if(s==0)
    continue; # ID0 is reserved for server
  sname <- paste("sensor",s,sep="");
  all_series[[sname]] <-remove_outliers(
    cbind(data_collector_raw[data_collector_raw[2]==s,1],data_collector_raw[data_collector_raw[2]==s,5]),
    2)
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
plot(all_series$sensor1,col="black")
lines(new_ts,new_s1,type="l",col="red")
