# Quick look at variable distributions.

load(file="ddata.Rdata")

# Plot
par(mfrow=c(4,2))
for(i in seq_along(dtemps))
{
  plot(dtemps[[i]], main=paste("temp",i))
}
plot(dac_state[[1]], main=paste("A/C",i))

# Print summary
lapply(dtemps,summary)