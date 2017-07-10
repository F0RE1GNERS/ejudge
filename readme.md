# eJudge v2

This project is yet under development and not ready for deployment.


## What is different?

+ Use a sandbox written in Python. The sandbox is basically the same, but easier to maintain.
  The lowest memory now becomes 12 MB :(
+ Add support for interactor
+ We now use "lazy update" to share data between judge server and main server:
  + All available data are automatically added to the judge server when it is added to the list.
  + Judge server can be disabled, since deletion cost is higher than before.
  + When problem data is updated, judge server gets a new copy of data.
+ New file system organization:
  + in/out file are added directly under `data/` without subfolders. Thus these files should be named uniquely with md5+timestamp
  + Judge server do not know which input belongs to which problem. These information should be specified when judging.
  + Submissions are also added under subfolder named md5+timestamp.
  + All special judge and interactors are added as "permanent submissions".
+ More options are added:
  + We now support display running result (only first 512 bytes sadly)
  + 
  
 
## Some random notes

`python3 setup.py build_ext --inplace`

compile time = 10 * max time