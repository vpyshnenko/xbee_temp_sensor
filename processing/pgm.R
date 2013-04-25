
# See:
# [1] S. Højsgaard, D. Edwards, and S. Lauritzen, Graphical Models with R (Use R!). Springer, 2012, p. 191.

library(gRbase)
pgma <- ug(
  #windows
           c("w1","s1"),
           c("w2","s2"),
           c("w3","s3"),                     
           c("w4","s4"),
           c("w4","st"),
           # two sensors in living room
           c("s4","st"),          
  # doors 
           c("s1","d15"), c("d15","s5"),
           c("s3","d35"), c("d35","s5"),
           c("s2","d25"), c("d25","s5"),
  # upstairs/downstairs           
           c("st","s5"),
           #c("s4","s5"),
  # outside temp via windows           
           c("wu","w1"),
           c("wu","w2"),
           c("wu","w3"),
           c("wu","w4"),
  # HVAC in rooms           
           c("hvac","s1"),
           c("hvac","s2"),
           c("hvac","s3"),
           c("hvac","s4"),
#           c("hvac","s5"),
           c("hvac","st")
)
#plot(pgm1)
ipgma=as(pgma,"igraph")

V(ipgma)$shape <- c("square","circle","square","circle","square","circle","square","circle","circle","square","circle","square","square","rectangle","rectangle")
V(ipgma)$color <- c("green","red","green","red","green","red","green","red","red","grey","red","grey","grey","blue","yellow")
V(ipgma)$curved <- rep(T,15)
plot(as(ipgma,"igraph"))

