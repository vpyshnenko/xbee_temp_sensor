# Quick look at variable distributions.

load(file="ddata.Rdata")

# Plot
par(mfrow=c(4,2))
for(i in seq_along(dtemps))
{
  plot(dtemps[[i]], main=paste("temp",i))
}
rm(i)
plot(dac_state[[1]], main="HVAC")

# Print summary
lapply(dtemps,summary)