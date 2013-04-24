# Quick look at variable distributions.

load(file="data.Rdata")
par(mfrow=c(4,2))
for(i in 1:ncol(temps))
{
  hist(temps[,i], main=paste("temp",i))
}
hist(ac_state[,1], main=paste("A/C",i))
