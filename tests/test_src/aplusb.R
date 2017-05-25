# The complete code is given. You can just review and submit!
nums <- read.table("/dev/stdin", sep=" ");
nums <- as.list(as.data.frame(t(nums)))
write.table(as.numeric(nums[1])+as.numeric(nums[2]), sep = "", append=T, row.names = F, col.names = F)
