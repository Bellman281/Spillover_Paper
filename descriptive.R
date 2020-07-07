library(moments)
library(FinTS)


data <- read.csv("~/Comodity -berna/source.csv", header=T)
str(data)
data2<-data [,-1]
 
z<-diff(log(ts(data2)))

heads <- read.csv("~/Comodity -berna/symbols.csv", header=F)

dateA=data[,1]
str(dateA)
j=1
for (j in 1:9)
{
  plot(as.Date(dateA, "%m/%d/%Y"),ts(data2[j]),xlab="", 
       ylab=heads[j,2],type="l", main=heads[j,1], col=2,xaxt = "n")
  axis(side=1, at = seq(as.Date("2005/1/1"), as.Date("2015/1/1"), "years"),
       labels=seq(2005, 2015, by = 1), las=2)
  grid()
  
}

#descriptive table
Result<-matrix(nrow=8, ncol=10)

j=1
for (i in 1:8)
{
  Result[i,1]<-100*mean(z[,j])
  Result[i,2]<-sd(z[,j])
  Result[i,3]<-unname(skewness(z[,j]))
  Result[i,4]<- unname(kurtosis(z[,j]))  
  Result[i,5]<-unname(jarque.test(as.vector(z[,j]))$ statistic)
  Result[i,6]<-unname(jarque.test(as.vector(z[,j]))$ p.value)
  Result[i,7]<-unname(ArchTest(z[,j])$statistic)
  Result[i,8]<-unname(ArchTest(z[,j])$p.value)
  Result[i,9]<-unname(Box.test(z[,j],lag=20,type="Ljung-Box")$statistic)
  Result[i,10]<-cor(z[,1],z[,j],method="pearson")
  
  j=j+1
  
}

#table 1 of paper
write.table(Result, file = "~/Comodity -berna/Descriptive-Table1.txt", sep = "\t")

#Export for RATS 
write.table(z, file = "~/Comodity -berna/LogDiff.txt", sep = "\t")
