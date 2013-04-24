library(signal)
#library("playwith")

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
    next; # ID0 is reserved for server
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
start_time <- ceiling(max(start_times))
end_time <- floor(min(end_times))
rm(start_times,end_times)

# load exclusions. We assume they are stored in increasing time order
# and are non-overlapping.
exclude_ranges_raw<-read.csv("exclude_ranges.csv", header=T)
exclude_ranges <- NULL
for(i in 1:nrow(exclude_ranges_raw))
{
  exclude_ranges<-rbind(exclude_ranges,
    c(max(as.POSIXct(exclude_ranges_raw[[i,1]]),start_time),
      min(as.POSIXct(exclude_ranges_raw[[i,2]]),end_time)))
}
rm(s) #in the loop above magically variable 's' is set!
rm(i,exclude_ranges_raw)
colnames(exclude_ranges)<-c("from","to")

# range inversion, from excludes to includes
include_ranges <- NULL
from <- start_time
for(i in 1:nrow(exclude_ranges))
{
    to <- exclude_ranges[[i,1]]
    if(from != to)
    {
      include_ranges<-rbind(include_ranges, c(from, to))
    }
    from <- exclude_ranges[i,2]
}
if(from<end_time)
  include_ranges<-rbind(include_ranges, c(from, end_time))
rm(from,to,exclude_ranges,i, start_time, end_time)


# resampling, per interval
RESAMPLING_STEP=60

resample_ts <- function(new_ts,xy,c=2,m="spline")
{
  interp1(xy[,1],xy[,c],new_ts,method=m)
}

smooth_ts <- function(new_ts,y)
{
  lowess(new_ts,y,
         10/length(new_ts),
         100,
         1E-16)$y
}

temps <- NULL
ac_state <- NULL
new_ts <- NULL
for(i in 1:nrow(include_ranges))
{
  start_time <- include_ranges[[i,1]]
  end_time <- include_ranges[[i,2]]
  inew_ts<-seq(start_time,end_time,RESAMPLING_STEP)
  # Temperature measurements, smoothed and resampled
  itemps <- cbind(
    smooth_ts(inew_ts,resample_ts(inew_ts,all_series$sensor1)),
    smooth_ts(inew_ts,resample_ts(inew_ts,all_series$sensor2)),
    smooth_ts(inew_ts,resample_ts(inew_ts,all_series$sensor3)),
    smooth_ts(inew_ts,resample_ts(inew_ts,all_series$sensor4)),
    smooth_ts(inew_ts,resample_ts(inew_ts,all_series$sensor5)),
    resample_ts(inew_ts,all_series$wu), # WU is already smoothed
    smooth_ts(inew_ts,resample_ts(inew_ts,all_series$radiothermostat))
  )
  temps <- rbind(temps, itemps)
  colnames(temps) <- c("sensor1","sensor2","sensor3","sensor4","sensor5","wu","radiothermostat")
  
  # discrete A/C state: 
  # column 1 is HVAC: 0:OFF,1:HEAT,-1:COOL
  # column 2 is FAN: 0:OFF, 1:ON
  iac_state = cbind(
    resample_ts(inew_ts,all_series$radiothermostat,3,"nearest"),
    resample_ts(inew_ts,all_series$radiothermostat,4,"nearest")
  )
  ac_state <- rbind(ac_state,iac_state)
  colnames(ac_state) <- c("hvac","fan")
  new_ts<-c(new_ts,inew_ts)
}
rm(i,itemps,iac_state,inew_ts)

#playwith(matplot(new_ts,cbind(temps,max(temps)*ac_state),type="l"))

write.table(cbind(new_ts,temps), file="temps.csv", sep=",", row.names=FALSE, col.names=c("t","t1","t2","t3","t4","t5","wu","tt"))
write.table(cbind(new_ts,ac_state), file="ac_state.csv", sep=",", row.names=FALSE, col.names=c("t","hvac","fan"))
save(new_ts,temps,ac_state,file="data.Rdata")

